#!/bin/bash
# One CALM run on the CRP as a Slurm job on ALICE (1 A100). From the repo folder:
#   mkdir -p runs/calm   (once: Slurm needs the folder before it can write the output file)
#   sbatch --partition=gpu-short --time=01:00:00 experiments/calm_job.sh 0.5 1 20
#       one run: alpha, seed (a run number), budget (scored rules, default 500)
#   sbatch --array=0-29%4 --partition=gpu-short,gpu-a100-80g --time=04:00:00 experiments/calm_job.sh
#       all 30 runs, at most 4 at a time; seed is the outer loop, as in the EoH batch
# Output: runs/calm/calm_a<alpha>_s<seed>.{jsonl,row.json}; experiments/calm_result.py collect
#SBATCH --job-name=calm-crp
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=10
#SBATCH --mem=64G
#SBATCH --output=runs/calm/%x_%j.out
set -euo pipefail

if [ -n "${SLURM_ARRAY_TASK_ID:-}" ]; then  # job array: 0-29 = seeds 1-10 x alphas 0.5, 0.3, 0.1
    ALPHAS=(0.5 0.3 0.1)
    ALPHA=${ALPHAS[$((SLURM_ARRAY_TASK_ID % 3))]} SEED=$((SLURM_ARRAY_TASK_ID / 3 + 1)) BUDGET=500
else
    ALPHA=$1 SEED=$2 BUDGET=${3:-500}
fi
NAME=calm_a${ALPHA}_s${SEED}
ROOT=$PWD
CALM=$ROOT/frameworks/calm
DATA=/data1/liuw2/narek
export HF_HOME=$DATA/cache/hf VLLM_CACHE_ROOT=$DATA/cache/vllm TRITON_CACHE_DIR=$DATA/cache/triton
export PYTHONUNBUFFERED=1  # write CALM's output to the .out file at once, not in chunks
# a rerun starts clean: CALM appends to an existing log folder, and an old row file must not
# be merged with a new rule log (run_crp.py already deletes the old rule log)
rm -rf "$CALM/calm_saved/crp_online/$NAME" "$ROOT/runs/calm/$NAME.row.json"

echo "Job $SLURM_JOB_ID on $(hostname), GPU given by Slurm: ${CUDA_VISIBLE_DEVICES:-none}"
nvidia-smi -L

# Our own Ray with 8 workers (CALM would start one worker per core and hit thread limits);
# its own port and temp folder, so two jobs on the same node never share a Ray cluster
PORT=$((20000 + SLURM_JOB_ID % 10000))
"$CALM/.venv/bin/ray" start --head --num-cpus=8 --port=$PORT --temp-dir=/tmp/ray_$SLURM_JOB_ID \
    --include-dashboard=false --disable-usage-stats
export RAY_ADDRESS=127.0.0.1:$PORT
# no 'ray stop' at the end: it would stop every Ray of this user on the node, also other
# jobs' Rays; Slurm ends all of this job's processes when the job finishes

cd "$CALM"
"$CALM/.venv/bin/python" run_crp.py --alpha "$ALPHA" --model $DATA/models/qwen3-14b-nothink \
    --rule-log "$ROOT/runs/calm/$NAME.jsonl" --log-name "$NAME" --budget "$BUDGET"
"$CALM/.venv/bin/python" "$ROOT/experiments/calm_result.py" row --alpha "$ALPHA" --seed "$SEED" \
    --seconds "$SECONDS" --budget "$BUDGET"

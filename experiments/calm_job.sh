#!/bin/bash
# One CALM run on the CRP as a Slurm job on ALICE (1 A100). From the repo folder:
#   mkdir -p runs/calm   (once: Slurm needs the folder before it can write the output file)
#   sbatch --partition=gpu-short --time=01:00:00 experiments/calm_job.sh 0.5 test 20
# Arguments: alpha, run name, budget (scored rules). Output: runs/calm/<name>.{jsonl,out}
#SBATCH --job-name=calm-crp
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=10
#SBATCH --mem=64G
#SBATCH --output=runs/calm/%x_%j.out
set -euo pipefail

ALPHA=$1 NAME=$2 BUDGET=${3:-500}
ROOT=$PWD
CALM=$ROOT/frameworks/calm
DATA=/data1/liuw2/narek
export HF_HOME=$DATA/cache/hf VLLM_CACHE_ROOT=$DATA/cache/vllm TRITON_CACHE_DIR=$DATA/cache/triton
export PYTHONUNBUFFERED=1  # write CALM's output to the .out file at once, not in chunks

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

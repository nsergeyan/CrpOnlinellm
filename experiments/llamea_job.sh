#!/bin/bash
# One LLaMEA run on the CRP as a Slurm job on one A100 (tested on ALICE, Leiden's cluster; the
# partition names are ALICE's). CRP_DATA is the folder filled by frameworks/setup_ollama.sh;
# LLaMEA's environment comes from frameworks/setup_llamea.sh. From the repo folder:
#   mkdir -p runs/llamea   (once: Slurm needs the folder before it can write the output file)
#   CRP_DATA=/your/folder sbatch --partition=gpu-short --time=01:00:00 experiments/llamea_job.sh 0.5 1 20
#       one run: alpha, seed (a run number), budget (scored rules, default 500)
#   CRP_DATA=/your/folder sbatch --array=0-29%6 --partition=gpu-a100-80g,gpu-mig-40g --gres=gpu:1 --time=06:00:00 experiments/llamea_job.sh
#       all 30 runs, at most 6 at a time; seed is the outer loop, as in the EoH batch
# Output: runs/llamea/llamea_a<alpha>_s<seed>.{jsonl,row.json}; then experiments/run_llamea.py collect
#SBATCH --job-name=llamea-crp
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=6
#SBATCH --mem=32G
#SBATCH --output=runs/llamea/%x_%j.out
set -euo pipefail

if [ -n "${SLURM_ARRAY_TASK_ID:-}" ]; then  # job array: 0-29 = seeds 1-10 x alphas 0.5, 0.3, 0.1
    ALPHAS=(0.5 0.3 0.1)
    ALPHA=${ALPHAS[$((SLURM_ARRAY_TASK_ID % 3))]} SEED=$((SLURM_ARRAY_TASK_ID / 3 + 1)) BUDGET=500
else
    ALPHA=$1 SEED=$2 BUDGET=${3:-500}
fi
if [ -e "runs/llamea/llamea_a${ALPHA}_s${SEED}.row.json" ] && [ "$BUDGET" = 500 ]; then
    echo "llamea_a${ALPHA}_s${SEED} is done already"
    exit 0
fi
DATA=${CRP_DATA:?set CRP_DATA to the folder filled by frameworks/setup_ollama.sh}
export OLLAMA_MODELS=$DATA/ollama/models
# Ollama's program files on the node's local disk: from the network disk, starting CUDA takes
# longer than Ollama waits for it, and it falls back to the slower Vulkan (no MIG support)
LOCAL=${TMPDIR:-/tmp}/ollama_$SLURM_JOB_ID
mkdir -p "$LOCAL" && cp -r "$DATA/ollama/bin" "$DATA/ollama/lib" "$LOCAL"
trap 'rm -rf "$LOCAL"' EXIT
export PATH=$LOCAL/bin:$PATH
export OLLAMA_LOAD_TIMEOUT=30m  # the first load of the 9 GB model from the network disk can take minutes
# LLaMEA sends its 5 offspring prompts at the same time; 16,384 tokens each, as for our framework
export OLLAMA_NUM_PARALLEL=5 OLLAMA_CONTEXT_LENGTH=16384
# keep the model loaded: Ollama drops it after 5 idle minutes, and LLaMEA's own start can take longer
export OLLAMA_KEEP_ALIVE=-1
# its own port, so two jobs on the same node never share a model server
export OLLAMA_HOST=127.0.0.1:$((20000 + SLURM_JOB_ID % 10000))
export PYTHONUNBUFFERED=1  # write the output to the .out file at once, not in chunks

echo "Job $SLURM_JOB_ID on $(hostname), GPU given by Slurm: ${CUDA_VISIBLE_DEVICES:-none}"
nvidia-smi -L
# Slurm ends the server with the job
ollama serve > "runs/llamea/ollama_$SLURM_JOB_ID.log" 2>&1 &
until ollama list > /dev/null 2>&1; do sleep 1; done
# load the model before LLaMEA starts: from the network disk this can take longer than LLaMEA's
# client waits for its first answers (3 tries of 10 minutes), which would cost it its first rules
ollama run qwen3:14b-nothink "Say OK." > /dev/null

frameworks/llamea/.venv/bin/python experiments/run_llamea.py run --alpha "$ALPHA" --seed "$SEED" \
    --budget "$BUDGET" --base-url "http://$OLLAMA_HOST/v1"

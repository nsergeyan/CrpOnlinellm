#!/bin/bash
# experiments/bench_parallel.py as a Slurm job on one GPU (tested on ALICE): Ollama answering
# 1, 2, 4 and 8 requests at a time. CRP_DATA is the folder filled by frameworks/setup_ollama.sh.
# From the repo folder:
#   CRP_DATA=/your/folder sbatch --partition=gpu-mig-40g --gres=gpu:1 --time=01:00:00 experiments/bench_parallel_job.sh
# Output: runs/ours/bench-parallel_<job id>.out
#SBATCH --job-name=bench-parallel
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --output=runs/ours/%x_%j.out
set -euo pipefail

DATA=${CRP_DATA:?set CRP_DATA to the folder filled by frameworks/setup_ollama.sh}
export OLLAMA_MODELS=$DATA/ollama/models
# Ollama on the node's local disk, as in framework_job.sh (otherwise it does not find CUDA)
LOCAL=${TMPDIR:-/tmp}/ollama_$SLURM_JOB_ID
mkdir -p "$LOCAL" && cp -r "$DATA/ollama/bin" "$DATA/ollama/lib" "$LOCAL"
trap 'rm -rf "$LOCAL"' EXIT
export PATH=$LOCAL/bin:$PATH
export OLLAMA_LOAD_TIMEOUT=30m OLLAMA_NUM_PARALLEL=8
export OLLAMA_HOST=127.0.0.1:$((20000 + SLURM_JOB_ID % 10000))
export PYTHONUNBUFFERED=1

echo "Job $SLURM_JOB_ID on $(hostname)"
nvidia-smi -L
ollama serve > "runs/ours/ollama_$SLURM_JOB_ID.log" 2>&1 &
until ollama list > /dev/null 2>&1; do sleep 1; done

.venv/bin/python experiments/bench_parallel.py --base-url "http://$OLLAMA_HOST/v1"

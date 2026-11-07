#!/bin/bash
# One run of our framework as a Slurm job on one A100 (tested on ALICE, Leiden's cluster; the
# partition names are ALICE's). CRP_DATA is the folder filled by frameworks/setup_ollama.sh.
# From the repo folder:
#   mkdir -p runs/ours   (once: Slurm needs the folder before it can write the output file)
#   CRP_DATA=/your/folder sbatch --partition=gpu-short --time=04:00:00 experiments/framework_job.sh 0.5 1
#       one run: alpha, seed (a run number), then any options of `run_framework.py run`,
#       e.g. --seed-rule lowest or --off pareto
# Output: runs/ours/<name>.{jsonl,summary.json,row.json}; then experiments/run_framework.py collect
#SBATCH --job-name=ours-crp
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --output=runs/ours/%x_%j.out
set -euo pipefail

ALPHA=$1 SEED=$2
shift 2
DATA=${CRP_DATA:?set CRP_DATA to the folder filled by frameworks/setup_ollama.sh}
export PATH=$DATA/ollama/bin:$PATH OLLAMA_MODELS=$DATA/ollama/models
# its own port, so two jobs on the same node never share a model server
export OLLAMA_HOST=127.0.0.1:$((20000 + SLURM_JOB_ID % 10000))
export PYTHONUNBUFFERED=1  # write the output to the .out file at once, not in chunks

echo "Job $SLURM_JOB_ID on $(hostname), GPU given by Slurm: ${CUDA_VISIBLE_DEVICES:-none}"
nvidia-smi -L
# Slurm ends the server with the job
ollama serve > "runs/ours/ollama_$SLURM_JOB_ID.log" 2>&1 &
until ollama list > /dev/null 2>&1; do sleep 1; done

.venv/bin/python experiments/run_framework.py run --alpha "$ALPHA" --seed "$SEED" \
    --base-url "http://$OLLAMA_HOST/v1" "$@"

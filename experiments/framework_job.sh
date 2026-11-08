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
export OLLAMA_MODELS=$DATA/ollama/models
# Ollama's program files on the node's local disk: from the network disk, starting CUDA takes
# longer than Ollama waits for it, and it falls back to the slower Vulkan (no MIG support)
LOCAL=${TMPDIR:-/tmp}/ollama_$SLURM_JOB_ID
mkdir -p "$LOCAL" && cp -r "$DATA/ollama/bin" "$DATA/ollama/lib" "$LOCAL"
trap 'rm -rf "$LOCAL"' EXIT
export PATH=$LOCAL/bin:$PATH
export OLLAMA_LOAD_TIMEOUT=30m  # the first load of the 9 GB model from the network disk can take minutes
# up to 8 requests at once (the framework's batch_size) with room for 16,384 tokens each, about 3x
# our longest prompt plus answer; Ollama's default (32,768 on a 40 GB GPU) times 8 does not fit
export OLLAMA_NUM_PARALLEL=8 OLLAMA_CONTEXT_LENGTH=16384
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

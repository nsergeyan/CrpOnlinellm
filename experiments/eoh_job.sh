#!/bin/bash
# One run of EoH with our framework's prior knowledge (eoh-knowledge, README decision 54) as a
# Slurm job on one A100 (tested on ALICE, Leiden's cluster; the partition names are ALICE's).
# CRP_DATA is the folder filled by frameworks/setup_ollama.sh; ReEvo (which holds EoH) comes from
# frameworks/setup_reevo.sh. From the repo folder:
#   mkdir -p runs/eoh   (once: Slurm needs the folder before it can write the output file)
#   CRP_DATA=/your/folder sbatch --partition=gpu-short --time=01:00:00 experiments/eoh_job.sh 0.5 1 --quick
#       one test run with 30 evaluations: alpha, seed (a run number), then options of run_llm.py
#   CRP_DATA=/your/folder sbatch --array=0-29%6 --partition=gpu-a100-80g,gpu-mig-40g --gres=gpu:1 --time=06:00:00 experiments/eoh_job.sh
#       all 30 runs, at most 6 at a time; seed is the outer loop, as in the other batches
# Output: a row in results/llm_full.csv and the rule log results/llm_runs_full/eoh-knowledge_a<alpha>_s<seed>.jsonl
#SBATCH --job-name=eoh-crp
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --output=runs/eoh/%x_%j.out
set -euo pipefail

if [ -n "${SLURM_ARRAY_TASK_ID:-}" ]; then  # job array: 0-29 = seeds 1-10 x alphas 0.5, 0.3, 0.1
    ALPHAS=(0.5 0.3 0.1)
    ALPHA=${ALPHAS[$((SLURM_ARRAY_TASK_ID % 3))]} SEED=$((SLURM_ARRAY_TASK_ID / 3 + 1)) EXTRA=()
else
    ALPHA=$1 SEED=$2 EXTRA=("${@:3}")
fi
if [ ${#EXTRA[@]} -eq 0 ] && grep -q "^[^,]*,eoh-knowledge,[^,]*,$ALPHA,$SEED,500," results/llm_full.csv; then
    echo "eoh-knowledge alpha $ALPHA seed $SEED is done already"
    exit 0
fi
DATA=${CRP_DATA:?set CRP_DATA to the folder filled by frameworks/setup_ollama.sh}
export OLLAMA_MODELS=$DATA/ollama/models
# Ollama's program files on the node's local disk: from the network disk, starting CUDA takes
# longer than Ollama waits for it, and it falls back to the slower Vulkan (no MIG support)
LOCAL=${TMPDIR:-/tmp}/ollama_$SLURM_JOB_ID
# this job's own copy of ReEvo: every run writes the LLM's code to the same problems/<problem>/gpt.py,
# so two runs in one folder would overwrite each other's rules. The environment is shared (a link):
# copying its many small files from the network disk is slow.
export REEVO_DIR=${TMPDIR:-/tmp}/reevo_$SLURM_JOB_ID
trap 'rm -rf "$LOCAL" "$REEVO_DIR"' EXIT
mkdir -p "$LOCAL" && cp -r "$DATA/ollama/bin" "$DATA/ollama/lib" "$LOCAL"
rsync -a --exclude .venv frameworks/reevo/ "$REEVO_DIR/"
ln -s "$PWD/frameworks/reevo/.venv" "$REEVO_DIR/.venv"
export PATH=$LOCAL/bin:$PATH
export OLLAMA_LOAD_TIMEOUT=30m  # the first load of the 9 GB model from the network disk can take minutes
# EoH sends one request at a time; 16,384 tokens, as for our framework
export OLLAMA_NUM_PARALLEL=1 OLLAMA_CONTEXT_LENGTH=16384
export OLLAMA_KEEP_ALIVE=-1  # keep the model loaded between EoH's requests
# its own port, so two jobs on the same node never share a model server
export OLLAMA_HOST=127.0.0.1:$((20000 + SLURM_JOB_ID % 10000))
export PYTHONUNBUFFERED=1  # write the output to the .out file at once, not in chunks

echo "Job $SLURM_JOB_ID on $(hostname), GPU given by Slurm: ${CUDA_VISIBLE_DEVICES:-none}"
nvidia-smi -L
# Slurm ends the server with the job
ollama serve > "runs/eoh/ollama_$SLURM_JOB_ID.log" 2>&1 &
until ollama list > /dev/null 2>&1; do sleep 1; done
ollama run qwen3:14b-nothink "Say OK." > /dev/null  # load the model before EoH starts, as for LLaMEA

.venv/bin/python experiments/run_llm.py --method eoh-knowledge --alpha "$ALPHA" --seed "$SEED" \
    --base-url "http://$OLLAMA_HOST/v1" "${EXTRA[@]}"

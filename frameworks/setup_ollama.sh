#!/bin/bash
# Ollama and Qwen3-14B with thinking off, in a data folder, for running our framework on a Slurm
# cluster without admin rights (tested on ALICE). The same Ollama version and model as the laptop
# runs of EoH and ReEvo. Also makes the project's Python environment (.venv) if it is missing.
# From the repo folder, on the login node (downloads only, about 11 GB, no GPU needed):
#   CRP_DATA=/your/folder bash frameworks/setup_ollama.sh
# PYTHON can name the Python (3.10 or newer) for .venv; default python3.
set -euo pipefail

VERSION=0.34.4  # the laptop's Ollama server
DATA=${CRP_DATA:?set CRP_DATA to the folder for Ollama and the model}
OLLAMA_DIR=$DATA/ollama
export OLLAMA_MODELS=$OLLAMA_DIR/models
mkdir -p "$OLLAMA_MODELS"

if [ ! -x "$OLLAMA_DIR/bin/ollama" ]; then
    command -v zstd >/dev/null || { echo "zstd is needed to unpack Ollama"; exit 1; }
    curl -fL "https://github.com/ollama/ollama/releases/download/v$VERSION/ollama-linux-amd64.tar.zst" \
        | zstd -d | tar -x -C "$OLLAMA_DIR"
fi
export PATH=$OLLAMA_DIR/bin:$PATH

# a private server on its own port, only for the download; stopped when the script ends
export OLLAMA_HOST=127.0.0.1:$((30000 + RANDOM % 10000))
ollama serve > "$OLLAMA_DIR/setup_serve.log" 2>&1 &
SERVER=$!
trap 'kill $SERVER' EXIT
until ollama list > /dev/null 2>&1; do sleep 1; done
ollama pull qwen3:14b
python3 frameworks/make_nothink_model.py qwen3:14b
echo "Compare the IDs with the laptop's: qwen3:14b bdbd181c33f2, qwen3:14b-nothink 00081b164e0f"
ollama list

if [ ! -x .venv/bin/python ]; then
    "${PYTHON:-python3}" -m venv .venv
    .venv/bin/pip install -q -e ".[llm]"
fi
.venv/bin/python -c "import crp.framework, numpy; print('Python environment ok')"

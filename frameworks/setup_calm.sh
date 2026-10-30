#!/usr/bin/env bash
# Set up CALM (paper version) in frameworks/calm, with its own Python 3.11 environment.
# Run from anywhere:  bash frameworks/setup_calm.sh
# Safe to run again: it reuses the clone and the environment, and re-copies our files.
# On Linux (GPU server) it installs everything for fine-tuning; on macOS only what CALM's
# API mode needs, which is enough for tests/test_llm_calm.py with a fake LLM.
set -euo pipefail

CALM_URL=https://github.com/whxru/CALM
CALM_COMMIT=ecb3cad   # "Release CALM", the version described in the ICLR 2026 paper
PYTHON=${PYTHON:-python3.11}
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIR=${CALM_DIR:-"$ROOT/frameworks/calm"}

# CALM's own list pins libraries from early 2025 that cannot load Qwen3, so these are the
# oldest versions that can; trl stays at CALM's version. ray, grpcio and aiohttp are pinned
# because newer ones break Ray's helper processes. setuptools is needed by triton.
GPU_PACKAGES=(vllm==0.8.5.post1 transformers==4.51.3 trl==0.15.1 unsloth==2025.5.9
              unsloth_zoo==2025.5.11 "ray[cgraph]==2.46.0" setuptools nvidia-ml-py)
API_PACKAGES=(ray==2.46.0)
COMMON_PACKAGES=(grpcio==1.70.0 aiohttp==3.11.12 datasets openai numpy scipy pyyaml)

echo "1/4 CALM code at commit $CALM_COMMIT"
if [ ! -d "$DIR/.git" ]; then
    git clone --quiet "$CALM_URL" "$DIR"
fi
git -C "$DIR" checkout --quiet "$CALM_COMMIT"
if ! git -C "$DIR" diff --quiet; then             # CALM's own files must stay untouched
    echo "CALM's own files in $DIR were edited. Undo that first (git -C $DIR diff)." >&2
    exit 1
fi

echo "2/4 Python environment $DIR/.venv"
[ -x "$DIR/.venv/bin/python" ] || "$PYTHON" -m venv "$DIR/.venv"

echo "3/4 Installing CALM's packages and our crp code"
if [ "$(uname)" = "Linux" ]; then PACKAGES=("${GPU_PACKAGES[@]}"); else PACKAGES=("${API_PACKAGES[@]}"); fi
"$DIR/.venv/bin/python" -m pip install --quiet --upgrade pip
"$DIR/.venv/bin/python" -m pip install --quiet "${PACKAGES[@]}" "${COMMON_PACKAGES[@]}" -e "$ROOT"

echo "4/4 Our CRP files"
"$DIR/.venv/bin/python" "$ROOT/frameworks/install_calm_files.py" "$DIR"

echo "Done. CALM is ready in $DIR"

#!/usr/bin/env bash
# Set up LLaMEA (pip package, pinned version) in frameworks/llamea, with its own Python environment.
# Run from anywhere:  bash frameworks/setup_llamea.sh
# Safe to run again: it reuses the environment.
set -euo pipefail

LLAMEA_VERSION=1.4.2
PYTHON=${PYTHON:-python3.11}                      # LLaMEA needs Python >= 3.11
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIR=${LLAMEA_DIR:-"$ROOT/frameworks/llamea"}

echo "1/2 Python environment $DIR/.venv"
[ -x "$DIR/.venv/bin/python" ] || "$PYTHON" -m venv "$DIR/.venv"

echo "2/2 Installing LLaMEA $LLAMEA_VERSION and our crp code"
"$DIR/.venv/bin/python" -m pip install --quiet --upgrade pip
"$DIR/.venv/bin/python" -m pip install --quiet "llamea==$LLAMEA_VERSION" -e "$ROOT[llm]"

echo "Done. LLaMEA is ready in $DIR"

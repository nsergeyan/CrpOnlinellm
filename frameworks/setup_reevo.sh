#!/usr/bin/env bash
# Set up ReEvo at a pinned commit in frameworks/reevo, with its own Python 3.11 environment.
# Run from anywhere:  bash frameworks/setup_reevo.sh
# Safe to run again: it reuses the clone and the environment, and re-copies our files.
set -euo pipefail

REEVO_URL=https://github.com/ai4co/reevo
REEVO_COMMIT=6dce18257da5e11db2d138e417a2fffc5c72d05f
PYTHON=${PYTHON:-python3.11}                      # ReEvo needs Python >= 3.11
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIR=${REEVO_DIR:-"$ROOT/frameworks/reevo"}

echo "1/4 ReEvo code at commit $REEVO_COMMIT"
if [ ! -d "$DIR/.git" ]; then
    git clone --quiet "$REEVO_URL" "$DIR"
fi
git -C "$DIR" checkout --quiet "$REEVO_COMMIT"
if ! git -C "$DIR" diff --quiet; then             # ReEvo's own files must stay untouched
    echo "ReEvo's own files in $DIR were edited. Undo that first (git -C $DIR diff)." >&2
    exit 1
fi

echo "2/4 Python environment $DIR/.venv"
[ -x "$DIR/.venv/bin/python" ] || "$PYTHON" -m venv "$DIR/.venv"

echo "3/4 Installing ReEvo's packages and our crp code"
"$DIR/.venv/bin/python" -m pip install --quiet --upgrade pip
"$DIR/.venv/bin/python" -m pip install --quiet -e "$DIR" -e "$ROOT"
"$DIR/.venv/bin/python" -m pip install --quiet joblib   # needed by baselines/eoh, missing from ReEvo's list

echo "4/4 Our CRP files"
"$DIR/.venv/bin/python" "$ROOT/frameworks/install_reevo_files.py" "$DIR"

echo "Done. ReEvo is ready in $DIR"

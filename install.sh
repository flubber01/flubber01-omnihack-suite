#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════
#  OMNIHACK MISSION CONTROL — ONE-SHOT INSTALLER
#
#  Single-command install & launch:
#
#     bash install.sh                    # inside a clone
#     bash install.sh --no-launch        # install only
#
#  Or fully remote (clones the repo automatically):
#
#     bash <(curl -fsSL https://raw.githubusercontent.com/flubber01/\
# flubber01-omnihack-suite/arena/01a0e419-flubber01-omnihack-suite/install.sh)
# ═══════════════════════════════════════════════════════════════════════
set -euo pipefail

REPO="https://github.com/flubber01/flubber01-omnihack-suite.git"
BRANCH="arena/01a0e419-flubber01-omnihack-suite"
PORT="${OMNI_PORT:-7860}"
LAUNCH=1
[[ "${1:-}" == "--no-launch" ]] && LAUNCH=0

echo "◤ OMNIHACK INSTALLER ◢"

# 1. ensure we are inside the repo (clone if invoked standalone) ----------
if [[ ! -f requirements.txt ]]; then
  echo "→ repo not found here, cloning…"
  TARGET="flubber01-omnihack-suite"
  if command -v git >/dev/null 2>&1; then
    git clone --depth 1 --branch "$BRANCH" "$REPO" "$TARGET" || \
    git clone --depth 1 "$REPO" "$TARGET"
  else
    echo "✗ git is required (apt install git)"; exit 1
  fi
  cd "$TARGET"
fi

# 2. python ----------------------------------------------------------------
PY="$(command -v python3 || true)"
if [[ -z "$PY" ]]; then
  echo "✗ python3 not found — install it first (apt install python3 python3-venv)"
  exit 1
fi
echo "→ python: $($PY --version)"

# 3. venv + deps -------------------------------------------------------------
if [[ ! -d .venv ]]; then
  "$PY" -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
echo "→ dependencies installed"

# 4. launch ------------------------------------------------------------------
if [[ $LAUNCH -eq 1 ]]; then
  echo "→ launching Mission Control on 0.0.0.0:${PORT}"
  echo "   main   → http://localhost:${PORT}/"
  echo "   screen → http://localhost:${PORT}/ops"
  echo "   wall   → http://localhost:${PORT}/wall"
  exec python run_mission_control.py
else
  echo "✓ installed. start later with:  source .venv/bin/activate && python run_mission_control.py"
fi

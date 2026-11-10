#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
cd "$root"
python - "$tmp" <<'PY'
import json,sys
from pathlib import Path
from shieldlab.reachavoid import analyze_reachavoid
from shieldlab.recurrence import analyze_recurrence
for name,fn in [('reachavoid',analyze_reachavoid),('recurrence',analyze_recurrence)]:
 controls=json.load(open('docs/'+name+'-controls.json'))
 (Path(sys.argv[1])/(name+'.json')).write_text(json.dumps([{'input':c['input'],'report':fn(c['input'])}for c in controls]))
PY
python -m pip wheel --no-deps --wheel-dir "$tmp/wheels" "$root"
python -m venv "$tmp/venv"
cd "$tmp"
env -u PYTHONPATH "$tmp/venv/bin/python" -m pip install --no-deps "$tmp"/wheels/*.whl
env -u PYTHONPATH "$tmp/venv/bin/python" "$root/tools/verify_installed.py" "$root/docs/controls.json"
env -u PYTHONPATH "$tmp/venv/bin/python" "$root/tools/verify_reachavoid_installed.py" "$tmp/reachavoid.json"
env -u PYTHONPATH "$tmp/venv/bin/python" "$root/tools/verify_recurrence_installed.py" "$tmp/recurrence.json"

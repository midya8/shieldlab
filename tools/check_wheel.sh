#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
cd "$root"
python - "$tmp/reachavoid-expected.json" <<'PY_EXPECTED'
import json,sys
from shieldlab.reachavoid import analyze_reachavoid
controls=json.load(open('docs/reachavoid-controls.json'))
json.dump([{'input':c['input'],'report':analyze_reachavoid(c['input'])}for c in controls],open(sys.argv[1],'w'))
PY_EXPECTED
python -m pip wheel --no-deps --wheel-dir "$tmp/wheels" "$root"
python -m venv "$tmp/venv"
"$tmp/venv/bin/python" -m pip install --no-deps "$tmp"/wheels/*.whl
"$tmp/venv/bin/python" "$root/tools/verify_installed.py" "$root/docs/controls.json"

"$tmp/venv/bin/python" "$root/tools/verify_reachavoid_installed.py" "$tmp/reachavoid-expected.json"

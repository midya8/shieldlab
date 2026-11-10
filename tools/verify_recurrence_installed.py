"""Verify installed extension outside checkout against pre-build whole reports."""
import copy
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from shieldlab.recurrence import analyze_recurrence
from shieldlab.recurrence_verify import verify_recurrence

origins = []
for name in ['shieldlab.recurrence', 'shieldlab.recurrence_input', 'shieldlab.recurrence_verify', 'shieldlab.recurrence_cli']:
    p = Path(importlib.import_module(name).__file__).resolve()
    assert 'site-packages' in p.parts, p
    origins.append(str(p))
rows = json.loads(Path(sys.argv[1]).read_text())
env = dict(os.environ); env.pop('PYTHONPATH', None)
commands = [[sys.executable, '-m', 'shieldlab.recurrence'],
            [str(Path(sys.executable).parent/'shieldlab-recurrence')]]
with tempfile.TemporaryDirectory() as d:
    for row in rows:
        expected = row['report']
        assert analyze_recurrence(row['input']) == expected
        assert verify_recurrence(expected)
        for cmd in commands:
            p = subprocess.run(cmd+['-'], input=json.dumps(row['input']), text=True, capture_output=True, cwd=d, env=env)
            assert p.returncode == 0, p.stderr
            assert json.loads(p.stdout) == expected
            p = subprocess.run(cmd+['-', '--verify'], input=json.dumps(expected), text=True, capture_output=True, cwd=d, env=env)
            assert p.returncode == 0, p.stderr
            assert json.loads(p.stdout) == {'valid': True, 'schema': 'shieldlab-recurrence-v1'}
    paths = [('schema',), ('winning',), ('losing',), ('outer', 0, 'inner', 0, 'checks', 0, 'reset'),
             ('outer', 0, 'after'), ('states', 0, 'winning'), ('policy_atlases', 'controller', 0, 'outcomes', 0, 'winning'),
             ('policy_atlases', 'environment', 0, 'outcomes', 0, 'failure'), ('uniform_policy_ids', 'controller'),
             ('proof_graphs', 0, 'edges'), ('proof_graphs', 0, 'player'), ('states', 0, 'environment_policy_ids')]
    rejected = 0
    for path in paths:
        forged = copy.deepcopy(rows[0]['report']); node = forged
        for key in path[:-1]: node = node[key]
        node[path[-1]] = 'forged'
        for cmd in commands:
            p = subprocess.run(cmd+['-', '--verify'], input=json.dumps(forged), text=True, capture_output=True, cwd=d, env=env)
            assert p.returncode == 2 and not p.stdout and 'Traceback' not in p.stderr, p.stderr
            rejected += 1
print(json.dumps({'recurrence_controls': len(rows), 'entrypoints': len(commands),
                  'installed_origins': origins, 'forged_cli_rejections': rejected}))

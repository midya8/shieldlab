"""Reproduce every browser control through installed import and both CLI entry points."""
import importlib
import json
import os
import tempfile
from pathlib import Path
import subprocess
import sys
from shieldlab import analyze, verify
controls=json.loads(Path(sys.argv[1]).read_text())
origins=[]
for name in ['shieldlab','shieldlab.core','shieldlab.verify','shieldlab.__main__']:
    origin=str(Path(importlib.import_module(name).__file__).resolve())
    assert 'site-packages' in origin,origin
    origins.append(origin)
outside=tempfile.TemporaryDirectory()
env=dict(os.environ);env.pop('PYTHONPATH',None)
for c in controls:
    expected=analyze(c['input']);assert verify(expected)
    for cmd in [[sys.executable,'-m','shieldlab'],[str(Path(sys.executable).parent/'shieldlab')]]:
        p=subprocess.run(cmd+['-'],input=json.dumps(c['input']),text=True,capture_output=True,check=True,cwd=outside.name,env=env)
        actual=json.loads(p.stdout);assert actual==expected
        p=subprocess.run(cmd+['-','--verify'],input=json.dumps(actual),text=True,capture_output=True,check=True,cwd=outside.name,env=env)
        assert json.loads(p.stdout)=={'valid':True,'schema':'shieldlab-v1'}
print(json.dumps({'reports':len(controls),'entry_points':2,'installed_origins':origins}))

outside.cleanup()

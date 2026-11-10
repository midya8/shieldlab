"""Installed origins and every control compared to pre-build source reports."""
import copy
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from shieldlab.reachavoid import analyze_reachavoid
from shieldlab.reachavoid_verify import verify_reachavoid

origins=[]
for n in ['shieldlab','shieldlab.core','shieldlab.verify','shieldlab.__main__','shieldlab.reachavoid_input','shieldlab.reachavoid','shieldlab.reachavoid_verify','shieldlab.reachavoid_cli']:
    p=Path(importlib.import_module(n).__file__).resolve();assert 'site-packages'in p.parts,p;origins.append(str(p))
rows=json.loads(Path(sys.argv[1]).read_text());env=dict(os.environ);env.pop('PYTHONPATH',None)
commands=[[sys.executable,'-m','shieldlab.reachavoid'],[str(Path(sys.executable).parent/'shieldlab-reachavoid')]]
with tempfile.TemporaryDirectory()as d:
    for row in rows:
        expected=row['report'];assert analyze_reachavoid(row['input'])==expected;assert verify_reachavoid(expected)
        for cmd in commands:
            p=subprocess.run(cmd+['-'],input=json.dumps(row['input']),text=True,capture_output=True,check=True,cwd=d,env=env)
            assert json.loads(p.stdout)==expected
            p=subprocess.run(cmd+['-','--verify'],input=json.dumps(expected),text=True,capture_output=True,check=True,cwd=d,env=env)
            assert json.loads(p.stdout)=={'valid':True,'schema':'shieldlab-reachavoid-v1'}
    mutations=[('schema',),('winning',),('rounds',0,'added'),('states',0,'rank'),('states',0,'controller_choice'),('proof_graphs',0,'edges'),('policy_count',),('policy_atlas',0,'outcomes',0,'winning'),('policy_atlas',0,'outcomes',0,'witness','cycle_start'),('policy_summaries',0,'winning_policy_ids')]
    rejected=0
    for path in mutations:
        b=copy.deepcopy(rows[0]['report']);node=b
        for key in path[:-1]:node=node[key]
        node[path[-1]]='forged'
        for cmd in commands:
            p=subprocess.run(cmd+['-','--verify'],input=json.dumps(b),text=True,capture_output=True,cwd=d,env=env)
            assert p.returncode==2 and p.stdout=='' and 'Traceback'not in p.stderr
            rejected+=1
print(json.dumps({'reachavoid_reports':len(rows),'entrypoints':len(commands),'installed_origins':origins,'forged_cli_rejections':rejected}))

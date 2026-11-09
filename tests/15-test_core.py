import copy
import itertools
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from shieldlab import analyze, validate, verify, policy_oracle

ROOT = Path(__file__).resolve().parents[1]
CONTROLS = json.loads((ROOT/'docs/controls.json').read_text())


def game(n, edges, owners, safe):
    return {'states':[{'name':'s'+str(i),'owner':'controller' if owners>>i&1 else 'environment','safe':bool(safe>>i&1),
                       'moves':[{'action':'a'+str(j),'to':'s'+str(t)} for j,t in enumerate(edges[i])]} for i in range(n)]}


class Tests(unittest.TestCase):
    def test_controls_and_quantifier_flip(self):
        reports = [analyze(c['input']) for c in CONTROLS]
        for r in reports: self.assertTrue(verify(r))
        self.assertEqual(reports[0]['winning'], ['choose','approved'])
        self.assertEqual(reports[1]['winning'], ['choose','pending','approved'])
        self.assertFalse(reports[0]['states'][0]['moves'][0]['safe_move'])
        self.assertTrue(reports[1]['states'][0]['moves'][0]['safe_move'])
        self.assertEqual([s['rank'] for s in reports[2]['states']], [5,4,3,2,1,0])
        self.assertEqual(reports[3]['winning'], ['a','b'])
        self.assertEqual(reports[4]['proof_graphs'][0]['edges'], [{'from':'idle','action':'wait','to':'idle'}])
        self.assertEqual(reports[5]['proof_graphs'][0]['edges'], [])

    def test_all_three_state_total_graphs_all_owners_and_safe_sets(self):
        choices = [[j for j in range(3) if mask>>j&1] for mask in range(1,8)]
        count=0
        for edges in itertools.product(choices,repeat=3):
            for owners in range(8):
                for safe in range(8):
                    x=game(3,edges,owners,safe);r=analyze(x)
                    self.assertEqual(r['winning'],policy_oracle(x));verify(r);count+=1
        self.assertEqual(count,21952)

    def test_seeded_larger_graphs_and_rank_obligations(self):
        rng=random.Random(904)
        for _ in range(150):
            n=rng.randint(1,6);edges=[[rng.randrange(n) for _ in range(rng.randint(1,3))] for i in range(n)]
            x=game(n,edges,rng.randrange(1<<n),rng.randrange(1<<n));r=analyze(x);verify(r)
            for s,p in zip(r['states'],r['proof_graphs']):
                if s['winning']:
                    self.assertFalse(p['bad'])
                    if s['owner']=='controller':self.assertTrue(any(m['safe_move'] for m in s['moves']))
                    else:self.assertTrue(all(m['target_winning'] for m in s['moves']))
                elif s['rank']>0:
                    if s['owner']=='controller':self.assertTrue(all(m['rank_decreasing'] for m in s['moves']))
                    else:self.assertTrue(any(m['rank_decreasing'] for m in s['moves']))

    def test_independent_checker_never_calls_solver(self):
        r=analyze(CONTROLS[0]['input'])
        with patch('shieldlab.core.analyze',side_effect=RuntimeError('disabled')):self.assertTrue(verify(r))

    def test_full_structure_and_typed_forgeries(self):
        base=analyze(CONTROLS[0]['input'])
        changes=[lambda r:r.update(schema='other'),lambda r:r['winning'].append('pending'),lambda r:r['rounds'].pop(),
                 lambda r:r['rounds'][0]['checks'][0]['target_in_before'].reverse(),
                 lambda r:r['rounds'][0]['checks'][0].update(kept=1),lambda r:r['states'][1].update(rank=True),
                 lambda r:r['states'][0].update(controller_choice='fast'),lambda r:r['states'][0]['moves'][0].update(safe_move=True),
                 lambda r:r['proof_graphs'][0]['edges'].clear(),lambda r:r['proof_graphs'][1].update(rank_bound=2),
                 lambda r:r['proof_graphs'][1]['bad'].clear(),lambda r:r.update(extra=True)]
        # Round-zero target flags for choose are both true; mutate a false flag at pending instead.
        changes[3]=lambda r:r['rounds'][0]['checks'][1]['target_in_before'].__setitem__(1,True)
        for change in changes:
            r=copy.deepcopy(base);change(r)
            with self.assertRaises(ValueError):verify(r)

    def test_input_immutability_and_ordering(self):
        x=copy.deepcopy(CONTROLS[0]['input']);before=copy.deepcopy(x);r=analyze(x);verify(r);self.assertEqual(x,before)
        x['states'].reverse();x['states'][0]['moves'].reverse();other=analyze(x);verify(other)
        self.assertEqual(set(r['winning']),set(other['winning']))
        self.assertEqual({s['name']:s['rank'] for s in r['states']},{s['name']:s['rank'] for s in other['states']})

    def test_strict_bounded_schema_and_dead_ends(self):
        for x in [{},{'states':[]},{'states':[{}]},{'states':[{'name':'x','owner':'controller','safe':True,'moves':[]}]}]:
            with self.assertRaises((ValueError,TypeError)):validate(x)
        base=CONTROLS[0]['input']
        for mutate in [lambda x:x['states'][0].update(owner='random'),lambda x:x['states'][0].update(safe=1),
                       lambda x:x['states'][0]['moves'][0].update(to='missing'),lambda x:x['states'][0]['moves'][0].update(action='bad word'),
                       lambda x:x['states'][0]['moves'].append(x['states'][0]['moves'][0]),lambda x:x.update(extra=1)]:
            x=copy.deepcopy(base);mutate(x)
            with self.assertRaises(ValueError):validate(x)

    def test_cli_strict_atomic_and_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'out.json';out.write_text('preserve')
            for raw in ['{"states":[],"states":[]}','{"states":NaN}','{}','['*1500,' '*65537]:
                p=subprocess.run([sys.executable,'-m','shieldlab','-','--output',str(out)],input=raw,text=True,capture_output=True)
                self.assertEqual(p.returncode,2);self.assertFalse(p.stdout);self.assertEqual(out.read_text(),'preserve')
            p=subprocess.run([sys.executable,'-m','shieldlab','-','--output',str(out)],input=json.dumps(CONTROLS[0]['input']),text=True,capture_output=True)
            self.assertEqual(p.returncode,0,p.stderr);self.assertFalse(p.stdout);self.assertEqual(json.loads(out.read_text()),analyze(CONTROLS[0]['input']))
            p=subprocess.run([sys.executable,'-m','shieldlab',str(out),'--verify'],text=True,capture_output=True)
            self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(json.loads(p.stdout),{'valid':True,'schema':'shieldlab-v1'})

if __name__=='__main__':unittest.main()

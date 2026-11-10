import copy
import itertools
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest
from shieldlab.reachavoid import analyze_reachavoid
from shieldlab.reachavoid_verify import verify_reachavoid, replay_reachavoid
from shieldlab.core import analyze as analyze_safety

ROOT=Path(__file__).resolve().parents[1]
CONTROLS=json.loads((ROOT/'docs/reachavoid-controls.json').read_text())


def strategy_pair_values(request):
    """Independent deterministic strategy-pair simulation, no graph search.

    For each complete controller strategy enumerate every complete adversarial
    strategy and simulate its unique play until first target/unsafe/repeat.
    """
    states=request['arena']['states'];by={s['name']:s for s in states};goals=set(request['goals'])
    players={o:[s for s in states if s['owner']==o and s['safe']and s['name']not in goals]for o in ['controller','environment']}
    choices={o:list(itertools.product(*(range(len(s['moves']))for s in ss)))for o,ss in players.items()}
    rows=[]
    for c in choices['controller']:
        p={s['name']:j for s,j in zip(players['controller'],c)};worst={n:0 for n in by}
        for e in choices['environment']:
            policy=p|{s['name']:j for s,j in zip(players['environment'],e)}
            for root in by:
                n=root;visited=set();steps=0
                while n not in goals and by[n]['safe']and n not in visited:
                    visited.add(n);n=by[n]['moves'][policy[n]]['to'];steps+=1
                if n not in goals:worst[root]=None
                elif worst[root]is not None:worst[root]=max(worst[root],steps)
        rows.append(worst)
    best={n:min((r[n]for r in rows if r[n]is not None),default=None)for n in by}
    return rows,best


def graph(n,edges,owners,status):
    names=['s'+str(i)for i in range(n)]
    return {'arena':{'states':[{'name':name,'owner':'controller'if owners>>i&1 else'environment','safe':status[i]!=0,
            'moves':[{'action':'a'+str(j),'to':names[t]}for j,t in enumerate(edges[i])]}for i,name in enumerate(names)]},
            'goals':[names[i]for i,v in enumerate(status)if v==2]}


class ReachAvoidTests(unittest.TestCase):
    def check(self,request,full=True):
        report=analyze_reachavoid(request);rows,best=strategy_pair_values(request)
        self.assertEqual([s['rank']for s in report['states']],[best[s['name']]for s in request['arena']['states']])
        self.assertEqual(len(rows),report['policy_count'])
        for row,atlas in zip(rows,report['policy_atlas']):
            self.assertEqual([o['worst_steps']for o in atlas['outcomes']],list(row.values()))
            self.assertEqual([o['winning']for o in atlas['outcomes']],[v is not None for v in row.values()])
        if full:self.assertTrue(verify_reachavoid(report))
        return report

    def test_prescribed_control_and_example_byte_reproduction(self):
        import importlib.util
        spec=importlib.util.spec_from_file_location('reachavoid_controls',ROOT/'tools/make_reachavoid_controls.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        self.assertEqual(json.dumps(module.controls(),indent=2)+'\n',(ROOT/'docs/reachavoid-controls.json').read_text())
        self.assertEqual(json.dumps(module.controls()[0]['input'],indent=2)+'\n',(ROOT/'docs/reachavoid-example.json').read_text())

    def test_all_fixed_controls(self):
        for c in CONTROLS:
            with self.subTest(c['id']):self.check(c['input'])

    def test_every_two_node_total_graph_owner_safe_goal_configuration(self):
        subsets=[(0,),(1,),(0,1)];count=0
        for edges in itertools.product(subsets,repeat=2):
            for owner in range(4):
                for status in itertools.product(range(3),repeat=2):
                    self.check(graph(2,edges,owner,status));count+=1
        self.assertEqual(count,324)

    def test_all_three_node_graphs_one_goal_and_all_other_safety_owners(self):
        subsets=[x for k in [1,2,3]for x in itertools.combinations(range(3),k)];count=0
        for edges in itertools.product(subsets,repeat=3):
            for owner in range(8):
                for goal in range(3):
                    others=[i for i in range(3)if i!=goal]
                    for bits in range(4):
                        status=[0]*3;status[goal]=2
                        for j,i in enumerate(others):status[i]=(bits>>j)&1
                        self.check(graph(3,edges,owner,status),False);count+=1
        self.assertEqual(count,32928)

    def test_seeded_larger_graphs_and_independent_full_replay(self):
        rng=random.Random(491203)
        for k in range(120):
            n=4+k%3;edges=[rng.sample(range(n),rng.randint(1,3))for _ in range(n)]
            status=[rng.randrange(3)for _ in range(n)]
            self.check(graph(n,edges,rng.randrange(1<<n),status))

    def test_winning_successor_can_stall_and_owner_flip_prevents_goal(self):
        a=self.check(CONTROLS[0]['input']);b=self.check(CONTROLS[1]['input'])
        self.assertEqual([m['target_winning']for m in a['states'][0]['moves']],[True,True])
        self.assertEqual([m['optimal_controller_move']for m in a['states'][0]['moves']],[False,True])
        self.assertEqual(a['policy_atlas'][0]['outcomes'][0]['witness']['kind'],'goal_avoiding_lasso')
        self.assertEqual(a['states'][0]['rank'],1);self.assertIsNone(b['states'][0]['rank'])
        self.assertIn('choose',b['safe_but_cannot_force_goal'])

    def test_nonoptimal_detour_can_still_win(self):
        a=self.check(CONTROLS[2]['input'])
        self.assertEqual([p['outcomes'][0]['worst_steps']for p in a['policy_atlas']],[1,2])
        self.assertEqual(a['policy_summaries'][0]['winning_policy_ids'],[0,1])
        self.assertEqual(a['policy_summaries'][0]['optimal_policy_ids'],[0])

    def test_terminal_goal_semantics_differ_from_infinite_safety(self):
        c=CONTROLS[4]['input'];a=self.check(c)
        self.assertIn('start',a['winning']);self.assertNotIn('start',analyze_safety(c['arena'])['winning'])
        self.assertEqual(a['proof_graphs'][2]['edges'],[])
        self.assertEqual(a['policy_atlas'][0]['outcomes'][2]['worst_steps'],0)
        self.assertFalse(a['policy_atlas'][0]['outcomes'][0]['winning'])

    def test_every_proof_edge_and_exact_first_hit_rank(self):
        for c in CONTROLS:
            a=self.check(c['input']);by={s['name']:s for s in a['states']}
            for p in a['proof_graphs']:
                for e in p['edges']:
                    s=by[e['from']];self.assertFalse(s['goal']);self.assertTrue(s['safe'])
                    self.assertIn({'action':e['action'],'to':e['to']},[{'action':m['action'],'to':m['to']}for m in s['moves']])
                    if p['rank_bound']is not None:self.assertLess(by[e['to']]['rank'],s['rank'])
                    else:self.assertFalse(by[e['to']]['winning'])
            self.assertLessEqual(max([s['rank']for s in a['states']if s['rank']is not None],default=0),5)

    def test_full_policy_boundary_and_report_size(self):
        request=graph(6,[(i,(i+1)%6,(i+2)%6)for i in range(6)],63,[1]*6)
        a=self.check(request);self.assertEqual(a['policy_count'],729)
        self.assertEqual(a['winning'],[]);self.assertEqual(a['safe_until_goal'],['s'+str(i)for i in range(6)])
        self.assertLess(len(json.dumps(a,indent=2).encode()),16*1024*1024)

    def test_state_and_move_permutation_preserves_semantic_values(self):
        rng=random.Random(41293)
        for control in CONTROLS:
            old=analyze_reachavoid(control['input']);request=copy.deepcopy(control['input'])
            rng.shuffle(request['arena']['states'])
            for state in request['arena']['states']:rng.shuffle(state['moves'])
            new=self.check(request)
            self.assertEqual({s['name']:s['rank']for s in old['states']},{s['name']:s['rank']for s in new['states']})
            self.assertEqual(set(old['safe_until_goal']),set(new['safe_until_goal']))
            def policies(report):
                return {tuple(sorted((p['state'],p['action'])for p in row['policy'])):
                        {o['start']:(o['winning'],o['worst_steps'])for o in row['outcomes']}for row in report['policy_atlas']}
            self.assertEqual(policies(old),policies(new))

    def test_schema_goal_and_dead_end_rejection(self):
        base=CONTROLS[0]['input'];cases=[]
        for goals in [None,{},'done',['done','done'],['unknown'],['bad'],[True],[{}]]:
            b=copy.deepcopy(base);b['goals']=goals;cases.append(b)
        b=copy.deepcopy(base);b['extra']=1;cases.append(b)
        b=copy.deepcopy(base);b['arena']['states'][1]['moves']=[];cases.append(b)
        b=copy.deepcopy(base);b['arena']['states'][0]['moves'][0]['to']=[];cases.append(b)
        for b in cases:
            with self.assertRaises((ValueError,TypeError)):analyze_reachavoid(b)
            with self.assertRaises((ValueError,TypeError)):replay_reachavoid(b)

    def test_input_output_isolation_and_goal_order(self):
        b=copy.deepcopy(CONTROLS[7]['input']);before=copy.deepcopy(b);a=self.check(b)
        self.assertEqual(b,before);self.assertEqual(a['input']['goals'],['a','b'])
        b['arena']['states'][0]['name']='changed';self.assertEqual(a['input']['arena']['states'][0]['name'],'a')
        a['states'][0]['moves'][0]['to']='changed';self.assertEqual(a['input']['arena']['states'][0]['moves'][0]['to'],'b')

    def test_complete_report_tamper_rejection(self):
        a=analyze_reachavoid(CONTROLS[0]['input'])
        paths=[['schema'],['winning'],['losing'],['rounds',0,'before'],['rounds',0,'checks',0,'qualified'],['rounds',0,'checks',0,'admitted'],['rounds',0,'added'],['states',0,'rank'],['states',0,'controller_choice'],['states',0,'moves',0,'target_winning'],['states',0,'moves',1,'optimal_controller_move'],['proof_graphs',0,'edges'],['proof_graphs',0,'rank_bound'],['policy_count'],['policy_atlas',0,'outcomes',0,'winning'],['policy_atlas',0,'outcomes',0,'witness','cycle_start'],['policy_atlas',1,'outcomes',0,'worst_steps'],['policy_summaries',0,'winning_policy_ids'],['uniform_optimal_policy_ids'],['limits']]
        for path in paths:
            b=copy.deepcopy(a);node=b
            for k in path[:-1]:node=node[k]
            node[path[-1]]='forged'
            with self.subTest(path=path),self.assertRaises(ValueError):verify_reachavoid(b)
        b=copy.deepcopy(a);b['extra']=1
        with self.assertRaises(ValueError):verify_reachavoid(b)

    def test_checker_does_not_import_or_call_generator(self):
        with tempfile.TemporaryDirectory()as d:
            p=Path(d)/'report.json';p.write_text(json.dumps(analyze_reachavoid(CONTROLS[0]['input'])))
            code="import sys,json;sys.modules['shieldlab.reachavoid']=None;from shieldlab.reachavoid_verify import verify_reachavoid;assert verify_reachavoid(json.load(open(sys.argv[1])))"
            r=subprocess.run([sys.executable,'-c',code,str(p)],capture_output=True,text=True,cwd=ROOT)
            self.assertEqual(r.returncode,0,r.stderr)

    def test_cli_entrypoints_atomic_reproduction_and_errors(self):
        with tempfile.TemporaryDirectory()as d:
            d=Path(d);inp=d/'input.json';out=d/'output.json';inp.write_text(json.dumps(CONTROLS[0]['input']))
            for module in ['shieldlab.reachavoid','shieldlab.reachavoid_cli']:
                r=subprocess.run([sys.executable,'-m',module,str(inp),'--output',str(out)],capture_output=True,text=True)
                self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(r.stdout,'');self.assertTrue(verify_reachavoid(json.loads(out.read_text())))
                r=subprocess.run([sys.executable,'-m',module,str(out),'--verify'],capture_output=True,text=True)
                self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(json.loads(r.stdout),{'valid':True,'schema':'shieldlab-reachavoid-v1'})
            out.write_text('preserve')
            for raw in ['{}','{"arena":{},"arena":{},"goals":[]}','NaN',' '*65537]:
                r=subprocess.run([sys.executable,'-m','shieldlab.reachavoid','-','--output',str(out)],input=raw,capture_output=True,text=True)
                self.assertEqual(r.returncode,2);self.assertEqual(r.stdout,'');self.assertEqual(out.read_text(),'preserve');self.assertNotIn('Traceback',r.stderr)
            huge=d/'oversize.json';huge.write_bytes(b' '*(16*1024*1024+1))
            r=subprocess.run([sys.executable,'-m','shieldlab.reachavoid',str(huge),'--verify','--output',str(out)],capture_output=True,text=True)
            self.assertEqual(r.returncode,2);self.assertEqual(r.stdout,'');self.assertEqual(out.read_text(),'preserve')
            self.assertEqual(sorted(p.name for p in d.iterdir()),['input.json','output.json','oversize.json'])

if __name__=='__main__':unittest.main()

"""Independent private prototype checks, unique strategy-pair play simulation."""
import copy
import itertools
import random
import unittest
from shieldlab.recurrence import analyze_recurrence


def graph(n, edges, owners, status):
    names = ['s' + str(i) for i in range(n)]
    return {'arena': {'states': [{'name': name,
            'owner': 'controller' if owners >> i & 1 else 'environment',
            'safe': status[i] != 0,
            'moves': [{'action': 'a' + str(j), 'to': names[t]} for j, t in enumerate(edges[i])]}
            for i, name in enumerate(names)]}, 'goals': [names[i] for i, k in enumerate(status) if k == 2]}


def pairs(request):
    states = request['arena']['states']; by = {s['name']: s for s in states}
    goals = set(request['goals']); players = ['controller', 'environment']
    controlled = {p: [s for s in states if s['owner'] == p and s['safe']] for p in players}
    choices = {p: list(itertools.product(*(range(len(s['moves'])) for s in controlled[p]))) for p in players}
    verdicts = {p: [[True] * len(states) for _ in choices[p]] for p in players}
    for ci, c in enumerate(choices['controller']):
        for ei, e in enumerate(choices['environment']):
            policy = {s['name']: j for p, ns in [('controller', c), ('environment', e)]
                      for s, j in zip(controlled[p], ns)}
            for ri, root in enumerate(by):
                path = []; n = root
                while by[n]['safe'] and n not in path:
                    path.append(n); n = by[n]['moves'][policy[n]]['to']
                cw = by[n]['safe'] and bool(set(path[path.index(n):]) & goals)
                verdicts['controller'][ci][ri] &= cw
                verdicts['environment'][ei][ri] &= not cw
    return verdicts


def matrix_policy_values(request, row, player):
    """Third algorithm: transitive closure, no path traversal or play pairs."""
    ss=request['arena']['states'];ns=[s['name']for s in ss];ix={n:i for i,n in enumerate(ns)}
    policy={r['state']:r['action']for r in row['policy']};safe=[i for i,s in enumerate(ss)if s['safe']]
    goals={ix[n]for n in request['goals']};n=len(ss)
    edges=[]
    for i,s in enumerate(ss):
        if not s['safe']:continue
        for m in s['moves']:
            if s['owner']!=player or policy[s['name']]==m['action']:edges.append((i,ix[m['to']]))
    def closure(allowed):
        a=[[False]*n for _ in range(n)]
        for i,j in edges:
            if i in allowed and j in allowed:a[i][j]=True
        for k in range(n):
            for i in range(n):
                for j in range(n):a[i][j]=a[i][j]or(a[i][k]and a[k][j])
        return a
    sr=closure(set(safe));ng=closure(set(safe)-goals)
    out=[]
    for root in range(n):
        if root not in safe:out.append(player=='environment');continue
        reachable={i for i in safe if i==root or sr[root][i]}
        if player=='controller':
            leak=any(i in reachable and j not in safe for i,j in edges)
            cycle=any(i in reachable and ng[i][i]for i in safe)
            out.append(not leak and not cycle)
        else:out.append(not any(g in reachable and sr[g][g]for g in goals))
    return out


class RecurrencePrototypeTests(unittest.TestCase):
    def check(self, req):
        before = copy.deepcopy(req); r = analyze_recurrence(req)
        self.assertEqual(req, before)
        ref = pairs(req)
        for p in ['controller', 'environment']:
            self.assertEqual([[o['winning'] for o in row['outcomes']] for row in r['policy_atlases'][p]], ref[p])
            self.assertTrue(r['uniform_policy_ids'][p])
        names = [s['name'] for s in req['arena']['states']]
        self.assertEqual(r['winning'], [n for i, n in enumerate(names) if any(a[i] for a in ref['controller'])])
        for o in r['outer']:
            self.assertLessEqual(set(o['after']), set(o['before']))
            self.assertEqual(o['inner'][-1]['after'], o['inner'][-1]['before'])
            self.assertEqual(o['inner'][0]['before'], [])
            for inner in o['inner']:
                self.assertLessEqual(set(inner['before']), set(inner['after']))
        self.assertEqual(r['outer'][-1]['before'], r['outer'][-1]['after'])
        for a in r['policy_atlases'].values():
            for row in a:
                for out in row['outcomes']:
                    w = out['failure']
                    if w is None: continue
                    path = w['path']; n = out['start']; nodes = []
                    for edge in path:
                        self.assertEqual(n, edge['from']);nodes.append(n);n = edge['to']
                    if w['cycle_start'] is not None:
                        k = w['cycle_start'];self.assertEqual(nodes[k], n);self.assertGreater(len(path) - k, 0)
                        hasgoal = bool(set(nodes[k:]) & set(req['goals']))
                        self.assertEqual(hasgoal, w['kind'] == 'safe_recurrent_lasso')
        return r

    def test_two_state_exhaustive(self):
        subsets = [(0,), (1,), (0, 1)]; count = 0
        for edges in itertools.product(subsets, repeat=2):
            for owners in range(4):
                for status in itertools.product(range(3), repeat=2):
                    self.check(graph(2, edges, owners, status));count += 1
        self.assertEqual(count, 324)

    def test_three_state_all_graphs_and_safety_target_ownership(self):
        subsets = [x for k in [1, 2, 3] for x in itertools.combinations(range(3), k)]
        count = 0
        for edges in itertools.product(subsets, repeat=3):
            for owners in range(8):
                for status in itertools.product(range(3), repeat=3):
                    self.check(graph(3, edges, owners, status));count += 1
        self.assertEqual(count, 74088)

    def test_larger_seeded(self):
        rng = random.Random(802194)
        for k in range(160):
            n = 4 + k % 3
            self.check(graph(n, [rng.sample(range(n), rng.randint(1, 3)) for _ in range(n)],
                             rng.randrange(1 << n), [rng.randrange(3) for _ in range(n)]))

    def test_first_hit_is_not_recurrence_and_goal_outgoing_matters(self):
        # Hit target immediately, then an irreversible target-free safe wait.
        a = self.check(graph(2, [(1,), (1,)], 0, [2, 1]))
        self.assertEqual(a['winning'], [])
        # Goal outgoing is live, even when the root is the goal.
        b = self.check(graph(2, [(1,), (1,)], 0, [2, 0]))
        self.assertEqual(b['winning'], [])
        # Target self-loop is infinitely many visits, not terminal success.
        c = self.check(graph(1, [(0,)], 0, [2]));self.assertEqual(c['winning'], ['s0'])

    def test_owner_flip_and_winning_target_do_not_make_every_move_permissive(self):
        a = self.check(graph(2, [(0, 1), (0,)], 1, [1, 2]))
        b = self.check(graph(2, [(0, 1), (0,)], 0, [1, 2]))
        self.assertEqual(a['winning'], ['s0', 's1']);self.assertEqual(b['winning'], [])
        self.assertEqual(a['states'][0]['controller_policy_ids'], [1])

    def test_full_policy_boundary_both_owners(self):
        for owners in [0, 63]:
            r = self.check(graph(6, [(i, (i + 1) % 6, (i + 2) % 6) for i in range(6)], owners, [2, 1, 1, 1, 1, 1]))
            self.assertEqual(max(map(len, r['policy_atlases'].values())), 729)

    def test_empty_targets_all_targets_and_unsafe_stops(self):
        self.assertEqual(self.check(graph(2, [(1,), (0,)], 1, [1, 1]))['winning'], [])
        self.assertEqual(self.check(graph(2, [(1,), (0,)], 1, [2, 2]))['winning'], ['s0', 's1'])
        self.assertEqual(self.check(graph(2, [(1,), (0,)], 1, [0, 2]))['winning'], [])

    def test_independent_full_replay_and_leaf_mutations(self):
        from shieldlab.recurrence_verify import verify_recurrence
        rng = random.Random(803777)
        subsets = [(0,), (1,), (0, 1)]
        for edges in itertools.product(subsets, repeat=2):
            for owners in range(4):
                for status in itertools.product(range(3), repeat=2):
                    self.assertTrue(verify_recurrence(analyze_recurrence(graph(2, edges, owners, status))))
        for k in range(100):
            n = 4 + k % 3
            req = graph(n, [rng.sample(range(n), rng.randint(1, 3)) for _ in range(n)],
                        rng.randrange(1 << n), [rng.randrange(3) for _ in range(n)])
            self.assertTrue(verify_recurrence(analyze_recurrence(req)))
        report = analyze_recurrence(graph(2, [(0, 1), (0,)], 1, [1, 2]))
        paths = []
        def leaves(node, prefix):
            if isinstance(node, dict):
                for k, v in node.items():
                    if not prefix and k == 'input': continue
                    leaves(v, prefix + [k])
            elif isinstance(node, list):
                for i, v in enumerate(node): leaves(v, prefix + [i])
            else: paths.append(prefix)
        leaves(report, [])
        for path in paths:
            forged = copy.deepcopy(report);node = forged
            for k in path[:-1]:node = node[k]
            v = node[path[-1]]
            node[path[-1]] = (not v) if type(v) is bool else (v + 1 if type(v) is int else 'forged')
            with self.subTest(path=path), self.assertRaises(ValueError):verify_recurrence(forged)
        self.assertEqual(len(paths), 163)
        print('individually rejected non-input primitive mutations:', len(paths))

    def test_checker_generator_disabled(self):
        import json, subprocess, sys, tempfile
        from pathlib import Path
        report = analyze_recurrence(graph(2, [(0, 1), (0,)], 1, [1, 2]))
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / 'report.json';f.write_text(json.dumps(report))
            code = "import sys,json;sys.modules['shieldlab.recurrence']=None;from shieldlab.recurrence_verify import verify_recurrence;assert verify_recurrence(json.load(open(sys.argv[1])))"
            r = subprocess.run([sys.executable, '-c', code, str(f)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)

    def test_original_controls_reproduction(self):
        import importlib.util, json
        from pathlib import Path
        from shieldlab.recurrence_verify import verify_recurrence
        root = Path(__file__).resolve().parents[1]
        spec = importlib.util.spec_from_file_location('recurrence_controls', root/'tools/make_recurrence_controls.py')
        module = importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        controls = module.controls()
        self.assertEqual(json.dumps(controls, indent=2)+'\n', (root/'docs/recurrence-controls.json').read_text())
        self.assertEqual(len(controls), 12)
        for c in controls:
            report = self.check(c['input'])
            self.assertEqual(report['winning'], c['expected_winning']);self.assertTrue(verify_recurrence(report))

    def test_strict_full_report_types_keys_and_order(self):
        from shieldlab.recurrence_verify import verify_recurrence
        report = analyze_recurrence(graph(2, [(0, 1), (0,)], 1, [1, 2]))
        bad = []
        r = copy.deepcopy(report);r['extra'] = True;bad.append(r)
        r = copy.deepcopy(report);r['states'][0]['winning'] = 1;bad.append(r)
        r = copy.deepcopy(report);r['outer'][0]['index'] = 0.0;bad.append(r)
        r = copy.deepcopy(report);r['winning'] = tuple(r['winning']);bad.append(r)
        r = copy.deepcopy(report);r['states'].reverse();bad.append(r)
        r = copy.deepcopy(report);del r['proof_graphs'];bad.append(r)
        for r in bad:
            with self.assertRaises(ValueError):verify_recurrence(r)

    def test_cli_atomic_strict_bounded_entrypoints(self):
        import json, subprocess, sys, tempfile
        from pathlib import Path
        from shieldlab.recurrence_verify import verify_recurrence
        req = graph(2, [(0, 1), (0,)], 1, [1, 2])
        with tempfile.TemporaryDirectory() as d:
            d = Path(d); inp = d/'input.json'; out = d/'report.json'
            inp.write_text(json.dumps(req))
            for module in ['shieldlab.recurrence', 'shieldlab.recurrence_cli']:
                cmd = [sys.executable, '-m', module]
                r = subprocess.run(cmd+[str(inp), '--output', str(out)], capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, r.stderr);self.assertEqual(r.stdout, '')
                self.assertTrue(verify_recurrence(json.loads(out.read_text())))
                r = subprocess.run(cmd+[str(out), '--verify'], capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertEqual(json.loads(r.stdout), {'valid': True, 'schema': 'shieldlab-recurrence-v1'})
                for raw in ['{}', '{"arena":{},"arena":{},"goals":[]}', 'NaN', ' '*65537, '\ud800']:
                    out.write_text('preserve')
                    data = raw.encode('utf-8', errors='surrogatepass')
                    r = subprocess.run(cmd+['-', '--output', str(out)], input=data, capture_output=True)
                    self.assertEqual(r.returncode, 2, r.stderr);self.assertEqual(r.stdout, b'')
                    self.assertEqual(out.read_text(), 'preserve');self.assertNotIn(b'Traceback', r.stderr)
            huge = d/'huge.json';huge.write_bytes(b' '*(16*1024*1024+1));out.write_text('preserve')
            r = subprocess.run([sys.executable, '-m', 'shieldlab.recurrence', str(huge), '--verify', '--output', str(out)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 2);self.assertEqual(out.read_text(), 'preserve')
            self.assertEqual(r.stdout, '');self.assertNotIn('Traceback', r.stderr)

    def test_independent_matrix_cycle_and_proof_obligations(self):
        import json
        from pathlib import Path
        controls=json.loads((Path(__file__).resolve().parents[1]/'docs/recurrence-controls.json').read_text())
        cases=[c['input']for c in controls]
        for edges in itertools.product([(0,),(1,),(0,1)],repeat=2):
            for owners in range(4):
                for status in itertools.product(range(3),repeat=2):cases.append(graph(2,edges,owners,status))
        rng=random.Random(933721)
        for k in range(120):
            n=4+k%3;cases.append(graph(n,[rng.sample(range(n),rng.randint(1,3))for _ in range(n)],rng.randrange(1<<n),[rng.randrange(3)for _ in range(n)]))
        for req in cases:
            r=analyze_recurrence(req)
            for player,atlas in r['policy_atlases'].items():
                for row in atlas:self.assertEqual(matrix_policy_values(req,row,player),[o['winning']for o in row['outcomes']])
            for proof in r['proof_graphs']:
                row=r['policy_atlases'][proof['player']][proof['policy_id']]
                self.assertTrue(matrix_policy_values(req,row,proof['player'])[[s['name']for s in req['arena']['states']].index(proof['start'])])
        self.assertEqual(len(cases),456)

    def test_state_move_target_permutation_and_output_isolation(self):
        import json
        from pathlib import Path
        controls=json.loads((Path(__file__).resolve().parents[1]/'docs/recurrence-controls.json').read_text())
        rng=random.Random(640921)
        for c in controls:
            before=analyze_recurrence(c['input']);req=copy.deepcopy(c['input'])
            rng.shuffle(req['arena']['states']);rng.shuffle(req['goals'])
            for state in req['arena']['states']:rng.shuffle(state['moves'])
            after=self.check(req)
            self.assertEqual(set(before['winning']),set(after['winning']))
            for player in ['controller','environment']:
                def mapping(r):
                    return {tuple(sorted((c['state'],c['action'])for c in row['policy'])):
                            {o['start']:o['winning']for o in row['outcomes']}for row in r['policy_atlases'][player]}
                self.assertEqual(mapping(before),mapping(after))
            after['input']['arena']['states'][0]['name']='changed'
            self.assertNotEqual(req['arena']['states'][0]['name'],'changed')

    def test_validation(self):
        for bad in [{}, None, {'arena': {'states': []}, 'goals': []},
                    graph(1, [(0,)], 0, [0]) | {'goals': ['s0']},
                    graph(1, [(0,)], 0, [2]) | {'goals': ['s0', 's0']}]:
            with self.assertRaises((ValueError, TypeError)): analyze_recurrence(bad)


if __name__ == '__main__':
    unittest.main()

"""Independent full-report replay by complete positional-strategy pairs.

No generator import, recursive cycle search or nested-set solver call.
"""
from itertools import product
from .recurrence_input import validate_request


def replay_recurrence(request):
    request = validate_request(request)
    ss = request['arena']['states']; ns = [s['name'] for s in ss]; index = {n: i for i, n in enumerate(ns)}
    count = len(ns); goals = set(request['goals']); ps = ['controller', 'environment']
    targets = [[index[m['to']] for m in s['moves']] for s in ss]
    active = {p: [i for i, s in enumerate(ss) if s['safe'] and s['owner'] == p] for p in ps}
    assignments = {p: list(product(*(range(len(ss[i]['moves'])) for i in active[p]))) for p in ps}
    policies = {p: [dict(zip(active[p], a)) for a in assignments[p]] for p in ps}
    failures = {p: [[[] for _ in ns] for _ in policies[p]] for p in ps}
    for ci, c in enumerate(policies['controller']):
        for ei, e in enumerate(policies['environment']):
            selection = c | e
            for root in range(count):
                n = root; seen = {}; nodes = []; path = []; key = []
                while ss[n]['safe'] and n not in seen:
                    seen[n] = len(nodes); nodes.append(n)
                    k = selection[n]; m = ss[n]['moves'][k]
                    path.append({'from': ns[n], 'action': m['action'], 'to': m['to']});key.append(k)
                    n = targets[n][k]
                if not ss[n]['safe']:
                    p = 'controller'; witness = {'kind': 'unsafe_path', 'path': path, 'cycle_start': None}
                else:
                    start = seen[n]; hit = any(ns[j] in goals for j in nodes[start:])
                    p = 'environment' if hit else 'controller'
                    witness = {'kind': 'safe_recurrent_lasso' if hit else 'goal_avoiding_lasso',
                               'path': path, 'cycle_start': start}
                failures[p][ci if p == 'controller' else ei][root].append((tuple(key), witness))
    atlases = {}
    for p in ps:
        rows = []
        for pi, policy in enumerate(policies[p]):
            outcomes = []
            for i in range(count):
                bad = failures[p][pi][i]
                witness = min(bad, key=lambda t: t[0])[1] if bad else None
                outcomes.append({'start': ns[i], 'winning': not bad, 'failure': witness})
            rows.append({'id': pi, 'policy': [{'state': ns[i], 'action': ss[i]['moves'][k]['action']}
                                             for i, k in policy.items()], 'outcomes': outcomes})
        atlases[p] = rows
    winning = [n for i, n in enumerate(ns) if any(row['outcomes'][i]['winning'] for row in atlases['controller'])]
    losing = [n for n in ns if n not in winning]
    summaries = [{'state': n, 'winning': n in winning,
                  'controller_policy_ids': [r['id'] for r in atlases['controller'] if r['outcomes'][i]['winning']],
                  'environment_policy_ids': [r['id'] for r in atlases['environment'] if r['outcomes'][i]['winning']]}
                 for i, n in enumerate(ns)]
    uniform = {p: [r['id'] for r in atlases[p] if all(r['outcomes'][i]['winning'] for i, n in enumerate(ns)
               if n in (winning if p == 'controller' else losing))] for p in ps}
    for i, n in enumerate(ns):
        if bool(summaries[i]['environment_policy_ids']) != (n in losing):
            raise ValueError('positional determinacy mismatch')
    if not all(uniform.values()):
        raise ValueError('no uniform positional policy')
    # Explicit bit-vector Boolean evaluation; all intermediate obligations,
    # including unchanged inner and outer rounds, are independently rebuilt.
    safe_mask = sum(1 << i for i, s in enumerate(ss) if s['safe'])
    ordered = lambda mask: [n for i, n in enumerate(ns) if mask >> i & 1]
    outer = []; z = safe_mask
    while True:
        inner = []; y = 0
        while True:
            nxt = 0; checks = []
            for i, s in enumerate(ss):
                tz = [bool(z >> j & 1) for j in targets[i]]
                ty = [bool(y >> j & 1) for j in targets[i]]
                exists = s['owner'] == 'controller'
                rz = (True in tz) if exists else (False not in tz)
                ry = (True in ty) if exists else (False not in ty)
                reset = ns[i] in goals and rz; admitted = s['safe'] and (reset or ry)
                if admitted: nxt |= 1 << i
                checks.append({'state': ns[i], 'operator': 'exists' if exists else 'all', 'safe': s['safe'],
                               'goal': ns[i] in goals, 'target_in_outer': tz, 'target_in_inner': ty,
                               'reset': reset, 'progress': ry, 'admitted': admitted})
            inner.append({'index': len(inner), 'before': ordered(y), 'checks': checks,
                          'after': ordered(nxt), 'added': ordered(nxt & ~y)})
            if nxt == y: break
            y = nxt
        outer.append({'index': len(outer), 'before': ordered(z), 'inner': inner,
                      'after': ordered(y), 'removed': ordered(z & ~y)})
        if z == y: break
        z = y
    if ordered(z) != winning: raise ValueError('strategy-pair/fixed-point disagreement')
    proofs = []
    for root in range(count):
        p = 'controller' if ns[root] in winning else 'environment'
        pi = uniform[p][0]; policy = policies[p][pi]
        frontier = [root]; visited = {root}; edges = []
        for i in frontier:
            if not ss[i]['safe']: continue
            for mi, m in enumerate(ss[i]['moves']):
                if ss[i]['owner'] == p and policy[i] != mi: continue
                edges.append({'from': ns[i], 'action': m['action'], 'to': m['to']})
                j = targets[i][mi]
                if j not in visited: visited.add(j);frontier.append(j)
        proofs.append({'start': ns[root], 'player': p, 'policy_id': pi, 'nodes': [ns[i] for i in frontier],
                       'edges': edges, 'unsafe': [ns[i] for i in frontier if not ss[i]['safe']]})
    return {'schema': 'shieldlab-recurrence-v1', 'input': request, 'outer': outer,
            'winning': winning, 'losing': losing, 'policy_atlases': atlases,
            'states': summaries, 'uniform_policy_ids': uniform, 'proof_graphs': proofs}


def verify_recurrence(report):
    if type(report) is not dict or type(report.get('input')) is not dict:
        raise ValueError('expected complete recurrence report')
    expected = replay_recurrence(report['input'])
    def same(a, b):
        if type(a) is not type(b): return False
        if type(b) is dict:
            return set(a) == set(b) and all(same(a[k], v) for k, v in b.items())
        if type(b) is list:
            return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
        return a == b
    if not same(report, expected): raise ValueError('recurrence report replay mismatch')
    return True

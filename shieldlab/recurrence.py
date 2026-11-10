"""Exact bounded safe recurrent-target games, with live target moves.

Established Buchi fixed-point theory; no fairness or real-agent guarantee.
"""
from itertools import product
from .recurrence_input import validate_request



def _outcome(states, goals, policy, player, root):
    """Explore simple play prefixes, not strategy-pair simulation.

    A controller policy wins iff no unsafe state and no target-avoiding cycle
    is reachable. An environment policy wins the complement iff no safe cycle
    containing a target is reachable. Unsafe stops immediately for either.
    """
    by = {s['name']: s for s in states}

    def visit(n, nodes, edges):
        if not by[n]['safe']:
            return {'kind': 'unsafe_path', 'path': edges, 'cycle_start': None} if player == 'controller' else None
        if n in nodes:
            k = nodes.index(n)
            recurring_goal = any(x in goals for x in nodes[k:])
            bad = not recurring_goal if player == 'controller' else recurring_goal
            return {'kind': 'goal_avoiding_lasso' if player == 'controller' else 'safe_recurrent_lasso',
                    'path': edges, 'cycle_start': k} if bad else None
        s = by[n]
        moves = [s['moves'][policy[n]]] if s['owner'] == player else s['moves']
        for m in moves:
            bad = visit(m['to'], nodes + [n], edges + [{'from': n, **m}])
            if bad is not None:
                return bad
        return None

    bad = visit(root, [], [])
    return {'start': root, 'winning': bad is None, 'failure': bad}


def analyze_recurrence(data):
    data = validate_request(data)
    states = data['arena']['states']; names = [s['name'] for s in states]
    goals = set(data['goals']); safe = {s['name'] for s in states if s['safe']}
    order = lambda ns: [n for n in names if n in ns]
    z = set(safe); outer = []
    while True:
        y = set(); inner = []
        while True:
            checks = []; after = set()
            for s in states:
                n = s['name']; tz = [m['to'] in z for m in s['moves']]
                ty = [m['to'] in y for m in s['moves']]
                op = any if s['owner'] == 'controller' else all
                reset = n in goals and op(tz)
                progress = op(ty)
                admitted = s['safe'] and (reset or progress)
                if admitted:
                    after.add(n)
                checks.append({'state': n, 'operator': 'exists' if s['owner'] == 'controller' else 'all',
                               'safe': s['safe'], 'goal': n in goals, 'target_in_outer': tz,
                               'target_in_inner': ty, 'reset': reset, 'progress': progress, 'admitted': admitted})
            inner.append({'index': len(inner), 'before': order(y), 'checks': checks,
                          'after': order(after), 'added': order(after - y)})
            if after == y:
                break
            y = after
        outer.append({'index': len(outer), 'before': order(z), 'inner': inner,
                      'after': order(y), 'removed': order(z - y)})
        if y == z:
            break
        z = y
    atlas = {}
    for player in ['controller', 'environment']:
        controlled = [s for s in states if s['owner'] == player and s['safe']]
        rows = []
        for choices in product(*(range(len(s['moves'])) for s in controlled)):
            policy = {s['name']: i for s, i in zip(controlled, choices)}
            rows.append({'id': len(rows), 'policy': [{'state': s['name'], 'action': s['moves'][i]['action']}
                         for s, i in zip(controlled, choices)],
                         'outcomes': [_outcome(states, goals, policy, player, n) for n in names]})
        atlas[player] = rows
    summaries = []
    for i, n in enumerate(names):
        ids = {p: [a['id'] for a in rows if a['outcomes'][i]['winning']] for p, rows in atlas.items()}
        assert bool(ids['controller']) == (n in z)
        assert bool(ids['environment']) == (n not in z)
        summaries.append({'state': n, 'winning': n in z,
                          'controller_policy_ids': ids['controller'], 'environment_policy_ids': ids['environment']})
    uniform = {p: [a['id'] for a in rows if all(a['outcomes'][i]['winning'] for i, n in enumerate(names)
               if (n in z) == (p == 'controller'))] for p, rows in atlas.items()}
    assert all(uniform.values())
    proofs = []
    for root in names:
        p = 'controller' if root in z else 'environment'
        a = atlas[p][uniform[p][0]]
        policy = {r['state']: r['action'] for r in a['policy']}
        queue = [root]; seen = {root}; edges = []
        by = {s['name']: s for s in states}
        for n in queue:
            s = by[n]
            if not s['safe']:
                continue
            for m in s['moves']:
                if s['owner'] == p and m['action'] != policy[n]:
                    continue
                edges.append({'from': n, **m})
                if m['to'] not in seen:
                    seen.add(m['to']); queue.append(m['to'])
        proofs.append({'start': root, 'player': p, 'policy_id': a['id'], 'nodes': queue,
                       'edges': edges, 'unsafe': [n for n in queue if not by[n]['safe']]})
    return {'schema': 'shieldlab-recurrence-v1', 'input': data, 'outer': outer,
            'winning': order(z), 'losing': order(set(names) - z), 'policy_atlases': atlas,
            'states': summaries, 'uniform_policy_ids': uniform, 'proof_graphs': proofs}


if __name__ == '__main__':
    from .recurrence_cli import main
    raise SystemExit(main())

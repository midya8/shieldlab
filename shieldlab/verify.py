"""Independent losing-attractor replay and positional-policy graph oracle."""
from itertools import product
from .core import validate


def policy_oracle(data):
    data = validate(data); states = data['states']; by = {s['name']: s for s in states}
    cs = [s for s in states if s['owner'] == 'controller']; winners = set()
    for choices in product(*(range(len(s['moves'])) for s in cs)):
        policy = {s['name']: j for s, j in zip(cs, choices)}
        for start in by:
            seen = {start}; queue = [start]
            for n in queue:
                s = by[n]; moves = [s['moves'][policy[n]]] if s['owner'] == 'controller' else s['moves']
                for m in moves:
                    if m['to'] not in seen: seen.add(m['to']); queue.append(m['to'])
            if all(by[n]['safe'] for n in seen): winners.add(start)
    return [n for n in by if n in winners]


def _equal(a, b, path='report'):
    if type(a) is not type(b): raise ValueError(path + ': wrong type')
    if isinstance(a, dict):
        if set(a) != set(b): raise ValueError(path + ': keys mismatch')
        for k in a: _equal(a[k], b[k], path + '.' + k)
    elif isinstance(a, list):
        if len(a) != len(b): raise ValueError(path + ': length mismatch')
        for i, (x, y) in enumerate(zip(a, b)): _equal(x, y, path + '[' + str(i) + ']')
    elif a != b: raise ValueError(path + ': value mismatch')


def verify(report):
    if not isinstance(report, dict) or 'input' not in report: raise ValueError('report requires input')
    data = validate(report['input']); states = data['states']; names = [s['name'] for s in states]
    by = {s['name']: s for s in states}; lost = {s['name'] for s in states if not s['safe']}
    rank = {n: 0 for n in lost}; rounds = []
    order = lambda ns: [n for n in names if n in ns]
    while True:
        before = set(names) - lost; new = set(lost); checks = []
        for s in states:
            ts = [m['to'] not in lost for m in s['moves']]
            if s['owner'] == 'environment':
                qualifies = not any(m['to'] in lost for m in s['moves'])
            else: qualifies = not all(m['to'] in lost for m in s['moves'])
            if not s['safe'] or not qualifies: new.add(s['name'])
            checks.append({'state': s['name'], 'operator': 'exists' if s['owner'] == 'controller' else 'all',
                           'safe': s['safe'], 'target_in_before': ts, 'qualified': qualifies, 'kept': s['safe'] and qualifies})
        removed = new - lost
        rounds.append({'index': len(rounds), 'before': order(before), 'checks': checks,
                       'after': order(set(names) - new), 'removed': order(removed)})
        for n in removed: rank[n] = len(rounds)
        if new == lost: break
        lost = new
    winning = [n for n in names if n not in lost]
    if winning != policy_oracle(data): raise ValueError('independent policy oracle disagrees')
    records = []
    for s in states:
        n = s['name']; win = n not in lost; moves = []
        for m in s['moves']:
            moves.append({**m, 'target_winning': m['to'] not in lost, 'target_rank': rank.get(m['to']),
                          'safe_move': win and s['owner'] == 'controller' and m['to'] not in lost,
                          'rank_decreasing': n in rank and m['to'] in rank and rank[m['to']] < rank[n]})
        c = [m['action'] for m in moves if m['safe_move']]
        e = [m['action'] for m in moves if s['owner'] == 'environment' and not win and s['safe'] and m['rank_decreasing']]
        records.append({'name': n, 'owner': s['owner'], 'safe': s['safe'], 'winning': win, 'rank': rank.get(n),
                        'moves': moves, 'controller_choice': c[0] if c else None, 'environment_choice': e[0] if e else None})
    graphs = []; rb = {s['name']: s for s in records}
    for root in records:
        seen = [root['name']]; edges = []
        for n in seen:
            s = rb[n]
            if not root['winning'] and not s['safe']: continue
            controlled = 'controller' if root['winning'] else 'environment'
            choice = s[controlled + '_choice']
            for m in s['moves']:
                if s['owner'] == controlled and m['action'] != choice: continue
                edges.append({'from': n, 'action': m['action'], 'to': m['to']})
                if m['to'] not in seen: seen.append(m['to'])
        if root['winning']:
            if any(n in lost for n in seen): raise ValueError('invariant leaves winning region')
        else:
            if any(by[e['from']]['safe'] and not rank[e['to']] < rank[e['from']] for e in edges): raise ValueError('rank does not descend')
        graphs.append({'start': root['name'], 'kind': 'closed_invariant' if root['winning'] else 'ranked_counterstrategy',
                       'nodes': seen, 'edges': edges, 'bad': [n for n in seen if not by[n]['safe']], 'rank_bound': rank.get(root['name'])})
    expected = {'schema': 'shieldlab-v1', 'input': data, 'rounds': rounds, 'winning': winning,
                'losing': order(lost), 'states': records, 'proof_graphs': graphs}
    _equal(expected, report)
    return True

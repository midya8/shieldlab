"""Finite total turn-based safety games, with synchronous fixed-point witnesses."""
import re


def validate(data):
    if not isinstance(data, dict) or set(data) != {'states'}:
        raise ValueError('input must contain exactly states')
    states = data['states']
    if not isinstance(states, list) or not 1 <= len(states) <= 6:
        raise ValueError('states must contain one to six records')
    names = []
    for s in states:
        if not isinstance(s, dict) or set(s) != {'name', 'owner', 'safe', 'moves'}:
            raise ValueError('state keys must be name, owner, safe, moves')
        name = s['name']
        if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,15}', name) or name in names:
            raise ValueError('state names must be unique ASCII identifiers, at most 16 characters')
        names.append(name)
        if s['owner'] not in ('controller', 'environment') or type(s['safe']) is not bool:
            raise ValueError('owner must be controller/environment and safe must be boolean')
        if not isinstance(s['moves'], list) or not 1 <= len(s['moves']) <= 3:
            raise ValueError('each state needs one to three moves; dead ends are rejected')
        actions = []
        for m in s['moves']:
            if not isinstance(m, dict) or set(m) != {'action', 'to'}:
                raise ValueError('move keys must be action and to')
            a = m['action']
            if not isinstance(a, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,15}', a) or a in actions:
                raise ValueError('actions must be unique per state, at most 16 ASCII identifier characters')
            actions.append(a)
    if any(m['to'] not in names for s in states for m in s['moves']):
        raise ValueError('every move target must name a declared state')
    return {'states': [{'name': s['name'], 'owner': s['owner'], 'safe': s['safe'],
                        'moves': [dict(m) for m in s['moves']]} for s in states]}


def analyze(data):
    data = validate(data)
    states = data['states']; names = [s['name'] for s in states]
    idx = {n: i for i, n in enumerate(names)}
    mask = sum(1 << i for i, s in enumerate(states) if s['safe'])
    ranks = [None if s['safe'] else 0 for s in states]
    ordered = lambda bits: [n for i, n in enumerate(names) if bits & (1 << i)]
    rounds = []
    while True:
        checks = []; after = 0
        for i, s in enumerate(states):
            targets = [bool(mask & (1 << idx[m['to']])) for m in s['moves']]
            qualified = any(targets) if s['owner'] == 'controller' else all(targets)
            kept = s['safe'] and qualified
            if kept: after |= 1 << i
            checks.append({'state': s['name'], 'operator': 'exists' if s['owner'] == 'controller' else 'all',
                           'safe': s['safe'], 'target_in_before': targets, 'qualified': qualified, 'kept': kept})
        removed = mask & ~after
        rounds.append({'index': len(rounds), 'before': ordered(mask), 'checks': checks,
                       'after': ordered(after), 'removed': ordered(removed)})
        for i in range(len(states)):
            if removed & (1 << i): ranks[i] = len(rounds)
        if after == mask: break
        mask = after
    records = []
    for i, s in enumerate(states):
        win = bool(mask & (1 << i)); moves = []
        for m in s['moves']:
            j = idx[m['to']]; tw = bool(mask & (1 << j))
            moves.append({**m, 'target_winning': tw, 'target_rank': ranks[j],
                          'safe_move': win and s['owner'] == 'controller' and tw,
                          'rank_decreasing': ranks[i] is not None and ranks[j] is not None and ranks[j] < ranks[i]})
        records.append({'name': s['name'], 'owner': s['owner'], 'safe': s['safe'], 'winning': win,
                        'rank': ranks[i], 'moves': moves,
                        'controller_choice': next((m['action'] for m in moves if m['safe_move']), None),
                        'environment_choice': next((m['action'] for m in moves if s['owner'] == 'environment' and not win and s['safe'] and m['rank_decreasing']), None)})
    graphs = []
    for root in records:
        queue = [root['name']]; seen = {root['name']}; edges = []
        for name in queue:
            s = records[idx[name]]
            if not root['winning'] and not s['safe']: continue
            for m in s['moves']:
                selected = (s['owner'] == 'environment' or m['action'] == s['controller_choice']) if root['winning'] else (s['owner'] == 'controller' or m['action'] == s['environment_choice'])
                if not selected: continue
                edges.append({'from': name, 'action': m['action'], 'to': m['to']})
                if m['to'] not in seen: seen.add(m['to']); queue.append(m['to'])
        graphs.append({'start': root['name'], 'kind': 'closed_invariant' if root['winning'] else 'ranked_counterstrategy',
                       'nodes': queue, 'edges': edges, 'bad': [n for n in queue if not states[idx[n]]['safe']],
                       'rank_bound': root['rank']})
    return {'schema': 'shieldlab-v1', 'input': data, 'rounds': rounds, 'winning': ordered(mask),
            'losing': [n for n in names if n not in ordered(mask)], 'states': records, 'proof_graphs': graphs}

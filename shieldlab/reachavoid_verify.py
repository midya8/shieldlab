"""Independent complete positional-policy/path replay, without an attractor.

Enumerates vertex-simple play prefixes in a fixed policy graph, terminating on
first goal, unsafe vertex or repeated vertex. No solver import or call.
"""
from itertools import product
from .reachavoid_input import validate_request, LIMITS
from .verify import _equal


def _paths(by, goals, policy, start):
    stack = [(start, [], [])]; longest = None
    while stack:
        n, nodes, path = stack.pop()
        if n in goals:
            candidate = {'start': start, 'winning': True, 'worst_steps': len(path),
                         'witness': {'kind': 'longest_goal_path', 'path': path, 'cycle_start': None}}
            if longest is None or len(path) > longest['worst_steps']: longest = candidate
            continue
        if not by[n]['safe'] or n in nodes:
            return {'start': start, 'winning': False, 'worst_steps': None,
                    'witness': {'kind': 'unsafe_path' if not by[n]['safe'] else 'goal_avoiding_lasso',
                                'path': path, 'cycle_start': nodes.index(n) if n in nodes else None}}
        moves = by[n]['moves']
        if by[n]['owner'] == 'controller': moves = [moves[policy[n]]]
        for m in reversed(moves):
            stack.append((m['to'], nodes + [n], path + [{'from': n, **m}]))
    return longest


def _safe_under_policy(by, goals, policy, start):
    seen = {start}; stack = [start]
    while stack:
        n = stack.pop()
        if not by[n]['safe']: return False
        if n in goals: continue
        moves = by[n]['moves']
        if by[n]['owner'] == 'controller': moves = [moves[policy[n]]]
        for m in moves:
            if m['to'] not in seen: seen.add(m['to']); stack.append(m['to'])
    return True


def replay_reachavoid(request):
    data = validate_request(request); states = data['arena']['states']; goals = set(data['goals'])
    names = [s['name'] for s in states]; by = {s['name']: s for s in states}
    cs = [s for s in states if s['owner'] == 'controller' and s['safe'] and s['name'] not in goals]
    atlas = []; safe = set(); best = {}
    for choices in product(*(range(len(s['moves'])) for s in cs)):
        policy = dict(zip([s['name'] for s in cs], choices))
        outcomes = []
        for n in names:
            result = _paths(by, goals, policy, n); outcomes.append(result)
            if result['winning']: best[n] = min(best.get(n, 999), result['worst_steps'])
            if _safe_under_policy(by, goals, policy, n): safe.add(n)
        atlas.append({'id': len(atlas), 'policy': [{'state': s['name'], 'action': s['moves'][j]['action']}
                     for s, j in zip(cs, choices)], 'outcomes': outcomes})
    order = lambda ns: [n for n in names if n in ns]
    winning = set(best); rounds = []; i = 0
    while True:
        before = {n for n, rank in best.items() if rank <= i}; after = {n for n, rank in best.items() if rank <= i+1}
        checks = []
        for s in states:
            ts = [m['to'] in before for m in s['moves']]
            qualified = (not all(not v for v in ts)) if s['owner'] == 'controller' else (not any(not v for v in ts))
            admitted = s['name'] in goals or s['safe'] and qualified
            if admitted != (s['name'] in after): raise ValueError('policy oracle disagrees with local reachability obligation')
            checks.append({'state': s['name'], 'operator': 'exists' if s['owner'] == 'controller' else 'all',
                           'safe': s['safe'], 'goal': s['name'] in goals, 'target_in_before': ts,
                           'qualified': qualified, 'admitted': admitted})
        rounds.append({'index': i, 'before': order(before), 'checks': checks, 'after': order(after), 'added': order(after-before)})
        if before == after: break
        i += 1
    records = []
    for s in states:
        n = s['name']; active = s['safe'] and n not in goals
        moves = []
        for m in s['moves']:
            optimum = active and s['owner'] == 'controller' and n in best and m['to'] in best and best[m['to']] == best[n]-1
            moves.append({**m, 'target_winning': m['to'] in best, 'target_rank': best.get(m['to']), 'optimal_controller_move': optimum})
        records.append({'name': n, 'owner': s['owner'], 'safe': s['safe'], 'goal': n in goals,
                        'winning': n in best, 'rank': best.get(n), 'moves': moves,
                        'controller_choice': next((m['action'] for m in moves if m['optimal_controller_move']), None),
                        'environment_choice': next((m['action'] for m in moves if active and s['owner'] == 'environment'
                                                    and n not in best and not m['target_winning']), None)})
    rb = {r['name']: r for r in records}; proofs = []
    for root in records:
        nodes = [root['name']]; edges = []
        for n in nodes:
            state = rb[n]
            if n in goals or not by[n]['safe']: continue
            fixed_owner = 'controller' if root['winning'] else 'environment'
            selected = state[fixed_owner+'_choice']
            for m in by[n]['moves']:
                if state['owner'] == fixed_owner and m['action'] != selected: continue
                if root['winning']:
                    if m['to'] not in best or best[m['to']] >= best[n]: raise ValueError('strategy rank fails to descend')
                elif m['to'] in best: raise ValueError('counterstrategy leaves goal-avoiding trap')
                edges.append({'from': n, **m})
                if m['to'] not in nodes: nodes.append(m['to'])
        proofs.append({'start': root['name'], 'kind': 'ranked_goal_strategy' if root['winning'] else 'goal_avoiding_counterstrategy',
                       'nodes': nodes, 'edges': edges, 'goals': [n for n in nodes if n in goals],
                       'unsafe': [n for n in nodes if not by[n]['safe']], 'rank_bound': root['rank']})
    summaries = [{'state': n,
                  'winning_policy_ids': [a['id'] for a in atlas if a['outcomes'][i]['winning']],
                  'optimal_policy_ids': [a['id'] for a in atlas if a['outcomes'][i]['winning'] and a['outcomes'][i]['worst_steps'] == best.get(n)]}
                 for i, n in enumerate(names)]
    uniform = [a['id'] for a in atlas if all(n not in best or
               (a['outcomes'][i]['winning'] and a['outcomes'][i]['worst_steps'] == best[n]) for i, n in enumerate(names))]
    if not uniform: raise ValueError('no uniform optimal positional policy')
    return {'schema': 'shieldlab-reachavoid-v1', 'input': data, 'rounds': rounds,
            'winning': order(winning), 'losing': order(set(names)-winning),
            'safe_until_goal': order(safe), 'safe_but_cannot_force_goal': order(safe-winning),
            'states': records, 'proof_graphs': proofs, 'policy_count': len(atlas), 'policy_atlas': atlas,
            'policy_summaries': summaries, 'uniform_optimal_policy_ids': uniform, 'limits': LIMITS[:]}


def verify_reachavoid(report):
    if not isinstance(report, dict) or 'input' not in report:
        raise ValueError('reach-avoid report requires input')
    expected = replay_reachavoid(report['input'])
    _equal(expected, report)
    return True

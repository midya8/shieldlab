"""Finite adversarial reach-before-unsafe games, with exact first-hit bounds.

Established attractor construction. No fairness, probabilities, continuous
control, recurrent goal, environment model learning or deployed shield claim.
"""
from itertools import product
from .reachavoid_input import validate_request, LIMITS




def _policy_outcome(by, goals, policy, root):
    def visit(n, nodes, path):
        if n in goals:
            return {'start': root, 'winning': True, 'worst_steps': len(path),
                    'witness': {'kind': 'longest_goal_path', 'path': path, 'cycle_start': None}}
        if not by[n]['safe']:
            return {'start': root, 'winning': False, 'worst_steps': None,
                    'witness': {'kind': 'unsafe_path', 'path': path, 'cycle_start': None}}
        if n in nodes:
            return {'start': root, 'winning': False, 'worst_steps': None,
                    'witness': {'kind': 'goal_avoiding_lasso', 'path': path, 'cycle_start': nodes.index(n)}}
        s = by[n]
        moves = [s['moves'][policy[n]]] if s['owner'] == 'controller' else s['moves']
        longest = None
        for m in moves:
            out = visit(m['to'], nodes + [n], path + [{'from': n, **m}])
            if not out['winning']:
                return out
            if longest is None or out['worst_steps'] > longest['worst_steps']:
                longest = out
        return longest
    return visit(root, [], [])


def analyze_reachavoid(request):
    request = validate_request(request)
    states = request['arena']['states']; names = [s['name'] for s in states]
    by = {s['name']: s for s in states}; goals = set(request['goals'])
    order = lambda ns: [n for n in names if n in ns]
    reached = set(goals); rank = {n: 0 for n in goals}; rounds = []
    while True:
        after = set(goals); checks = []
        for s in states:
            n = s['name']; ts = [m['to'] in reached for m in s['moves']]
            qualifies = any(ts) if s['owner'] == 'controller' else all(ts)
            admitted = n in goals or (s['safe'] and qualifies)
            if admitted: after.add(n)
            checks.append({'state': n, 'operator': 'exists' if s['owner'] == 'controller' else 'all',
                           'safe': s['safe'], 'goal': n in goals, 'target_in_before': ts,
                           'qualified': qualifies, 'admitted': admitted})
        added = after - reached
        rounds.append({'index': len(rounds), 'before': order(reached), 'checks': checks,
                       'after': order(after), 'added': order(added)})
        for n in added: rank[n] = len(rounds)
        if reached == after: break
        reached = after
    # Safety-until-goal uses absorbing success, not the original nonterminal
    # infinite safety objective, whose value can differ after reaching a goal.
    safe = {s['name'] for s in states if s['safe']}
    while True:
        nxt = goals | {s['name'] for s in states if s['safe'] and
                       (any(m['to'] in safe for m in s['moves']) if s['owner'] == 'controller'
                        else all(m['to'] in safe for m in s['moves']))}
        if nxt == safe: break
        safe = nxt
    records = []
    for s in states:
        n = s['name']; active = s['safe'] and n not in goals
        moves = [{**m, 'target_winning': m['to'] in reached, 'target_rank': rank.get(m['to']),
                  'optimal_controller_move': active and s['owner'] == 'controller' and n in reached
                    and m['to'] in rank and rank[m['to']] + 1 == rank[n]} for m in s['moves']]
        records.append({'name': n, 'owner': s['owner'], 'safe': s['safe'], 'goal': n in goals,
                        'winning': n in reached, 'rank': rank.get(n), 'moves': moves,
                        'controller_choice': next((m['action'] for m in moves if m['optimal_controller_move']), None),
                        'environment_choice': next((m['action'] for m in moves if active and s['owner'] == 'environment'
                                                    and n not in reached and not m['target_winning']), None)})
    rb = {r['name']: r for r in records}; proofs = []
    for root in records:
        queue = [root['name']]; seen = set(queue); edges = []
        for n in queue:
            s = rb[n]
            if s['goal'] or not s['safe']: continue
            controlled = 'controller' if root['winning'] else 'environment'
            for m in s['moves']:
                if s['owner'] == controlled and m['action'] != s[controlled + '_choice']: continue
                edges.append({'from': n, 'action': m['action'], 'to': m['to']})
                if m['to'] not in seen: seen.add(m['to']); queue.append(m['to'])
        proofs.append({'start': root['name'], 'kind': 'ranked_goal_strategy' if root['winning'] else 'goal_avoiding_counterstrategy',
                       'nodes': queue, 'edges': edges, 'goals': [n for n in queue if n in goals],
                       'unsafe': [n for n in queue if not by[n]['safe']], 'rank_bound': root['rank']})
    controlled = [s for s in states if s['safe'] and s['name'] not in goals and s['owner'] == 'controller']
    atlas = []
    for choices in product(*(range(len(s['moves'])) for s in controlled)):
        policy = {s['name']: i for s, i in zip(controlled, choices)}
        outcomes = [_policy_outcome(by, goals, policy, n) for n in names]
        atlas.append({'id': len(atlas), 'policy': [{'state': s['name'], 'action': s['moves'][i]['action']}
                                                 for s, i in zip(controlled, choices)], 'outcomes': outcomes})
    summaries = []
    for i, n in enumerate(names):
        winning_ids = [a['id'] for a in atlas if a['outcomes'][i]['winning']]
        optimal_ids = [a['id'] for a in atlas if a['outcomes'][i]['winning'] and a['outcomes'][i]['worst_steps'] == rank.get(n)]
        summaries.append({'state': n, 'winning_policy_ids': winning_ids, 'optimal_policy_ids': optimal_ids})
    uniform = [a['id'] for a in atlas if all(not r['winning'] or
               (a['outcomes'][i]['winning'] and a['outcomes'][i]['worst_steps'] == r['rank']) for i, r in enumerate(records))]
    return {'schema': 'shieldlab-reachavoid-v1', 'input': request, 'rounds': rounds,
            'winning': order(reached), 'losing': order(set(names) - reached),
            'safe_until_goal': order(safe), 'safe_but_cannot_force_goal': order(safe - reached),
            'states': records, 'proof_graphs': proofs, 'policy_count': len(atlas), 'policy_atlas': atlas,
            'policy_summaries': summaries, 'uniform_optimal_policy_ids': uniform, 'limits': LIMITS[:]}


if __name__ == '__main__':
    from .reachavoid_cli import main
    raise SystemExit(main())

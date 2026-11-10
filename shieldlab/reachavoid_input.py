"""Shared bounded request validation, with no solving or report generation."""
from .core import validate


def validate_request(data):
    if not isinstance(data, dict) or set(data) != {'arena', 'goals'}:
        raise ValueError('reach-avoid input must contain exactly arena and goals')
    arena = validate(data['arena'])
    goals = data['goals']
    names = [s['name'] for s in arena['states']]
    if not isinstance(goals, list) or any(type(n) is not str or n not in names for n in goals):
        raise ValueError('goals must be an array of declared state names')
    if len(goals) != len(set(goals)):
        raise ValueError('goals must be unique')
    if any(not s['safe'] and s['name'] in goals for s in arena['states']):
        raise ValueError('every goal must be safe; unsafe/goal overlap is rejected')
    return {'arena': arena, 'goals': [n for n in names if n in goals]}


LIMITS = [
    'Goal is terminal success on first hit; outgoing goal moves are ignored, not an obligation to remain safe afterward.',
    'All goals must be safe. Unsafe roots fail immediately. Empty goals make every root lose reach-avoid.',
    'A finite total turn-based perfect-information adversarial arena; no fairness assumption, probabilities or real-system guarantee.',
    'A move to a winning successor may still allow endless stalling under repeated permissive choices. Only the displayed optimal rank-decreasing controller choices enforce the stated bound.',
    'Policy counts describe complete deterministic positional assignments on safe non-goal controller states, including unreachable states; not distinct behaviors or all history-dependent strategies.',
    'One to six states and one to three moves per state; exhaustive policy evidence is deliberately bounded, not a scalable solver or new algorithm.'
]

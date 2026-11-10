"""Shared input validation only, no recurrence algorithm."""
from .core import validate

def validate_request(data):
    if type(data) is not dict or set(data) != {'arena', 'goals'}:
        raise ValueError('recurrence input must contain exactly arena and goals')
    arena = validate(data['arena'])
    goals = data['goals']
    names = [s['name'] for s in arena['states']]
    if type(goals) is not list or any(type(n) is not str or n not in names for n in goals):
        raise ValueError('goals must list declared names')
    if len(goals) != len(set(goals)):
        raise ValueError('goals must be unique')
    if any(not s['safe'] and s['name'] in goals for s in arena['states']):
        raise ValueError('goals must be safe')
    return {'arena': arena, 'goals': [n for n in names if n in goals]}

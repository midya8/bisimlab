"""Structural validation only; semantics are intentionally not shared."""
from .core import validate

def normalize(raw):
    if type(raw) is not dict or set(raw) != {'system', 'silent'}:
        raise ValueError('Expected exactly system and silent')
    system = validate(raw['system'])
    silent = raw['silent']
    if type(silent) is not list or any(type(a) is not str or a not in system['actions'] for a in silent) or len(set(silent)) != len(silent):
        raise ValueError('silent must be distinct declared labels')
    return {'system':system,'silent':[a for a in system['actions'] if a in silent]}

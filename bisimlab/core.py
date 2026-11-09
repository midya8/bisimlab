"""Bounded strong-bisimulation refinement with modal witness DAGs."""
import re
from collections import deque
from copy import deepcopy


def validate(data):
    if type(data) is not dict or set(data) != {'states', 'actions', 'edges'}:
        raise ValueError('Expected exactly states, actions, edges')
    for key, limit, minimum in [('states', 6, 1), ('actions', 3, 0)]:
        items = data[key]
        if type(items) is not list or not minimum <= len(items) <= limit:
            raise ValueError(f'{key}: length {minimum}..{limit}')
        if any(type(x) is not str or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,15}', x) for x in items) or len(set(items)) != len(items):
            raise ValueError(f'{key}: unique short ASCII identifiers required')
    edges = data['edges']
    if type(edges) is not list or len(edges) > 18:
        raise ValueError('edges: at most 18 triples')
    seen = set()
    for e in edges:
        if type(e) is not list or len(e) != 3 or any(type(x) is not str for x in e):
            raise ValueError('Each edge must be [source, action, target]')
        if e[0] not in data['states'] or e[2] not in data['states'] or e[1] not in data['actions'] or tuple(e) in seen:
            raise ValueError('Unknown edge name or duplicate edge')
        seen.add(tuple(e))
    return deepcopy(data)


def traces(data, p, q):
    """Exact finite-trace comparison by BFS on paired reachable subsets."""
    states, actions, edges = data['states'], data['actions'], data['edges']
    start = (1 << states.index(p), 1 << states.index(q))
    queue, seen = deque([(start, [])]), {start}
    while queue:
        (left, right), word = queue.popleft()
        if bool(left) != bool(right):
            return {'equivalent': False, 'word': word, 'explored': len(seen)}
        for a in actions:
            def step(mask):
                out = 0
                for s, label, t in edges:
                    if label == a and mask & (1 << states.index(s)):
                        out |= 1 << states.index(t)
                return out
            nxt = (step(left), step(right))
            if nxt not in seen:
                seen.add(nxt)
                queue.append((nxt, word + [a]))
    return {'equivalent': True, 'word': None, 'explored': len(seen)}


def analyze(data):
    d = validate(data)
    states, edges = d['states'], d['edges']
    pairs = [(p, q) for p in states for q in states]
    current = set(pairs)
    rounds = [{'index': 0, 'retained': [list(x) for x in pairs], 'removed': []}]
    nodes = [{'op': 'true'}]
    ids = {}
    depths = [0]
    def add(node, depth):
        i = len(nodes)
        nodes.append(node)
        depths.append(depth)
        return i
    while True:
        removed = []
        for p, q in pairs:
            if (p, q) not in current:
                continue
            attacks = []
            for side, source, other in [('left', p, q), ('right', q, p)]:
                for i, (s, a, t) in enumerate(edges):
                    if s != source:
                        continue
                    matches = [{'edge': j, 'pair': [t, u] if side == 'left' else [u, t],
                                'survives': ((t, u) if side == 'left' else (u, t)) in current}
                               for j, (v, b, u) in enumerate(edges) if v == other and b == a]
                    attacks.append({'side': side, 'edge': i, 'matches': matches,
                                    'fails': not any(m['survives'] for m in matches)})
            winning = next((a for a in attacks if a['fails']), None)
            if winning is not None:
                removed.append({'pair': [p, q], 'attacks': attacks, 'winning': attacks.index(winning)})
        # Build only from the previous relation's witnesses, not this round's removals.
        pending = {}
        for row in removed:
            p, q = row['pair']
            w = row['attacks'][row['winning']]
            _, action, t = edges[w['edge']]
            children = []
            for m in w['matches']:
                u, v = m['pair']
                child = ids[(u, v)] if w['side'] == 'left' else ids[(v, u)]
                children.append(child)
            inner = 0 if not children else add({'op': 'and', 'args': children}, max(depths[i] for i in children))
            diamond = add({'op': 'diamond', 'action': action, 'arg': inner}, depths[inner] + 1)
            root = diamond if w['side'] == 'left' else add({'op': 'not', 'arg': diamond}, depths[diamond])
            row['formula'] = root
            pending[(p, q)] = root
        current -= {tuple(r['pair']) for r in removed}
        rounds.append({'index': len(rounds), 'retained': [list(x) for x in pairs if x in current], 'removed': removed})
        ids.update(pending)
        if not removed:
            break
    classes = []
    for p in states:
        if not any(p in c for c in classes):
            classes.append([q for q in states if (p, q) in current])
    quotient = []
    for i, c in enumerate(classes):
        for a in d['actions']:
            for j, target in enumerate(classes):
                if any(s in c and b == a and t in target for s, b, t in edges):
                    quotient.append([i, a, j])
    truth = []
    for n in nodes:
        if n['op'] == 'true':
            value = set(states)
        elif n['op'] == 'not':
            value = set(states) - truth[n['arg']]
        elif n['op'] == 'and':
            value = set(states).intersection(*(truth[i] for i in n['args']))
        else:
            value = {s for s, a, t in edges if a == n['action'] and t in truth[n['arg']]}
        truth.append(value)
    formulas = [dict(n, depth=depths[i], holds=[s for s in states if s in truth[i]]) for i, n in enumerate(nodes)]
    results = []
    for p, q in pairs:
        rank = next((r['index'] for r in rounds if any(x['pair'] == [p, q] for x in r['removed'])), None)
        results.append({'pair': [p, q], 'bisimilar': (p, q) in current, 'rank': rank,
                        'formula': ids.get((p, q)), 'traces': traces(d, p, q)})
    return {'schema': 'bisimlab-v1', 'input': d, 'rounds': rounds, 'formulas': formulas,
            'pairs': results, 'classes': classes, 'quotient': quotient}

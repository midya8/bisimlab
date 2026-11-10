"""Exact bounded strong/weak/branching bisimulation, with finite path obligations."""
from collections import deque
from .core import validate


def analyze_silent(raw):
    if type(raw) is not dict or set(raw) != {'system', 'silent'}:
        raise ValueError('Expected exactly system and silent')
    system = validate(raw['system'])
    silent = raw['silent']
    if type(silent) is not list or any(type(a) is not str or a not in system['actions'] for a in silent) or len(set(silent)) != len(silent):
        raise ValueError('silent must be distinct declared action names')
    silent = [a for a in system['actions'] if a in silent]
    request = {'system': system, 'silent': silent}
    states, actions = system['states'], system['actions']
    n = len(states)
    edges = [(states.index(p), a, states.index(q)) for p, a, q in system['edges']]
    pairs = [(p, q) for p in range(n) for q in range(n)]
    paths = {}
    for start in range(n):
        reached, todo = {start: []}, deque([start])
        while todo:
            s = todo.popleft()
            for eid, (p, a, q) in enumerate(edges):
                if p == s and a in silent and q not in reached:
                    reached[q] = reached[s] + [eid]
                    todo.append(q)
        paths[start] = reached
    closure = [{'source': p, 'targets': [{'target': q, 'path': paths[p][q]} for q in range(n) if q in paths[p]]} for p in range(n)]
    cycles = []
    for p in range(n):
        options = [([eid] + paths[q][p]) for eid, (s, a, q) in enumerate(edges) if s == p and a in silent and p in paths[q]]
        if options:
            cycles.append({'state': p, 'path': min(options, key=lambda x: (len(x), x))})
    divergence = []
    for p in range(n):
        possible = [{'cycle_state': c['state'], 'prefix': paths[p][c['state']], 'cycle': c['path']} for c in cycles if c['state'] in paths[p]]
        witness = min(possible, key=lambda c: (len(c['prefix']) + len(c['cycle']), c['prefix'], c['cycle'])) if possible else None
        divergence.append({'state': p, 'divergent': witness is not None, 'witness': witness})

    def choices(source, other, eid, mode):
        _, action, target = edges[eid]
        result = []
        def add(prefix, central, suffix, end, requirements, kind):
            result.append({'kind': kind, 'prefix': prefix, 'edge': central, 'suffix': suffix,
                           'end': end, 'requirements': [list(x) for x in requirements]})
        if mode == 'strong':
            for j, (s, a, t) in enumerate(edges):
                if s == other and a == action:
                    add([], j, [], t, [(target, t)], 'direct')
        elif mode == 'weak' and action in silent:
            for end in range(n):
                if end in paths[other]:
                    add(paths[other][end], None, [], end, [(target, end)], 'silent-closure')
        else:
            if mode == 'branching' and action in silent:
                add([], None, [], other, [(target, other)], 'stutter')
            for middle in range(n):
                if middle not in paths[other]:
                    continue
                for j, (s, a, t) in enumerate(edges):
                    if s != middle or not (a == action or (mode == 'branching' and a in silent and action in silent)):
                        continue
                    if mode == 'branching':
                        add(paths[other][middle], j, [], t, [(source, middle), (target, t)], 'branch-preserving')
                    else:
                        for end in range(n):
                            if end in paths[t]:
                                add(paths[other][middle], j, paths[t][end], end, [(target, end)], 'weak-visible')
        return result

    families = []
    for mode in ['strong', 'branching', 'weak']:
        relation = set(pairs)
        rounds = [{'index': 0, 'retained': [list(x) for x in pairs], 'removed': []}]
        while True:
            removed = []
            for p, q in pairs:
                if (p, q) not in relation:
                    continue
                attacks = []
                for side, source, other in [('left', p, q), ('right', q, p)]:
                    for eid, (s, _, _) in enumerate(edges):
                        if s != source:
                            continue
                        candidates = choices(source, other, eid, mode)
                        for c in candidates:
                            c['previous_membership'] = [tuple(x) in relation for x in c['requirements']]
                            c['survives'] = all(c['previous_membership'])
                        attacks.append({'side': side, 'edge': eid, 'responses': candidates,
                                        'fails': not any(c['survives'] for c in candidates)})
                winning = next((i for i, a in enumerate(attacks) if a['fails']), None)
                if winning is not None:
                    removed.append({'pair': [p, q], 'attacks': attacks, 'winning': winning})
            relation -= {tuple(r['pair']) for r in removed}
            rounds.append({'index': len(rounds), 'retained': [list(x) for x in pairs if x in relation], 'removed': removed})
            if not removed:
                break
        classes, pending = [], set(range(n))
        while pending:
            p = min(pending)
            group = [q for q in range(n) if (p, q) in relation]
            classes.append(group)
            pending -= set(group)
        families.append({'semantics': mode, 'rounds': rounds, 'relation': [list(x) for x in pairs if x in relation], 'classes': classes})
    strong, branching, weak = [set(map(tuple, f['relation'])) for f in families]
    return {'schema': 'bisimlab-silent-v1', 'input': request, 'silent_closure': closure,
            'silent_cycles': cycles, 'divergence': divergence, 'families': families,
            'branching_not_strong': [list(x) for x in pairs if x in branching - strong],
            'weak_not_branching': [list(x) for x in pairs if x in weak - branching],
            'checks': {'strong_subset_branching': strong <= branching,
                       'branching_subset_weak': branching <= weak,
                       'all_equivalence_relations': all(all((q, p) in r for p, q in r) and all((p, p) in r for p in range(n)) and all((p, t) in r for p, q in r for s, t in r if q == s) for r in [strong, branching, weak])}}


def main(argv=None):
    """Strict JSON silent-action generation/checking with atomic output replacement."""
    import argparse
    import json
    import os
    from pathlib import Path
    import sys
    import tempfile
    from .silent_verify import verify_silent
    parser = argparse.ArgumentParser(description='Exact finite silent-action-recursive argumentation evidence')
    parser.add_argument('input', help='UTF-8 JSON path or - for stdin')
    parser.add_argument('--verify', action='store_true', help='independently check an exported silent-action report')
    parser.add_argument('-o', '--output')
    args = parser.parse_args(argv)
    limit = 4 * 1024 * 1024 if args.verify else 65536
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate JSON key')
            result[key] = value
        return result
    try:
        raw = sys.stdin.buffer.read(limit + 1) if args.input == '-' else Path(args.input).read_bytes()
        if len(raw) > limit:
            raise ValueError('input exceeds mode UTF-8 byte limit')
        data = json.loads(raw.decode('utf-8'), object_pairs_hook=unique,
                          parse_constant=lambda x: (_ for _ in ()).throw(ValueError('nonfinite JSON constant')))
        if args.verify:
            verify_silent(data)
            result = {'valid': True, 'schema': 'bisimlab-silent-v1'}
        else:
            result = analyze_silent(data)
        text = json.dumps(result, indent=2, allow_nan=False) + '\n'
        if args.output:
            target = Path(args.output)
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=target.parent, delete=False) as f:
                temporary = f.name
                try:
                    f.write(text)
                except BaseException:
                    os.unlink(temporary)
                    raise
            try:
                os.replace(temporary, target)
            except BaseException:
                os.unlink(temporary)
                raise
        else:
            sys.stdout.write(text)
    except (ValueError, OSError, UnicodeError, RecursionError) as error:
        parser.exit(2, 'Invalid input: ' + str(error) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

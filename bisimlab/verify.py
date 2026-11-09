"""Independent partition-signature replay and modal semantics. No analyzer import."""
from itertools import product
from collections import deque
from .core import validate


def verify(report):
    try:
        _verify(report)
        return True
    except (ValueError, TypeError, KeyError, IndexError, AssertionError, RecursionError):
        return False


def _verify(r):
    def exact(a, b):
        if type(a) is not type(b):
            raise ValueError('Type mismatch')
        if type(b) is dict:
            assert a.keys() == b.keys()
            for k in b: exact(a[k], b[k])
        elif type(b) is list:
            assert len(a) == len(b)
            for x, y in zip(a, b): exact(x, y)
        else: assert a == b
    assert type(r) is dict and set(r) == {'schema','input','rounds','formulas','pairs','classes','quotient'}
    exact(r['schema'], 'bisimlab-v1')
    d = validate(r['input'])
    states, actions, edges = d['states'], d['actions'], d['edges']
    pairs = list(product(states, repeat=2))
    blocks = [list(states)]
    relations = [set(pairs)]
    while True:
        def signature(s):
            return tuple(frozenset(i for i, group in enumerate(blocks) if any(x == s and b == a and y in group for x,b,y in edges)) for a in actions)
        sigs = {s: signature(s) for s in states}
        rel = {(p,q) for p,q in pairs if sigs[p] == sigs[q]}
        relations.append(rel)
        if rel == relations[-2]: break
        blocks = []
        for p in states:
            if not any(p in b for b in blocks): blocks.append([q for q in states if (p,q) in rel])
    assert len(r['rounds']) == len(relations)
    roots = {}
    # Full attack/match records, deterministic first failed attack, strict canonical indices.
    node_specs = [{'op':'true'}]
    depth = [0]
    def add(spec, dep):
        node_specs.append(spec); depth.append(dep); return len(node_specs)-1
    for k, rel in enumerate(relations):
        removed = []
        if k:
            for p,q in pairs:
                if (p,q) not in relations[k-1] - rel: continue
                attacks = []
                for side, src, other in [('left',p,q),('right',q,p)]:
                    for i, (s,a,t) in enumerate(edges):
                        if s != src: continue
                        matches = []
                        for j,(v,b,u) in enumerate(edges):
                            if v == other and b == a:
                                pair = (t,u) if side == 'left' else (u,t)
                                matches.append({'edge':j,'pair':list(pair),'survives':pair in relations[k-1]})
                        attacks.append({'side':side,'edge':i,'matches':matches,'fails':all(not m['survives'] for m in matches)})
                win = next(i for i,a in enumerate(attacks) if a['fails'])
                attack = attacks[win]
                args = [roots[tuple(m['pair']) if attack['side']=='left' else tuple(reversed(m['pair']))] for m in attack['matches']]
                inner = add({'op':'and','args':args}, max(depth[i] for i in args)) if args else 0
                diamond = add({'op':'diamond','action':edges[attack['edge']][1],'arg':inner},depth[inner]+1)
                root = diamond if attack['side']=='left' else add({'op':'not','arg':diamond},depth[diamond])
                removed.append({'pair':[p,q],'attacks':attacks,'winning':win,'formula':root})
            roots.update({tuple(a['pair']):a['formula'] for a in removed})
        exact(r['rounds'][k], {'index':k,'retained':[list(x) for x in pairs if x in rel],'removed':removed})
    values = []
    for i,node in enumerate(node_specs):
        vals = []
        for s in states:
            if node['op']=='true': yes=True
            elif node['op']=='not': yes=s not in values[node['arg']]
            elif node['op']=='and': yes=all(s in values[j] for j in node['args'])
            else: yes=any(x==s and a==node['action'] and t in values[node['arg']] for x,a,t in edges)
            if yes: vals.append(s)
        values.append(vals)
        exact(r['formulas'][i],dict(node,depth=depth[i],holds=vals))
    assert len(r['formulas'])==len(node_specs)
    expected=[]
    for p,q in pairs:
        rank=next((i for i,rel in enumerate(relations) if (p,q) not in rel),None)
        root=roots.get((p,q))
        if root is not None:
            assert p in values[root] and q not in values[root] and depth[root]==rank
        # Independent trace comparison: frozensets rather than bitmasks.
        start=(frozenset([p]),frozenset([q])); todo=deque([(start,[])]);seen={start}; word=None
        while todo:
            (x,y),w=todo.popleft()
            if bool(x)!=bool(y): word=w;break
            for a in actions:
                nxt=tuple(frozenset(t for s,b,t in edges if s in group and b==a) for group in (x,y))
                if nxt not in seen: seen.add(nxt);todo.append((nxt,w+[a]))
        expected.append({'pair':[p,q],'bisimilar':rank is None,'rank':rank,'formula':root,
                         'traces':{'equivalent':word is None,'word':word,'explored':len(seen)}})
    exact(r['pairs'],expected)
    classes=[]
    for p in states:
        if not any(p in b for b in classes): classes.append([q for q in states if (p,q) in relations[-1]])
    exact(r['classes'],classes)
    quotient=[[i,a,j] for i,b in enumerate(classes) for a in actions for j,c in enumerate(classes) if any(s in b and lab==a and t in c for s,lab,t in edges)]
    exact(r['quotient'],quotient)

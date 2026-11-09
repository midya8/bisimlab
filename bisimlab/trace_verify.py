"""Independent explicit-subset transition table and canonical graph replay."""
from itertools import combinations
from .trace_audit import validate_trace


def verify_traces(report):
    try:
        _verify(report);return True
    except (ValueError,TypeError,KeyError,IndexError,AssertionError,RecursionError):return False


def _verify(r):
    def exact(a,b):
        assert type(a) is type(b)
        if type(b) is dict:
            assert a.keys()==b.keys()
            for k in b:exact(a[k],b[k])
        elif type(b) is list:
            assert len(a)==len(b)
            for x,y in zip(a,b):exact(x,y)
        else:assert a==b
    assert type(r) is dict and set(r)=={'schema','input','nodes','layers','mismatches','equivalent','first_mismatch','path','word'}
    exact(r['schema'],'bisimlab-traces-v1')
    d=validate_trace(r['input']);s=d['system']['states'];actions=d['system']['actions'];edges=d['system']['edges']
    subsets=[frozenset(c) for k in range(len(s)+1) for c in combinations(s,k)]
    table={(group,a):frozenset(q for p,b,q in edges if p in group and b==a) for group in subsets for a in actions}
    reachable=[tuple(frozenset([p]) for p in d['pair'])];lookup={reachable[0]:0};parent=[None];via=[None];depth=[0]
    rows=[]
    for i,(x,y) in enumerate(reachable):
        successors=[]
        for a in actions:
            nxt=(table[x,a],table[y,a])
            if nxt not in lookup:
                lookup[nxt]=len(reachable);reachable.append(nxt);parent.append(i);via.append(a);depth.append(depth[i]+1)
            successors.append(lookup[nxt])
        rows.append({'id':i,'left':[p for p in s if p in x],'right':[p for p in s if p in y],
                     'parent':parent[i],'via':via[i],'depth':depth[i],'mismatch':bool(x)!=bool(y),'next':successors})
    exact(r['nodes'],rows)
    exact(r['layers'],[[i for i,v in enumerate(depth) if v==k] for k in range(max(depth)+1)])
    bad=[i for i,(x,y) in enumerate(reachable) if bool(x)!=bool(y)]
    exact(r['mismatches'],bad);exact(r['equivalent'],not bad);exact(r['first_mismatch'],bad[0] if bad else None)
    path=[];word=None
    if bad:
        i=bad[0]
        while i is not None:path.insert(0,i);i=parent[i]
        word=[via[i] for i in path[1:]]
        assert len(word)==min(depth[i] for i in bad)
        # Independently follow the witness word through the precomputed table.
        left,right=reachable[0]
        for a in word:left,right=table[left,a],table[right,a]
        assert bool(left)!=bool(right)
    exact(r['path'],path);exact(r['word'],word)

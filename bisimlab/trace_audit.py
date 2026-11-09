"""Complete single-pair reachable-subset product, with canonical BFS provenance."""
from .core import validate


def validate_trace(data):
    if type(data) is not dict or set(data) != {'system','pair'}:
        raise ValueError('Expected exactly system and pair')
    system=validate(data['system']);pair=data['pair']
    if type(pair) is not list or len(pair)!=2 or any(type(s) is not str or s not in system['states'] for s in pair):
        raise ValueError('pair: two declared state names')
    return {'system':system,'pair':list(pair)}


def audit_traces(data):
    d=validate_trace(data);s=d['system']['states'];actions=d['system']['actions'];edges=d['system']['edges']
    start=tuple(1<<s.index(p) for p in d['pair']);queue=[start];ids={start:0};parents=[None];vias=[None];depths=[0];nodes=[]
    def step(mask,a):
        out=0
        for p,b,q in edges:
            if b==a and mask&(1<<s.index(p)):out|=1<<s.index(q)
        return out
    for i,(left,right) in enumerate(queue):
        targets=[]
        for a in actions:
            target=(step(left,a),step(right,a))
            if target not in ids:
                ids[target]=len(queue);queue.append(target);parents.append(i);vias.append(a);depths.append(depths[i]+1)
            targets.append(ids[target])
        nodes.append({'id':i,'left':[p for j,p in enumerate(s) if left>>j&1],
                      'right':[p for j,p in enumerate(s) if right>>j&1],
                      'parent':parents[i],'via':vias[i],'depth':depths[i],
                      'mismatch':bool(left)!=bool(right),'next':targets})
    mismatches=[n['id'] for n in nodes if n['mismatch']];first=mismatches[0] if mismatches else None
    path=[];word=None
    if first is not None:
        p=first
        while p is not None:path.append(p);p=parents[p]
        path.reverse();word=[vias[i] for i in path[1:]]
    layers=[[n['id'] for n in nodes if n['depth']==depth] for depth in range(max(depths)+1)]
    return {'schema':'bisimlab-traces-v1','input':d,'nodes':nodes,'layers':layers,
            'mismatches':mismatches,'equivalent':not mismatches,'first_mismatch':first,
            'path':path,'word':word}

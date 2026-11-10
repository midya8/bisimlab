"""Independent set/path reconstruction. Never imports or calls silent generator."""
import itertools
import json
from .core import validate


def verify_silent(report):
    if type(report) is not dict or type(report.get('input')) is not dict or set(report['input']) != {'system','silent'}:
        raise ValueError('Expected silent-action report')
    data=report['input'];system=validate(data['system']);names=system['states'];n=len(names);hidden=data['silent']
    if type(hidden) is not list or any(type(a) is not str or a not in system['actions'] for a in hidden) or len(set(hidden))!=len(hidden):
        raise ValueError('Invalid silent labels')
    hidden=[a for a in system['actions'] if a in hidden]
    arcs=[(names.index(s),a,names.index(t)) for s,a,t in system['edges']]
    # Enumerate simple silent paths, then minimize length and edge-id tuple.
    # A reachable endpoint always has a simple path. Nonempty cycles may repeat only the root.
    reachable={};cycles=[]
    for root in range(n):
        candidates={root:[()]};loops=[]
        def walk(s,visited,path):
            for eid,(source,action,target) in enumerate(arcs):
                if source!=s or action not in hidden:continue
                extended=path+(eid,)
                if target==root:loops.append(extended)
                if target not in visited:
                    candidates.setdefault(target,[]).append(extended)
                    walk(target,visited|{target},extended)
        walk(root,{root},())
        reachable[root]={t:list(min(ps,key=lambda p:(len(p),p))) for t,ps in candidates.items()}
        if loops:cycles.append({'state':root,'path':list(min(loops,key=lambda p:(len(p),p)))})
    closure=[{'source':s,'targets':[{'target':t,'path':reachable[s][t]} for t in sorted(reachable[s])]} for s in range(n)]
    divergence=[]
    for s in range(n):
        options=[{'cycle_state':c['state'],'prefix':reachable[s][c['state']],'cycle':c['path']} for c in cycles if c['state'] in reachable[s]]
        best=min(options,key=lambda c:(len(c['prefix'])+len(c['cycle']),c['prefix'],c['cycle'])) if options else None
        divergence.append({'state':s,'divergent':best is not None,'witness':best})
    pairs=list(itertools.product(range(n),repeat=2));families=[]
    for mode in ['strong','branching','weak']:
        rel=set(pairs);rounds=[{'index':0,'retained':[list(p) for p in pairs],'removed':[]}]
        while True:
            rejections=[]
            for left,right in pairs:
                if (left,right) not in rel:continue
                attacks=[]
                for side,attacker,responder in [('left',left,right),('right',right,left)]:
                    for edge,(s,label,t) in enumerate(arcs):
                        if s!=attacker:continue
                        responses=[]
                        def append(kind,prefix,central,suffix,end,requirements):
                            statuses=[pair in rel for pair in requirements]
                            responses.append({'kind':kind,'prefix':list(prefix),'edge':central,'suffix':list(suffix),'end':end,'requirements':[list(p) for p in requirements],'previous_membership':statuses,'survives':all(statuses)})
                        if mode=='strong':
                            for eid,(q,action,u) in enumerate(arcs):
                                if q==responder and action==label:append('direct',[],eid,[],u,[(t,u)])
                        elif mode=='weak' and label in hidden:
                            for u in sorted(reachable[responder]):append('silent-closure',reachable[responder][u],None,[],u,[(t,u)])
                        else:
                            if mode=='branching' and label in hidden:append('stutter',[],None,[],responder,[(t,responder)])
                            for v in sorted(reachable[responder]):
                                for eid,(q,action,u) in enumerate(arcs):
                                    matches=action==label or (mode=='branching' and label in hidden and action in hidden)
                                    if q!=v or not matches:continue
                                    if mode=='branching':append('branch-preserving',reachable[responder][v],eid,[],u,[(attacker,v),(t,u)])
                                    else:
                                        for end in sorted(reachable[u]):append('weak-visible',reachable[responder][v],eid,reachable[u][end],end,[(t,end)])
                        attacks.append({'side':side,'edge':edge,'responses':responses,'fails':all(not r['survives'] for r in responses)})
                failures=[i for i,a in enumerate(attacks) if a['fails']]
                if failures:rejections.append({'pair':[left,right],'attacks':attacks,'winning':failures[0]})
            rel=rel-{tuple(r['pair']) for r in rejections}
            rounds.append({'index':len(rounds),'retained':[list(p) for p in pairs if p in rel],'removed':rejections})
            if not rejections:break
        groups=[]
        for s in range(n):
            if any(s in g for g in groups):continue
            groups.append([t for t in range(n) if (s,t) in rel])
        families.append({'semantics':mode,'rounds':rounds,'relation':[list(p) for p in pairs if p in rel],'classes':groups})
    a,b,c=[set(map(tuple,f['relation'])) for f in families]
    equivalence=all(all((s,s) in rel for s in range(n)) and all((t,s) in rel for s,t in rel) and all((s,u) in rel for s,t in rel for v,u in rel if t==v) for rel in [a,b,c])
    expected={'schema':'bisimlab-silent-v1','input':{'system':system,'silent':hidden},'silent_closure':closure,'silent_cycles':cycles,'divergence':divergence,'families':families,'branching_not_strong':[list(p) for p in pairs if p in b-a],'weak_not_branching':[list(p) for p in pairs if p in c-b],'checks':{'strong_subset_branching':a<=b,'branching_subset_weak':b<=c,'all_equivalence_relations':equivalence}}
    encode=lambda v:json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)
    if encode(expected)!=encode(report):raise ValueError('Silent-action evidence differs from independent reconstruction')
    return True

"""Independent exhaustive simple-path/partition replay. No generator imports."""
from .divergence_input import normalize


def rebuild(raw):
    request=normalize(raw);d=request['system'];names=d['states'];n=len(names);hidden=request['silent']
    edges=[(names.index(s),a,names.index(t)) for s,a,t in d['edges']]
    blocks=[[]]
    for s in range(n):
        options=[]
        for partition in blocks:
            for j in range(len(partition)+1):
                q=[list(b) for b in partition]
                if j==len(q):q.append([s])
                else:q[j].append(s)
                options.append(q)
        blocks=options
    labelings=[]
    for partition in blocks:
        labelings.append([next(i for i,b in enumerate(partition) if s in b) for s in range(n)])
    candidates=[]
    for labels in sorted(labelings):
        rows=[]
        for s in range(n):
            allpaths=[]
            def visit(p,seen,path):
                allpaths.append((p,path))
                for i,(u,a,v) in enumerate(edges):
                    if u==p and a in hidden and labels[v]==labels[s]:
                        if v not in seen:visit(v,seen|{v},path+[i])
            visit(s,{s},[])
            reached={q:min((path for p,path in allpaths if p==q),key=lambda p:(len(p),p)) for q in sorted(set(p for p,_ in allpaths))}
            exits=[]
            visible=[a for a in d['actions'] if a not in hidden or a==hidden[0]]
            for a in visible:
                for b in range(max(labels)+1):
                    if a in hidden and b==labels[s]:continue
                    ways=[path+[i] for p,path in allpaths for i,(u,c,v) in enumerate(edges) if u==p and labels[v]==b and (c==a or (c in hidden and a in hidden))]
                    if ways:
                        best=min(ways,key=lambda p:(len(p),p));exits.append({'action':None if a in hidden else a,'block':b,'path':best,'edge':best[-1]})
            choices=[]
            for p,prefix in reached.items():
                loops=[]
                def cycle(u,seen,path):
                    for i,(v,a,w) in enumerate(edges):
                        if v!=u or a not in hidden or labels[w]!=labels[s]:continue
                        if w==p:loops.append(path+[i])
                        elif w not in seen:cycle(w,seen|{w},path+[i])
                cycle(p,{p},[])
                if loops:choices.append({'at':p,'prefix':prefix,'cycle':min(loops,key=lambda x:(len(x),x))})
            witness=min(choices,key=lambda x:(len(x['prefix'])+len(x['cycle']),x['prefix'],x['cycle'])) if choices else None
            rows.append({'state':s,'block':labels[s],'inert':[{'target':q,'path':path} for q,path in reached.items()],'exits':exits,'divergent':bool(choices),'witness':witness})
        failures=[]
        for p in range(n):
            for q in range(p+1,n):
                if labels[p]!=labels[q]:continue
                if [(x['action'],x['block']) for x in rows[p]['exits']]!=[(x['action'],x['block']) for x in rows[q]['exits']]:failures.append({'pair':[p,q],'kind':'exit','left':rows[p]['exits'],'right':rows[q]['exits']})
                if rows[p]['divergent']!=rows[q]['divergent']:failures.append({'pair':[p,q],'kind':'divergence','left':rows[p]['witness'],'right':rows[q]['witness']})
        candidates.append({'index':len(candidates),'labels':labels,'states':rows,'branching':not any(f['kind']=='exit' for f in failures),'preserving':not failures,'failures':failures})
    families=[]
    for mode in ['branching','preserving']:
        valid=[c for c in candidates if c[mode]]
        union={(p,q) for c in valid for p in range(n) for q in range(n) if c['labels'][p]==c['labels'][q]}
        winners=[c for c in valid if {(p,q) for p in range(n) for q in range(n) if c['labels'][p]==c['labels'][q]}==union]
        if len(winners)!=1:raise ValueError('No unique coarsest valid partition')
        win=winners[0]
        families.append({'semantics':mode,'accepted':[c['index'] for c in valid],'coarsest':win['index'],'relation':[list(x) for x in sorted(union)],'classes':[[p for p in range(n) if win['labels'][p]==b] for b in range(max(win['labels'])+1)]})
    old,new=[set(map(tuple,f['relation'])) for f in families]
    if not new<=old:raise ValueError('Subset condition fails')
    return {'schema':'bisimlab-divergence-v1','input':request,'candidates':candidates,'families':families,'lost_pairs':[list(p) for p in sorted(old-new)],'checks':{'preserving_subset_branching':True,'coarsest_contains_all_accepted':True},'counts':{'partitions':len(candidates),'state_records':sum(len(c['states']) for c in candidates),'failures':sum(len(c['failures']) for c in candidates)}}


def verify_divergence(report):
    if type(report) is not dict or 'input' not in report:raise ValueError('Expected report object')
    expected=rebuild(report['input'])
    # Object key order is not semantic JSON; preserve arrays and canonical field values, not insertion order.
    def keyorder(a,b):
        if type(a) is not type(b):return False
        if isinstance(a,dict):return set(a)==set(b) and all(keyorder(a[k],b[k]) for k in a)
        if isinstance(a,list):return len(a)==len(b) and all(keyorder(x,y) for x,y in zip(a,b))
        return a==b
    if not keyorder(report,expected):raise ValueError('Invalid divergence atlas')
    return True

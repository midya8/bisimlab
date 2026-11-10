"""Complete bounded partition atlas for branching equivalence with explicit divergence."""
from collections import deque
from .divergence_input import normalize


def partitions(n):
    def walk(prefix):
        if len(prefix)==n:
            yield prefix
        else:
            for k in range(max(prefix,default=-1)+2):
                yield from walk(prefix+[k])
    yield from walk([])


def analyze_divergence(raw):
    request=normalize(raw);d=request['system'];n=len(d['states']);hidden=request['silent']
    edges=[(d['states'].index(s),a,d['states'].index(t)) for s,a,t in d['edges']]
    candidates=[]
    for labels in partitions(n):
        rows=[]
        for s in range(n):
            reached={s:[]};todo=deque([s])
            while todo:
                p=todo.popleft()
                for i,(u,a,v) in enumerate(edges):
                    if u==p and a in hidden and labels[u]==labels[v] and v not in reached:
                        reached[v]=reached[u]+[i];todo.append(v)
            exits=[]
            for ai,a in enumerate(d['actions']):
                if a in hidden and a!=hidden[0]:continue
                for target in range(max(labels)+1):
                    if a in hidden and target==labels[s]:continue
                    options=[]
                    for p,path in reached.items():
                        for i,(u,b,v) in enumerate(edges):
                            if u==p and labels[v]==target and (b==a or (b in hidden and a in hidden)):
                                options.append((path+[i],i))
                    if options:
                        path,eid=min(options,key=lambda x:(len(x[0]),x[0]))
                        exits.append({'action':None if a in hidden else a,'block':target,'path':path,'edge':eid})
            cycles=[]
            for p,prefix in reached.items():
                # BFS within this block, returning to p by a nonempty path.
                q=deque([(p,[])]);seen={p};found=None
                while q and found is None:
                    u,path=q.popleft()
                    for i,(v,a,w) in enumerate(edges):
                        if v!=u or a not in hidden or labels[w]!=labels[s]:continue
                        if w==p:found=path+[i];break
                        if w not in seen:seen.add(w);q.append((w,path+[i]))
                if found is not None:cycles.append({'at':p,'prefix':prefix,'cycle':found})
            witness=min(cycles,key=lambda x:(len(x['prefix'])+len(x['cycle']),x['prefix'],x['cycle'])) if cycles else None
            rows.append({'state':s,'block':labels[s],'inert':[{'target':p,'path':reached[p]} for p in sorted(reached)],'exits':exits,'divergent':witness is not None,'witness':witness})
        failures=[]
        for p in range(n):
            for q in range(p+1,n):
                if labels[p]!=labels[q]:continue
                left=[(x['action'],x['block']) for x in rows[p]['exits']];right=[(x['action'],x['block']) for x in rows[q]['exits']]
                if left!=right:failures.append({'pair':[p,q],'kind':'exit','left':rows[p]['exits'],'right':rows[q]['exits']})
                if rows[p]['divergent']!=rows[q]['divergent']:failures.append({'pair':[p,q],'kind':'divergence','left':rows[p]['witness'],'right':rows[q]['witness']})
        candidates.append({'index':len(candidates),'labels':labels,'states':rows,'branching':not any(f['kind']=='exit' for f in failures),'preserving':not failures,'failures':failures})
    families=[]
    for mode in ['branching','preserving']:
        accepted=[c for c in candidates if c[mode]]
        winner=max(accepted,key=lambda c:sum(x==y for x in c['labels'] for y in c['labels']))
        relation=[[p,q] for p in range(n) for q in range(n) if winner['labels'][p]==winner['labels'][q]]
        # The known equivalence theorem supplies existence; inspect this finite atlas explicitly too.
        assert all(all(winner['labels'][p]==winner['labels'][q] for p in range(n) for q in range(n) if c['labels'][p]==c['labels'][q]) for c in accepted)
        families.append({'semantics':mode,'accepted':[c['index'] for c in accepted],'coarsest':winner['index'],'relation':relation,'classes':[[p for p in range(n) if winner['labels'][p]==b] for b in range(max(winner['labels'])+1)]})
    old,new=[set(map(tuple,f['relation'])) for f in families]
    assert new<=old
    return {'schema':'bisimlab-divergence-v1','input':request,'candidates':candidates,'families':families,'lost_pairs':[list(p) for p in sorted(old-new)],'checks':{'preserving_subset_branching':True,'coarsest_contains_all_accepted':True},'counts':{'partitions':len(candidates),'state_records':sum(len(c['states']) for c in candidates),'failures':sum(len(c['failures']) for c in candidates)}}


def main(argv=None):
    import argparse,json,os,sys,tempfile
    from pathlib import Path
    from .divergence_verify import verify_divergence
    p=argparse.ArgumentParser(description='Complete finite explicit-divergence partition atlas')
    p.add_argument('input');p.add_argument('--verify',action='store_true');p.add_argument('-o','--output');a=p.parse_args(argv)
    def unique(items):
        d={}
        for k,v in items:
            if k in d:raise ValueError('duplicate JSON key')
            d[k]=v
        return d
    try:
        limit=8*1024*1024 if a.verify else 65536
        data=sys.stdin.buffer.read(limit+1) if a.input=='-' else Path(a.input).read_bytes()
        if len(data)>limit:raise ValueError('input exceeds UTF-8 byte limit')
        raw=json.loads(data.decode(),object_pairs_hook=unique,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('nonfinite constant')))
        if a.verify:verify_divergence(raw);result={'valid':True,'schema':'bisimlab-divergence-v1'}
        else:result=analyze_divergence(raw)
        text=json.dumps(result,indent=2,allow_nan=False)+'\n'
        if a.output:
            target=Path(a.output)
            with tempfile.NamedTemporaryFile(mode='w',encoding='utf8',dir=target.parent,delete=False) as f:
                name=f.name
                try:f.write(text)
                except BaseException:os.unlink(name);raise
            try:os.replace(name,target)
            except BaseException:os.unlink(name);raise
        else:sys.stdout.write(text)
    except (ValueError,OSError,UnicodeError,RecursionError) as error:p.exit(2,'Invalid input: '+str(error)+'\n')
    return 0

if __name__=='__main__':raise SystemExit(main())

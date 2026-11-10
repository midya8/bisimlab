"""Optional actual external reference, final relations only; no vendored reference code."""
import argparse,itertools,json,random,subprocess,tempfile
from pathlib import Path
from bisimlab.divergence import analyze_divergence

def cases():
    for n in [1,2]:
        states=['s'+str(i) for i in range(n)];options=list(itertools.product(states,['inside','a'],states))
        for mask in range(1<<len(options)):
            yield {'system':{'states':states,'actions':['inside','a'],'edges':[list(e) for i,e in enumerate(options) if mask>>i&1]},'silent':['inside']}
    rng=random.Random(47129)
    for _ in range(80):
        n=rng.randrange(3,7);ss=['s'+str(i) for i in range(n)];aa=['hiddenA','hiddenB','tau'];edges=[list(e) for e in itertools.product(ss,aa,ss) if rng.random()<.17];rng.shuffle(edges)
        yield {'system':{'states':ss,'actions':aa,'edges':edges[:18]},'silent':rng.choice([[],['hiddenA'],['hiddenA','hiddenB']])}
    yield from (c['input'] for c in json.loads((Path(__file__).resolve().parents[1]/'docs/divergence-controls.json').read_text()))

def main():
    p=argparse.ArgumentParser();p.add_argument('--ltscompare',required=True);a=p.parse_args();count=0;total=0
    version=subprocess.check_output([a.ltscompare,'--version'],text=True).splitlines()[0]
    with tempfile.TemporaryDirectory() as tmp:
        for data in cases():
            total+=1;r=analyze_divergence(data);d=data['system'];ss=d['states'];labels={x:'act'+str(i) for i,x in enumerate(d['actions'])}
            edges='\n'.join('(%d,"%s",%d)'%(ss.index(s),labels[b],ss.index(t)) for s,b,t in d['edges'])
            for i in range(len(ss)):Path(tmp,str(i)+'.aut').write_text('des (%d,%d,%d)\n%s\n'%(i,len(d['edges']),len(ss),edges))
            for mode,external in [('branching','branching-bisim'),('preserving','dpbranching-bisim')]:
                relation=set(map(tuple,next(f for f in r['families'] if f['semantics']==mode)['relation']))
                for i in range(len(ss)):
                    for j in range(i,len(ss)):
                        cmd=[a.ltscompare,'--equivalence='+external]
                        if data['silent']:cmd+=['--tau='+','.join(labels[x] for x in data['silent'])]
                        cmd +=[str(Path(tmp,str(i)+'.aut')),str(Path(tmp,str(j)+'.aut'))]
                        out=subprocess.check_output(cmd,text=True,stderr=subprocess.PIPE).strip();assert out in ['true','false'],out
                        assert (out=='true')==((i,j) in relation),(data,mode,i,j,out)
                        count+=1
    print(json.dumps({'reference':version,'frameworks':total,'unordered_pair_semantics_comparisons':count}))
if __name__=='__main__':main()

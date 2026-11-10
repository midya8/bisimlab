"""Optional unmodified mCRL2 ltscompare comparison; not a runtime dependency."""
import argparse
import itertools
import json
import random
import subprocess
import tempfile
from pathlib import Path
from bisimlab.silent import analyze_silent


def main():
    p=argparse.ArgumentParser();p.add_argument('--ltscompare',required=True);args=p.parse_args()
    version=subprocess.check_output([args.ltscompare,'--version'],text=True).splitlines()[0]
    cases=[]
    for n in [1,2]:
        states=['s'+str(i) for i in range(n)]
        choices=list(itertools.product(states,['internal','visible'],states))
        for mask in range(1<<len(choices)):
            cases.append({'system':{'states':states,'actions':['internal','visible'],'edges':[list(e) for i,e in enumerate(choices) if mask>>i&1]},'silent':['internal']})
    rng=random.Random(2081)
    for _ in range(80):
        n=rng.randrange(3,7);states=['s'+str(i) for i in range(n)];actions=['hiddenA','hiddenB','visible'];edges=[list(e) for e in itertools.product(states,actions,states) if rng.random()<.18];rng.shuffle(edges)
        cases.append({'system':{'states':states,'actions':actions,'edges':edges[:18]},'silent':rng.choice([[],['hiddenA'],['hiddenA','hiddenB']])})
    cases.extend(c['input'] for c in json.loads((Path(__file__).resolve().parents[1]/'docs/silent-controls.json').read_text()))
    comparisons=0
    with tempfile.TemporaryDirectory() as tmp:
        for data in cases:
            report=analyze_silent(data);d=data['system'];states=d['states'];labels={a:'act'+str(i) for i,a in enumerate(d['actions'])};edges='\n'.join('(%d,"%s",%d)'%(states.index(s),labels[a],states.index(t)) for s,a,t in d['edges'])
            for i in range(len(states)):
                Path(tmp,str(i)+'.aut').write_text('des (%d,%d,%d)\n%s\n'%(i,len(d['edges']),len(states),edges))
            for mode,external in [('strong','bisim'),('branching','branching-bisim'),('weak','weak-bisim')]:
                relation=set(map(tuple,next(f for f in report['families'] if f['semantics']==mode)['relation']))
                for a in range(len(states)):
                    for b in range(a,len(states)):
                        cmd=[args.ltscompare,'--equivalence='+external]
                        if mode!='strong' and data['silent']:cmd+=['--tau='+','.join(labels[x] for x in data['silent'])]
                        cmd +=[str(Path(tmp,str(a)+'.aut')),str(Path(tmp,str(b)+'.aut'))]
                        output=subprocess.check_output(cmd,text=True,stderr=subprocess.PIPE).strip()
                        assert output in ['true','false'],output
                        assert (output=='true')==((a,b) in relation),(mode,a,b,data,output,report)
                        comparisons+=1
    print(json.dumps({'reference':version,'frameworks':len(cases),'unordered_pair_semantics_comparisons':comparisons}))
if __name__=='__main__':main()

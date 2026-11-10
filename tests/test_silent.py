import copy
import itertools
import random
import unittest
from unittest.mock import patch
from bisimlab.silent import analyze_silent
from bisimlab.silent_verify import verify_silent
from bisimlab.core import analyze


def relation_oracle(data,mode):
    """Union every symmetric reflexive relation satisfying the definition; no refinement."""
    sys=data['system'];n=len(sys['states']);edges=[(sys['states'].index(s),a,sys['states'].index(t)) for s,a,t in sys['edges']];hidden=set(data['silent']);reach={s:{s} for s in range(n)}
    change=True
    while change:
        change=False
        for s,a,t in edges:
            if a in hidden:
                new=reach[s]|reach[t]
                if new!=reach[s]:reach[s]=new;change=True
    optional=list(itertools.combinations(range(n),2));answer={(s,s) for s in range(n)}
    for mask in range(1<<len(optional)):
        rel={(s,s) for s in range(n)}
        for i,(s,t) in enumerate(optional):
            if mask>>i&1:rel|={(s,t),(t,s)}
        okay=True
        for s,q in rel:
            for source,a,t in edges:
                if source!=s:continue
                if mode=='strong':good=any(v==q and b==a and (t,u) in rel for v,b,u in edges)
                elif mode=='weak':
                    targets=reach[q] if a in hidden else {w for v in reach[q] for x,b,u in edges if x==v and b==a for w in reach[u]}
                    good=any((t,u) in rel for u in targets)
                else:good=(a in hidden and (t,q) in rel) or any((s,v) in rel and x==v and (b==a or (a in hidden and b in hidden)) and (t,u) in rel for v in reach[q] for x,b,u in edges)
                if not good:okay=False;break
            if not okay:break
        if okay:answer|=rel
    return answer


class SilentTests(unittest.TestCase):
    def check(self,data,oracle=True):
        before=copy.deepcopy(data);r=analyze_silent(data);self.assertEqual(data,before);self.assertTrue(verify_silent(r));self.assertTrue(all(r['checks'].values()))
        if oracle:
            for f in r['families']:self.assertEqual(set(map(tuple,f['relation'])),relation_oracle(data,f['semantics']))
        return r

    def test_all_two_state_two_label_graphs_and_hidden_subsets(self):
        choices=list(itertools.product(['p','q'],['i','a'],['p','q']))
        for bits in range(256):
            sys={'states':['p','q'],'actions':['i','a'],'edges':[list(e) for i,e in enumerate(choices) if bits>>i&1]}
            for hidden in [[],['i'],['a'],['i','a']]:self.check({'system':sys,'silent':hidden})

    def test_all_three_state_unary_graphs(self):
        states=['p','q','r'];choices=list(itertools.product(states,['i'],states))
        for bits in range(512):
            sys={'states':states,'actions':['i'],'edges':[list(e) for i,e in enumerate(choices) if bits>>i&1]}
            for hidden in [[],['i']]:self.check({'system':sys,'silent':hidden})

    def test_seeded_larger_with_enumerated_relations(self):
        rng=random.Random(7931)
        for _ in range(120):
            n=rng.randint(3,6);states=['s'+str(i) for i in range(n)];actions=['x','y','z'];edges=[list(e) for e in itertools.product(states,actions,states) if rng.random()<.17];rng.shuffle(edges)
            self.check({'system':{'states':states,'actions':actions,'edges':edges[:18]},'silent':rng.choice([[],['x'],['x','y']])},n<=4)

    def test_strict_weak_branching_and_divergence_boundaries(self):
        data={'system':{'states':['p','q','b','d'],'actions':['i','a','b'],'edges':[['p','a','d'],['p','b','d'],['p','i','b'],['q','a','d'],['q','i','b'],['b','b','d']]},'silent':['i']}
        r=self.check(data);self.assertIn([0,1],r['weak_not_branching']);self.assertNotIn([0,1],r['families'][1]['relation'])
        d=self.check({'system':{'states':['dead','loop'],'actions':['i'],'edges':[['loop','i','loop']]},'silent':['i']})
        self.assertIn([0,1],d['branching_not_strong']);self.assertEqual([x['divergent'] for x in d['divergence']],[False,True]);self.assertIn([0,1],d['families'][1]['relation'])
        # A literal tau name stays visible unless explicitly hidden.
        t=self.check({'system':{'states':['p','q'],'actions':['tau'],'edges':[['p','tau','p']]},'silent':[]});self.assertEqual(t['branching_not_strong'],[]);self.assertEqual(t['weak_not_branching'],[])

    def test_foreign_types_schema_and_checker_isolation(self):
        good={'system':{'states':['s'],'actions':[],'edges':[]},'silent':[]};r=self.check(good)
        with patch('bisimlab.silent.analyze_silent',side_effect=AssertionError('generator called')):self.assertTrue(verify_silent(r))
        for d in [None,{},dict(good,extra=1),dict(good,silent=['no']),dict(good,silent=True),dict(good,silent=[1])]:
            with self.assertRaises((ValueError,TypeError)):analyze_silent(d)
        def leaves(x,path=()):
            if isinstance(x,dict):
                for k,v in x.items():yield from leaves(v,path+(k,))
            elif isinstance(x,list):
                for i,v in enumerate(x):yield from leaves(v,path+(i,))
            else:yield path,x
        for path,value in leaves(r):
            if path[0]=='input':continue
            forged=copy.deepcopy(r);target=forged
            for k in path[:-1]:target=target[k]
            target[path[-1]]=not value if type(value)is bool else value+1 if type(value)is int else 'forged'
            with self.assertRaises((ValueError,TypeError)):verify_silent(forged)

    def test_strict_atomic_cli_and_record_structure(self):
        import subprocess,sys,tempfile,json
        from pathlib import Path
        good={'system':{'states':['s'],'actions':[],'edges':[]},'silent':[]}
        report=analyze_silent(good)
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'report.json';out.write_text('preserved')
            cmd=[sys.executable,'-m','bisimlab.silent']
            for raw in ['{',json.dumps(dict(good,extra=1)),'{"system":{},"silent":[],"silent":[]}', 'NaN', ' '*65537]:
                result=subprocess.run(cmd+['-','-o',str(out)],input=raw,text=True,capture_output=True);self.assertEqual(result.returncode,2);self.assertEqual(out.read_text(),'preserved')
            subprocess.run(cmd+['-','-o',str(out)],input=json.dumps(good),text=True,check=True);self.assertEqual(json.loads(out.read_text()),report)
            subprocess.run(cmd+['--verify',str(out)],check=True,capture_output=True)
        for changed in [dict(report,extra=1),{k:v for k,v in report.items() if k!='families'}]:
            with self.assertRaises(ValueError):verify_silent(changed)
        changed=copy.deepcopy(report);changed['families'][0]['rounds'].append(changed['families'][0]['rounds'][-1])
        with self.assertRaises(ValueError):verify_silent(changed)

if __name__=='__main__':unittest.main()

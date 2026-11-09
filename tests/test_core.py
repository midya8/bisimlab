import copy
import itertools
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from bisimlab import analyze,verify
from bisimlab.core import validate

CONTROLS=json.loads((Path(__file__).parents[1]/'docs/controls.json').read_text())


def oracle(d):
    """Enumerate every symmetric relation including the diagonal on tiny graphs."""
    s=d['states'];off=list(itertools.combinations(s,2));union={(x,x) for x in s}
    for bits in range(1<<len(off)):
        rel={(x,x) for x in s}
        for i,(p,q) in enumerate(off):
            if bits>>i&1:rel|={(p,q),(q,p)}
        if all(all(any(v==q and b==a and (t,u) in rel for v,b,u in d['edges']) for x,a,t in d['edges'] if x==p) for p,q in rel):union|=rel
    return union


class Tests(unittest.TestCase):
    def test_controls(self):
        for c in CONTROLS:self.assertTrue(verify(analyze(c['system'])),c['name'])
        r=analyze(CONTROLS[0]['system']);p=next(p for p in r['pairs'] if p['pair']==['p','q'])
        self.assertFalse(p['bisimilar']);self.assertEqual(p['rank'],2);self.assertTrue(p['traces']['equivalent'])
    def test_all_three_state_one_action_graphs(self):
        s=['p','q','r'];edges=list(itertools.product(s,['a'],s))
        for mask in range(512):
            d={'states':s,'actions':['a'],'edges':[list(e) for i,e in enumerate(edges) if mask>>i&1]}
            r=analyze(d);self.assertTrue(verify(r));self.assertEqual({tuple(p['pair']) for p in r['pairs'] if p['bisimilar']},oracle(d))
    def test_seeded_graphs(self):
        rng=random.Random(1809)
        for _ in range(100):
            n=rng.randint(1,6);s=[f's{i}' for i in range(n)];a=['a','b','c'][:rng.randint(0,3)];all_edges=list(itertools.product(s,a,s));rng.shuffle(all_edges)
            d={'states':s,'actions':a,'edges':[list(e) for e in all_edges[:rng.randint(0,min(18,len(all_edges)))]]}
            r=analyze(d);self.assertTrue(verify(r))
            self.assertTrue(all(not p['bisimilar'] or p['traces']['equivalent'] for p in r['pairs']))
            if n<=4:self.assertEqual({tuple(p['pair']) for p in r['pairs'] if p['bisimilar']},oracle(d))
    def test_checker_does_not_call_analyzer(self):
        r=analyze(CONTROLS[0]['system'])
        with patch('bisimlab.core.analyze',side_effect=AssertionError('generator called')):self.assertTrue(verify(r))
    def test_forgeries(self):
        good=analyze(CONTROLS[0]['system']);bad=[]
        def change(fn):
            r=copy.deepcopy(good);fn(r);bad.append(r)
        change(lambda r:r.update(extra=1));change(lambda r:r['rounds'].pop());change(lambda r:r['rounds'][0]['retained'].pop());change(lambda r:r['classes'][0].append('z'));change(lambda r:r['quotient'].pop());change(lambda r:r['pairs'][1].update(bisimilar=True));change(lambda r:r['pairs'][1].update(rank=True));change(lambda r:r['pairs'][1]['traces'].update(equivalent=False));change(lambda r:r['formulas'][1].update(holds=[]));change(lambda r:r['formulas'][1].update(depth=True));change(lambda r:r['formulas'][1].update(arg=9999));change(lambda r:r['rounds'][1]['removed'][0]['attacks'][0].update(fails=False));change(lambda r:r['rounds'][1]['removed'][0].update(winning=True));change(lambda r:r['pairs'].reverse())
        for r in bad:self.assertFalse(verify(r))
    def test_mutation_and_permutation(self):
        d=copy.deepcopy(CONTROLS[0]['system']);old=copy.deepcopy(d);r=analyze(d);self.assertEqual(d,old)
        d['states'].reverse();d['actions'].reverse();d['edges'].reverse();p=analyze(d);self.assertTrue(verify(p));self.assertEqual({tuple(x['pair']):x['bisimilar'] for x in r['pairs']},{tuple(x['pair']):x['bisimilar'] for x in p['pairs']})
    def test_input_boundaries(self):
        base=CONTROLS[0]['system']
        for key,value in [('states',[]),('states',['x']*2),('states',['x']*7),('actions',['a']*4),('actions',['<x>']),('edges',[['bad','a','p']]),('edges',[base['edges'][0]]*2),('edges',[[True,'a','p']]),('edges',{}),('states',['x'*17])]:
            x=copy.deepcopy(base);x[key]=value
            with self.assertRaises(ValueError):validate(x)
        for x in [None,[],{},dict(base,extra=1)]:
            with self.assertRaises(ValueError):validate(x)
        self.assertFalse(verify(None));self.assertFalse(verify({}))
    def test_cli_strict_atomic(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'result.json';out.write_text('preserve')
            def run(raw,*args):return subprocess.run([sys.executable,'-m','bisimlab','-',*args],input=raw,capture_output=True,text=True)
            for raw in ['{','{"states":["x"],"states":["y"],"actions":[],"edges":[]}','NaN',' '*65537]:
                p=run(raw,'--output',str(out));self.assertEqual(p.returncode,2);self.assertEqual(out.read_text(),'preserve')
            p=run(json.dumps(CONTROLS[0]['system']),'--output',str(out));self.assertEqual(p.returncode,0,p.stderr)
            p=run(out.read_text(),'--verify');self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(json.loads(p.stdout),{'valid':True,'schema':'bisimlab-v1'})
            p=run('{}','--verify','--output',str(out));self.assertEqual(p.returncode,2);self.assertTrue(verify(json.loads(out.read_text())))
    def test_quotient_map_is_bisimulation(self):
        for c in CONTROLS:
            r=analyze(c['system']);groups=r['classes'];edges=c['system']['edges']
            for i,group in enumerate(groups):
                for s in group:
                    self.assertEqual({(a,j) for a in c['system']['actions'] for j,target in enumerate(groups) if any(x==s and b==a and y in target for x,b,y in edges)},{(a,j) for k,a,j in r['quotient'] if k==i})

if __name__=='__main__':unittest.main()

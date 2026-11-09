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
from bisimlab.core import traces
from bisimlab.trace_audit import audit_traces,validate_trace
from bisimlab.trace_verify import verify_traces

CONTROLS=json.loads((Path(__file__).parents[1]/'docs/trace-controls.json').read_text())


def reachable_by_paths(d,start,word):
    paths=[[start]]
    for a in word:
        paths=[path+[q] for path in paths for p,b,q in d['edges'] if path[-1]==p and b==a]
    return {p[-1] for p in paths}


class TraceTests(unittest.TestCase):
    def test_controls_and_complete_mismatch_continuation(self):
        for c in CONTROLS:
            r=audit_traces(c['input']);self.assertTrue(verify_traces(r))
            old=traces(c['input']['system'],*c['input']['pair']);self.assertEqual(old['equivalent'],r['equivalent']);self.assertEqual(old['word'],r['word'])
        r=audit_traces(CONTROLS[0]['input']);self.assertEqual(r['word'],['ask','done']);self.assertTrue(r['nodes'][r['first_mismatch']]['next'])
        self.assertTrue(any(not n['left'] and not n['right'] for n in r['nodes']))
    def test_all_three_state_unary_system_pairs(self):
        s=['p','q','r'];edges=list(itertools.product(s,['a'],s))
        for mask in range(512):
            d={'states':s,'actions':['a'],'edges':[list(e) for i,e in enumerate(edges) if mask>>i&1]}
            for p,q in itertools.product(s,repeat=2):
                r=audit_traces({'system':d,'pair':[p,q]});self.assertTrue(verify_traces(r))
                # Exhaustive finite unary words through the product's completeness bound.
                shortest=None
                for k in range(len(r['nodes'])):
                    word=['a']*k;left=reachable_by_paths(d,p,word);right=reachable_by_paths(d,q,word)
                    if bool(left)!=bool(right):shortest=word;break
                self.assertEqual(shortest,r['word'])
                for n in r['nodes']:
                    word=[];i=n['id']
                    while r['nodes'][i]['parent'] is not None:
                        word.insert(0,r['nodes'][i]['via']);i=r['nodes'][i]['parent']
                    self.assertEqual(set(n['left']),reachable_by_paths(d,p,word));self.assertEqual(set(n['right']),reachable_by_paths(d,q,word))
    def test_seeded_multi_action(self):
        rng=random.Random(426)
        for _ in range(120):
            s=[f's{i}' for i in range(rng.randint(1,6))];a=['a','b','c'][:rng.randint(0,3)];edges=list(itertools.product(s,a,s));rng.shuffle(edges)
            d={'system':{'states':s,'actions':a,'edges':[list(e) for e in edges[:rng.randint(0,min(18,len(edges)))]]},'pair':[rng.choice(s),rng.choice(s)]}
            r=audit_traces(d);self.assertTrue(verify_traces(r));old=traces(d['system'],*d['pair']);self.assertEqual(r['equivalent'],old['equivalent']);self.assertEqual(r['word'],old['word'])
            self.assertLessEqual(len(r['nodes']),2**(2*len(s)))
    def test_forged_graph_provenance_and_verdict(self):
        good=audit_traces(CONTROLS[0]['input']);bad=[]
        def change(f):
            r=copy.deepcopy(good);f(r);bad.append(r)
        change(lambda r:r.update(extra=1));change(lambda r:r['nodes'].pop());change(lambda r:r['nodes'].append(r['nodes'][0]));change(lambda r:r['nodes'][0]['next'].reverse());change(lambda r:r['nodes'][0].update(id=False));change(lambda r:r['nodes'][1].update(parent=1));change(lambda r:r['nodes'][1].update(via='done'));change(lambda r:r['nodes'][1].update(depth=True));change(lambda r:r['nodes'][0].update(left=[]));change(lambda r:r.update(equivalent=True));change(lambda r:r['mismatches'].clear());change(lambda r:r['path'].reverse());change(lambda r:r.update(word=['ask']));change(lambda r:r['layers'][0].append(1));change(lambda r:r.update(first_mismatch=True));change(lambda r:r['nodes'][0]['next'].pop())
        for r in bad:self.assertFalse(verify_traces(r))
        self.assertFalse(verify_traces({}));self.assertFalse(verify_traces(None))
    def test_checker_generator_disabled_and_no_mutation(self):
        d=copy.deepcopy(CONTROLS[0]['input']);before=copy.deepcopy(d);r=audit_traces(d);self.assertEqual(d,before)
        with patch('bisimlab.trace_audit.audit_traces',side_effect=AssertionError('generator called')):self.assertTrue(verify_traces(r))
    def test_validation_and_empty_action_graph(self):
        for d in [{},[],None,{'system':CONTROLS[0]['input']['system'],'pair':['p']},{'system':CONTROLS[0]['input']['system'],'pair':['bad','p']},{'system':CONTROLS[0]['input']['system'],'pair':['p',True]}]:
            with self.assertRaises(ValueError):validate_trace(d)
        r=audit_traces(CONTROLS[5]['input']);self.assertEqual(len(r['nodes']),1);self.assertEqual(r['nodes'][0]['next'],[]);self.assertEqual(r['layers'],[[0]]);self.assertEqual(r['path'],[]);self.assertIsNone(r['word']);self.assertTrue(r['equivalent'])
    def test_cli_modes_and_atomic_failure(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'report.json';out.write_text('preserve')
            def run(raw,*args):return subprocess.run([sys.executable,'-m','bisimlab','-','--traces',*args],input=raw,capture_output=True,text=True)
            for raw in ['{}','NaN','{"system":{},"pair":[],"pair":[]}',' '*65537]:
                p=run(raw,'--output',str(out));self.assertEqual(p.returncode,2);self.assertEqual(out.read_text(),'preserve')
            p=run(json.dumps(CONTROLS[0]['input']),'--output',str(out));self.assertEqual(p.returncode,0,p.stderr)
            r=out.read_text();p=run(r,'--verify');self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(json.loads(p.stdout),{'valid':True,'schema':'bisimlab-traces-v1'})
            p=run('{}','--verify','--output',str(out));self.assertEqual(p.returncode,2);self.assertEqual(out.read_text(),r)
    def test_permutation_semantics(self):
        d=copy.deepcopy(CONTROLS[0]['input']);r=audit_traces(d);d['system']['states'].reverse();d['system']['actions'].reverse();d['system']['edges'].reverse();new=audit_traces(d);self.assertTrue(verify_traces(new));self.assertEqual(r['equivalent'],new['equivalent']);self.assertEqual(len(r['word']),len(new['word']))

if __name__=='__main__':unittest.main()

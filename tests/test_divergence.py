import copy,itertools,json,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from bisimlab.divergence import analyze_divergence,partitions
from bisimlab.divergence_verify import verify_divergence
ROOT=Path(__file__).resolve().parents[1]
CONTROLS=json.loads((ROOT/'docs/divergence-controls.json').read_text())


def direct(data,labels):
    # Independent defining T obligations and internal nonempty cycle matrix closure, not exit signatures.
    ss=data['system']['states'];n=len(ss);hidden=data['silent'];edges=[(ss.index(s),a,ss.index(t)) for s,a,t in data['system']['edges']]
    adj=[[False]*n for _ in range(n)]
    for s,a,t in edges:
        if a in hidden and labels[s]==labels[t]:adj[s][t]=True
    nonempty=[row[:] for row in adj]
    for k in range(n):
        for i in range(n):
            for j in range(n):nonempty[i][j] |= nonempty[i][k] and nonempty[k][j]
    reach=[[i==j or nonempty[i][j] for j in range(n)] for i in range(n)]
    divergent=[any(reach[i][j] and nonempty[j][j] for j in range(n)) for i in range(n)]
    stable=True;preserves=True
    for s in range(n):
        for t in range(n):
            if labels[s]!=labels[t]:continue
            preserves &= divergent[s]==divergent[t]
            for p,a,q in edges:
                if p!=s:continue
                if a in hidden and labels[q]==labels[t]:continue
                if not any(reach[t][u] and labels[v]==labels[q] and (b==a or (a in hidden and b in hidden)) for u,b,v in edges):stable=False
    return stable,stable and preserves


class DivergenceTests(unittest.TestCase):
    def test_all_three_state_unary_graphs_defining_obligations(self):
        ss=['p','q','r'];choices=list(itertools.product(ss,['i'],ss))
        for mask in range(512):
            for hidden in [[],['i']]:
                data={'system':{'states':ss,'actions':['i'],'edges':[list(e) for i,e in enumerate(choices) if mask>>i&1]},'silent':hidden};r=analyze_divergence(data)
                for c in r['candidates']:self.assertEqual((c['branching'],c['preserving']),direct(data,c['labels']))
                verify_divergence(r)
    def test_two_state_all_labels_and_hiding(self):
        ss=['p','q'];choices=list(itertools.product(ss,['i','a'],ss))
        for mask in range(256):
            for hidden in [[],['i'],['a'],['i','a']]:
                d={'system':{'states':ss,'actions':['i','a'],'edges':[list(e) for i,e in enumerate(choices) if mask>>i&1]},'silent':hidden};r=analyze_divergence(d)
                for c in r['candidates']:self.assertEqual((c['branching'],c['preserving']),direct(d,c['labels']))
                verify_divergence(r)
    def test_seeded_and_full_capacity(self):
        from tools.check_divergence_mcrl2 import cases
        for d in list(cases())[260:]:
            r=analyze_divergence(d);verify_divergence(r)
            for c in r['candidates']:self.assertEqual((c['branching'],c['preserving']),direct(d,c['labels']))
    def test_controls_luttik_and_cycle_flag_trap(self):
        r=analyze_divergence(CONTROLS[0]['input']);self.assertIn([0,3],r['families'][0]['relation']);self.assertNotIn([0,3],r['families'][1]['relation'])
        universe=r['candidates'][0];self.assertTrue(universe['states'][0]['divergent']);self.assertTrue(universe['states'][3]['divergent'])
        self.assertEqual(r['counts']['partitions'],203)
    def test_all_noninput_primitive_forgery_rejections(self):
        r=analyze_divergence(CONTROLS[3]['input']);count=0
        def leaves(v,path):
            if isinstance(v,dict):
                for k,x in v.items():
                    if not path and k=='input':continue
                    yield from leaves(x,path+[k])
            elif isinstance(v,list):
                for k,x in enumerate(v):yield from leaves(x,path+[k])
            else:yield path,v
        for path,v in leaves(r,[]):
            forged=copy.deepcopy(r);d=forged
            for k in path[:-1]:d=d[k]
            d[path[-1]]=not v if type(v) is bool else v+1 if type(v) is int else 'altered' if type(v) is str else 0
            with self.assertRaises(ValueError):verify_divergence(forged)
            count+=1
        self.assertGreater(count,100);print('divergence primitive-leaf mutations rejected:',count)
    def test_checker_generator_disabled_and_type_shape(self):
        r=analyze_divergence(CONTROLS[0]['input'])
        with patch('bisimlab.divergence.analyze_divergence',side_effect=RuntimeError),patch('bisimlab.divergence.partitions',side_effect=RuntimeError):self.assertTrue(verify_divergence(r))
        for mutate in [lambda x:x.update(extra=0),lambda x:x['counts'].update(partitions=True),lambda x:x['candidates'].reverse(),lambda x:x['families'][0]['relation'].pop()]:
            f=copy.deepcopy(r);mutate(f)
            with self.assertRaises(ValueError):verify_divergence(f)
    def test_normalization_immutability_invalid(self):
        d=copy.deepcopy(CONTROLS[0]['input']);before=copy.deepcopy(d);r=analyze_divergence(d);self.assertEqual(d,before);r['input']['system']['states'][0]='changed';self.assertEqual(d,before)
        for bad in [{},dict(before,extra=0),dict(before,silent=['missing']),dict(before,silent=['internal','internal']),dict(before,silent=True)]:
            with self.assertRaises(ValueError):analyze_divergence(bad)
    def test_cli_strict_and_atomic(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);inp=p/'input';out=p/'output';inp.write_text(json.dumps(CONTROLS[2]['input']))
            cmd=[sys.executable,'-m','bisimlab.divergence']
            subprocess.run(cmd+[str(inp),'-o',str(out)],check=True,capture_output=True);good=out.read_bytes();subprocess.run(cmd+[str(out),'--verify'],check=True,capture_output=True)
            for bad in ['{"system":0,"system":1,"silent":[]}','NaN',' '*65537,'{}']:
                inp.write_text(bad);r=subprocess.run(cmd+[str(inp),'-o',str(out)],capture_output=True);self.assertEqual(r.returncode,2);self.assertEqual(r.stdout,b'');self.assertNotIn(b'Traceback',r.stderr);self.assertEqual(out.read_bytes(),good)
    def test_bell_numbers_and_report_capacity(self):
        self.assertEqual([len(list(partitions(n))) for n in range(1,7)],[1,2,5,15,52,203])
        r=analyze_divergence(CONTROLS[0]['input']);self.assertLess(len(json.dumps(r,indent=2).encode()),8*1024*1024)

        stress={'system':{'states':['a','b','c','d','e','f'],'actions':['x','y','z'],'edges':[[s,a,s] for s in ['a','b','c','d','e','f'] for a in ['x','y','z']]},'silent':['y','z']}
        full=analyze_divergence(stress);verify_divergence(full);self.assertLess(len(json.dumps(full,indent=2).encode()),8*1024*1024)
        self.assertEqual(full['families'][1]['classes'],[[0,1,2,3,4,5]])

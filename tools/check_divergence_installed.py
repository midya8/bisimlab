"""Build and install a fresh wheel, preserve every old installed check, verify new entrypoints."""
import json,os,subprocess,sys,tempfile
from pathlib import Path
from bisimlab.divergence import analyze_divergence
from bisimlab.divergence_verify import verify_divergence
ROOT=Path(__file__).resolve().parents[1]

def command(args,**kw):
    r=subprocess.run(args,capture_output=True,text=True,**kw)
    if r.returncode:
        print(r.stdout,file=sys.stderr);print(r.stderr,file=sys.stderr);r.check_returncode()
    return r.stdout

def main():
    controls=json.loads((ROOT/'docs/divergence-controls.json').read_text());reports=[analyze_divergence(c['input']) for c in controls];assert all(verify_divergence(r) for r in reports)
    with tempfile.TemporaryDirectory() as tmp:
        t=Path(tmp);command([sys.executable,'-m','pip','wheel','--no-deps','--wheel-dir',str(t/'wheels'),str(ROOT)]);command([sys.executable,'-m','venv',str(t/'venv')]);python=t/'venv/bin/python';command([str(python),'-m','pip','install','--no-deps',str(next((t/'wheels').glob('*.whl')))],cwd=tmp)
        env=dict(os.environ);env.pop('PYTHONPATH',None)
        prior=json.loads(command([str(python),str(ROOT/'tools/verify_installed.py')],cwd=tmp,env=env));assert prior['base_reports']==6 and prior['trace_reports']==7 and prior['silent_reports']==10 and prior['entry_points']==4
        modules=['bisimlab.divergence','bisimlab.divergence_input','bisimlab.divergence_verify']
        origins=json.loads(command([str(python),'-c','import json,importlib;print(json.dumps([importlib.import_module(m).__file__ for m in '+repr(modules)+']))'],cwd=tmp,env=env));assert all('site-packages' in p and str(ROOT) not in p for p in origins)
        rejected=0
        for cmd in [[str(python),'-m','bisimlab.divergence'],[str(t/'venv/bin/bisimlab-divergence')]]:
            for c,r in zip(controls,reports):
                raw=command(cmd+['-'],input=json.dumps(c['input']),cwd=tmp,env=env);assert json.loads(raw)==r
                assert json.loads(command(cmd+['-','--verify'],input=raw,cwd=tmp,env=env))=={'valid':True,'schema':'bisimlab-divergence-v1'}
                forged=json.loads(raw);forged['candidates'][0]['index']=True
                f=subprocess.run(cmd+['-','--verify'],input=json.dumps(forged),capture_output=True,text=True,cwd=tmp,env=env);assert f.returncode==2 and not f.stdout and 'Traceback' not in f.stderr;rejected+=1
        print(json.dumps({'new_controls':len(controls),'new_entrypoints':2,'new_module_origins':len(origins),'forged_reports_rejected':rejected,'previous_checks':prior}))
if __name__=='__main__':main()

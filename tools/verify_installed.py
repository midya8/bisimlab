"""Outside-checkout replay through module and console entry points."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def main():
    root=Path(__file__).resolve().parents[1]
    controls=json.loads((root/'docs/controls.json').read_text())
    from bisimlab import analyze
    reports=[analyze(c['system']) for c in controls]
    from bisimlab.trace_audit import audit_traces
    trace_controls=json.loads((root/'docs/trace-controls.json').read_text())
    trace_reports=[audit_traces(c['input']) for c in trace_controls]
    with tempfile.TemporaryDirectory() as tmp:
        env=dict(os.environ);env.pop('PYTHONPATH',None)
        origins=json.loads(subprocess.check_output([sys.executable,'-c','import json,bisimlab,bisimlab.core,bisimlab.verify,bisimlab.__main__;import importlib;print(json.dumps([importlib.import_module(x).__file__ for x in ["bisimlab","bisimlab.core","bisimlab.verify","bisimlab.__main__","bisimlab.trace_audit","bisimlab.trace_verify"]]))'],cwd=tmp,env=env,text=True))
        assert all('site-packages' in p and str(root) not in p for p in origins),origins
        for cmd in [[sys.executable,'-m','bisimlab'],[str(Path(sys.executable).parent/'bisimlab')]]:
            for c,r in zip(controls,reports):
                raw=subprocess.check_output(cmd+['-'],input=json.dumps(c['system']),text=True,cwd=tmp,env=env)
                assert json.loads(raw)==r
                checked=json.loads(subprocess.check_output(cmd+['-','--verify'],input=raw,text=True,cwd=tmp,env=env));assert checked=={'valid':True,'schema':'bisimlab-v1'}
            for c,r in zip(trace_controls,trace_reports):
                raw=subprocess.check_output(cmd+['-','--traces'],input=json.dumps(c['input']),text=True,cwd=tmp,env=env)
                assert json.loads(raw)==r
                checked=json.loads(subprocess.check_output(cmd+['-','--traces','--verify'],input=raw,text=True,cwd=tmp,env=env));assert checked=={'valid':True,'schema':'bisimlab-traces-v1'}
    print(json.dumps({'base_reports':len(reports),'trace_reports':len(trace_reports),'entry_points':2,'installed_origins':origins}))

if __name__=='__main__':main()

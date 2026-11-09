"""Strict bounded JSON CLI with atomic output."""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
from . import analyze, verify
from .trace_audit import audit_traces
from .trace_verify import verify_traces


def load(text):
    def pairs(items):
        out={}
        for k,v in items:
            if k in out: raise ValueError('Duplicate JSON key')
            out[k]=v
        return out
    return json.loads(text, object_pairs_hook=pairs, parse_constant=lambda x: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))


def main():
    ap=argparse.ArgumentParser(description='Inspect finite strong bisimulation and modal witnesses')
    ap.add_argument('input',help='JSON path, or - for stdin');ap.add_argument('--verify',action='store_true');ap.add_argument('--traces',action='store_true',help='Audit a single pair reachable-subset product');ap.add_argument('--output')
    args=ap.parse_args()
    try:
        cap=8*1024*1024 if args.verify else 65536
        raw=sys.stdin.buffer.read(cap+1) if args.input=='-' else Path(args.input).open('rb').read(cap+1)
        if len(raw)>cap: raise ValueError('Input exceeds byte limit')
        data=load(raw.decode('utf-8'))
        if args.verify:
            if not (verify_traces(data) if args.traces else verify(data)): raise ValueError('Invalid report')
            output={'valid':True,'schema':'bisimlab-traces-v1' if args.traces else 'bisimlab-v1'}
        else: output=audit_traces(data) if args.traces else analyze(data)
        text=json.dumps(output,indent=2,allow_nan=False)+'\n'
        if args.output:
            target=Path(args.output);tmp=None
            try:
                with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=target.parent,delete=False) as f: tmp=f.name;f.write(text)
                os.replace(tmp,target)
            finally:
                if tmp and os.path.exists(tmp): os.unlink(tmp)
        else: sys.stdout.write(text)
        return 0
    except (ValueError,TypeError,OSError,RecursionError) as e:
        print('bisimlab: '+str(e),file=sys.stderr);return 2

if __name__=='__main__':raise SystemExit(main())

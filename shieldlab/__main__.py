"""Strict bounded JSON CLI with atomic output."""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
from . import analyze, verify


def load(text):
    def pairs(items):
        out={}
        for k,v in items:
            if k in out: raise ValueError('Duplicate JSON key')
            out[k]=v
        return out
    return json.loads(text, object_pairs_hook=pairs, parse_constant=lambda x: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))


def main():
    ap=argparse.ArgumentParser(description='Inspect finite total turn-based safety games')
    ap.add_argument('input',help='JSON path, or - for stdin');ap.add_argument('--verify',action='store_true');ap.add_argument('--output')
    args=ap.parse_args()
    try:
        cap=8*1024*1024 if args.verify else 65536
        raw=sys.stdin.buffer.read(cap+1) if args.input=='-' else Path(args.input).open('rb').read(cap+1)
        if len(raw)>cap: raise ValueError('Input exceeds byte limit')
        data=load(raw.decode('utf-8'))
        if args.verify:
            if not verify(data): raise ValueError('Invalid report')
            output={'valid':True,'schema':'shieldlab-v1'}
        else: output=analyze(data)
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
        print('shieldlab: '+str(e),file=sys.stderr);return 2

if __name__=='__main__':raise SystemExit(main())

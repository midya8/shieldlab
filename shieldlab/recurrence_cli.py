"""Bounded JSON/atomic output for the separate recurrence contract."""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
from .__main__ import load


def main():
    ap = argparse.ArgumentParser(description='Inspect finite adversarial safe recurrent-target games')
    ap.add_argument('input', help='JSON path, or - for stdin')
    ap.add_argument('--verify', action='store_true')
    ap.add_argument('--output')
    args = ap.parse_args()
    try:
        cap = 16*1024*1024 if args.verify else 65536
        if args.input == '-': raw = sys.stdin.buffer.read(cap+1)
        else:
            with Path(args.input).open('rb') as f: raw = f.read(cap+1)
        if len(raw) > cap: raise ValueError('input exceeds byte limit')
        data = load(raw.decode('utf-8'))
        if args.verify:
            from .recurrence_verify import verify_recurrence
            verify_recurrence(data)
            output = {'valid': True, 'schema': 'shieldlab-recurrence-v1'}
        else:
            from .recurrence import analyze_recurrence
            output = analyze_recurrence(data)
        text = json.dumps(output, indent=2, allow_nan=False)+'\n'
        if len(text.encode()) > 16*1024*1024:
            raise ValueError('report exceeds byte limit')
        if args.output:
            target = Path(args.output); tmp = None
            try:
                with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=target.parent, delete=False) as f:
                    tmp = f.name; f.write(text)
                os.replace(tmp, target)
            finally:
                if tmp and os.path.exists(tmp): os.unlink(tmp)
        else: sys.stdout.write(text)
        return 0
    except (ValueError, TypeError, OSError, RecursionError) as e:
        print('shieldlab-recurrence: '+str(e), file=sys.stderr)
        return 2


if __name__ == '__main__': raise SystemExit(main())

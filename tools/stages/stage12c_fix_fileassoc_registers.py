#!/usr/bin/env python3
from pathlib import Path
import argparse

BAD='    invoke-static {v0, v1, p2}, Lhf/y0;->k(Landroid/content/Context;Lkh/e;Llf/b;)V'
GOOD='    invoke-static/range {p0 .. p2}, Lhf/y0;->k(Landroid/content/Context;Lkh/e;Llf/b;)V'

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args(); root=a.decoded
    p=root/'smali/hf/b0.smali'; t=p.read_text()
    n=t.count(BAD)
    if n!=1: raise RuntimeError(f'expected one Stage12 high-register invoke, got {n}')
    t=t.replace(BAD,GOOD,1)
    p.write_text(t)
    check=p.read_text()
    if BAD in check or check.count(GOOD)!=1:
        raise RuntimeError('Stage12 range invoke repair did not persist exactly once')
    print('stage12c repaired preferred-app dispatch to invoke-static/range {p0 .. p2}')

if __name__=='__main__': main()

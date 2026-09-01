#!/usr/bin/env python3
from pathlib import Path
import argparse,re

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args(); root=a.decoded
    faq=root/'assets/help/faq.html'; t=faq.read_text()
    pat=re.compile(r'\s*<li><b>In-app purchases / Google Play billing service</b>:.*?</li>',re.S|re.I)
    nt,n=pat.subn('',t,count=1)
    if n!=1: raise RuntimeError(f'commerce FAQ block count {n}')
    faq.write_text(nt)
    corpus='\n'.join(p.read_text(errors='ignore') for p in [faq])
    for tok in ('FX Plus','in-app purchase','billing service'):
        if tok.lower() in corpus.lower(): raise RuntimeError(f'commerce help token survives: {tok}')
    print('stage04i commerce help block removed')
if __name__=='__main__': main()

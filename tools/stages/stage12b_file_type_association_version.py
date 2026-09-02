#!/usr/bin/env python3
from pathlib import Path
import argparse,re

VC='9109005'

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args(); root=a.decoded
    y=root/'apktool.yml'; t=y.read_text()
    t,n=re.subn(r'(versionCode:\s*)[^\n]+',r'\g<1>'+VC,t,count=1)
    if n!=1: raise RuntimeError('versionCode not found')
    y.write_text(t)
    if 'versionCode: '+VC not in y.read_text(): raise RuntimeError('Stage12 versionCode did not persist')
    print('stage12b file association test versionCode='+VC)

if __name__=='__main__': main()

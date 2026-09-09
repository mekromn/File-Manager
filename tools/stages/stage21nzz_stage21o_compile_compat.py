#!/usr/bin/env python3
"""Temporary source-compat repair for Stage21o's generated Java helper.

Stage21o is executed later in the same deterministic replay. Its generated Java
client referenced DwFsTrace, which already exists in the decoded APK but is not
on javac's temporary stub classpath. Higher-level DW filesystem exceptions are
already captured by Stage21m, so remove only this redundant compile-time call.
"""
from pathlib import Path
import argparse

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); ap.parse_args()
    p=Path.cwd()/'tools/stages/stage21o_shizuku_file_io_operations.py'
    t=p.read_text()
    old='        DwFsTrace.capture(t);IOException e=t instanceof IOException?(IOException)t:new IOException(String.valueOf(t),t);return ph.n.k(e);'
    new='        IOException e=t instanceof IOException?(IOException)t:new IOException(String.valueOf(t),t);return ph.n.k(e);'
    if t.count(old)!=1: raise RuntimeError('Stage21o DwFsTrace compile anchor count '+str(t.count(old)))
    p.write_text(t.replace(old,new,1))
    print('stage21nzz: repaired Stage21o temporary javac classpath dependency')

if __name__=='__main__': main()

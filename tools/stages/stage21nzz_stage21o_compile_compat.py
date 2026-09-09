#!/usr/bin/env python3
"""Source-compat repair for Stage21o's generated Java helper.

Stage21o is executed later in the same deterministic replay. Its generated Java
client referenced DwFsTrace, which already exists in the decoded APK but is not
on javac's temporary stub classpath. Higher-level DW filesystem exceptions are
already captured by Stage21m, so remove only this redundant compile-time call.
The small self-test UID helper also performs IBinder.transact(), whose declared
RemoteException is broader than IOException, so widen only that private helper's
throws clause; its caller already catches Throwable.
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
    t=t.replace(old,new,1)

    old='    private static int uid(Context c)throws IOException{'
    new='    private static int uid(Context c)throws Exception{'
    if t.count(old)!=1: raise RuntimeError('Stage21o UID throws anchor count '+str(t.count(old)))
    t=t.replace(old,new,1)

    p.write_text(t)
    print('stage21nzz: repaired Stage21o generated Java compile dependencies')

if __name__=='__main__': main()

#!/usr/bin/env python3
from pathlib import Path
import argparse,re

VERSION_CODE='9109003'

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args(); root=a.decoded

    # Install over the already-issued 9109002 diagnostic build.
    yml=root/'apktool.yml'; t=yml.read_text()
    t,n=re.subn(r'(versionCode:\s*)[^\n]+',r'\g<1>'+VERSION_CODE,t,count=1)
    if n!=1: raise RuntimeError('versionCode field missing')
    yml.write_text(t)

    # Exact ART VerifyError regression guard from Pixel 9 Pro XL / Android 16:
    # ph.m.b(MainPrefActivity, PreferenceGroup) later executes new-array v4,v8.
    # v8 must be definitely initialized to integer 2 on the surviving pswitch_0 path.
    p=root/'smali/ph/m.smali'; text=p.read_text()
    sig='b(Ldw/filemanager/ui/fxsystem/MainPrefActivity;Landroid/preference/PreferenceGroup;)V'
    decl=next((l for l in text.splitlines() if l.startswith('.method') and sig in l),None)
    if decl is None: raise RuntimeError('ph/m method b missing')
    s=text.index(decl); e=text.index('.end method',s); m=text[s:e]
    init=m.find('const/4 v8, 0x2')
    use=m.find('new-array v4, v8, [Ljava/lang/Object;')
    if init<0 or use<0 or init>use:
        raise RuntimeError('ART verifier regression: v8 is not initialized before Object[] allocation')
    if '0x7f100610' in m or '0x7f10060f' in m or 'dw.filemanager.intent.extra.privacy' in text:
        raise RuntimeError('removed privacy UI unexpectedly restored')

    print(f'stage11c verifier repair guard passed; repair candidate versionCode={VERSION_CODE}')

if __name__=='__main__': main()

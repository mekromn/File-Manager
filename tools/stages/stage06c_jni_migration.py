#!/usr/bin/env python3
from pathlib import Path
import argparse

PAIRS=[
    (b'Java_nextapp_xf_shell_NativeFileAccess_nativeMkfifo',b'Java_dw_filemanager_NativeFileAccess_nativeMkfifo'),
    (b'Java_nextapp_xf_shell_NativeFileAccess_nativeGetLastModified',b'Java_dw_filemanager_NativeFileAccess_nativeGetLastModified'),
]
ABIS=('arm64-v8a','armeabi-v7a','x86','x86_64')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args(); root=a.decoded
    bridge=root/'smali/dw/filemanager/NativeFileAccess.smali'
    if not bridge.exists(): raise RuntimeError('migrated NativeFileAccess smali missing')
    if 'Ldw/filemanager/NativeFileAccess;' not in bridge.read_text(errors='ignore'):
        raise RuntimeError('NativeFileAccess descriptor not migrated')
    for abi in ABIS:
        so=root/'lib'/abi/'libnative-file-access.so'
        if not so.exists(): raise RuntimeError(f'missing {abi} native bridge')
        data=so.read_bytes()
        for old,new in PAIRS:
            n=data.count(old)
            if n!=1: raise RuntimeError(f'{abi}: expected one {old!r}, got {n}')
            if len(new)>len(old): raise RuntimeError('replacement symbol grew; in-place patch unsafe')
            data=data.replace(old,new+b'\0'*(len(old)-len(new)),1)
        so.write_bytes(data)
        check=so.read_bytes()
        for old,new in PAIRS:
            if old in check: raise RuntimeError(f'{abi}: old JNI symbol remains')
            if check.count(new)!=1: raise RuntimeError(f'{abi}: new JNI symbol count {check.count(new)}')
    print('stage06c JNI bridge migrated in all four ABI libraries')

if __name__=='__main__': main()

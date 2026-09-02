#!/usr/bin/env python3
from pathlib import Path
import argparse, os, shutil, subprocess

ABIS={
    'arm64-v8a':'aarch64-linux-android21-clang',
    'armeabi-v7a':'armv7a-linux-androideabi21-clang',
    'x86':'i686-linux-android21-clang',
    'x86_64':'x86_64-linux-android21-clang',
}
NEW_SYMBOLS=(
    'Java_dw_filemanager_NativeFileAccess_nativeMkfifo',
    'Java_dw_filemanager_NativeFileAccess_nativeGetLastModified',
)
OLD_SYMBOLS=(
    'Java_nextapp_xf_shell_NativeFileAccess_nativeMkfifo',
    'Java_nextapp_xf_shell_NativeFileAccess_nativeGetLastModified',
)

def find_ndk_bin():
    roots=[]
    for key in ('ANDROID_NDK_HOME','ANDROID_NDK_ROOT'):
        v=os.environ.get(key)
        if v: roots.append(Path(v))
    ah=os.environ.get('ANDROID_HOME') or os.environ.get('ANDROID_SDK_ROOT')
    if ah:
        ndks=Path(ah)/'ndk'
        if ndks.is_dir():
            roots.extend(sorted((p for p in ndks.iterdir() if p.is_dir()), reverse=True))
    for root in roots:
        b=root/'toolchains/llvm/prebuilt/linux-x86_64/bin'
        if all((b/c).exists() for c in ABIS.values()): return b
    if all(shutil.which(c) for c in ABIS.values()): return None
    raise RuntimeError('Android NDK clang toolchain not found; set ANDROID_NDK_HOME/ANDROID_NDK_ROOT or install an NDK under ANDROID_HOME/ndk')

def compiler(ndk_bin, name):
    if ndk_bin is None:
        p=shutil.which(name)
        if not p: raise RuntimeError(f'compiler missing from PATH: {name}')
        return p
    return str(ndk_bin/name)

def verify_exports(so:Path, abi:str):
    tool=shutil.which('readelf') or shutil.which('llvm-readelf')
    if not tool: raise RuntimeError('readelf/llvm-readelf not found for JNI export verification')
    # Dynamic symbol table only. `readelf -Ws` reports each export twice when a
    # full .symtab is also present, which is not an error.
    out=subprocess.check_output([tool,'--dyn-syms','--wide',str(so)],text=True,errors='replace')
    for sym in NEW_SYMBOLS:
        count=out.count(sym)
        if count!=1: raise RuntimeError(f'{abi}: expected exactly one dynamic export {sym}, got {count}')
    for sym in OLD_SYMBOLS:
        if sym in out: raise RuntimeError(f'{abi}: legacy JNI dynamic export remains: {sym}')
    sec=subprocess.check_output([tool,'-S','--wide',str(so)],text=True,errors='replace')
    if '.gnu.hash' not in sec and '.hash' not in sec:
        raise RuntimeError(f'{abi}: rebuilt JNI bridge has no ELF dynamic hash table')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args(); root=a.decoded
    bridge=root/'smali/dw/filemanager/NativeFileAccess.smali'
    if not bridge.exists(): raise RuntimeError('migrated NativeFileAccess smali missing')
    bt=bridge.read_text(errors='ignore')
    if 'Ldw/filemanager/NativeFileAccess;' not in bt:
        raise RuntimeError('NativeFileAccess descriptor not migrated')
    if 'const-string v0, "native-file-access"' not in bt or 'System;->loadLibrary' not in bt:
        raise RuntimeError('NativeFileAccess must load native-file-access before native calls')

    source=Path(__file__).resolve().parents[1]/'native'/'native_file_access.c'
    if not source.exists(): raise RuntimeError('clean JNI bridge source missing: '+str(source))
    ndk_bin=find_ndk_bin()

    for abi,cc_name in ABIS.items():
        so=root/'lib'/abi/'libnative-file-access.so'
        so.parent.mkdir(parents=True,exist_ok=True)
        cc=compiler(ndk_bin,cc_name)
        cmd=[cc,'-shared','-fPIC','-Oz','-fvisibility=hidden',
             '-Wl,-soname,libnative-file-access.so','-Wl,--build-id=sha1',
             '-o',str(so),str(source)]
        subprocess.run(cmd,check=True)
        verify_exports(so,abi)

    print('stage06c rebuilt NativeFileAccess JNI bridge for all four ABIs with valid ELF dynamic hashes and DW JNI exports')

if __name__=='__main__': main()

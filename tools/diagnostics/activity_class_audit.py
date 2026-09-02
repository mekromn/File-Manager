#!/usr/bin/env python3
from pathlib import Path
import argparse,re

CLASS_RE=re.compile(r'^\.class[^\n]* (L[^;]+;)',re.M)
ACTIVITY_NAME_RE=re.compile(r'<activity\b[^>]*\bandroid:name="([^"]+)"')
DOTTED_ACTIVITY_RE=re.compile(r'(?<![A-Za-z0-9_$])((?:dw\.filemanager)(?:\.[A-Za-z_$][A-Za-z0-9_$]*)+Activity)(?![A-Za-z0-9_$])')
DESCRIPTOR_ACTIVITY_RE=re.compile(r'(Ldw/filemanager/(?:[A-Za-z0-9_$]+/)*[A-Za-z0-9_$]*Activity;)')


def desc_to_dot(desc:str)->str:
    return desc[1:-1].replace('/','.')


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args(); root=a.decoded
    classes={}
    for sd in root.glob('smali*'):
        for p in sd.rglob('*.smali'):
            txt=p.read_text(errors='ignore')
            m=CLASS_RE.search(txt)
            if m:
                classes[desc_to_dot(m.group(1))]=str(p.relative_to(root))

    manifest=(root/'AndroidManifest.xml').read_text(errors='ignore')
    manifest_activities=[]
    for name in ACTIVITY_NAME_RE.findall(manifest):
        if name.startswith('.'):
            name='com.mekromn.dwfilemanager'+name
        manifest_activities.append(name)

    missing_manifest=[]
    for name in manifest_activities:
        if name.startswith(('android.','com.dropbox.','net.openid.')):
            continue
        if name not in classes:
            missing_manifest.append(name)

    string_refs={}
    descriptor_refs={}
    for sd in root.glob('smali*'):
        for p in sd.rglob('*.smali'):
            txt=p.read_text(errors='ignore')
            for name in DOTTED_ACTIVITY_RE.findall(txt):
                string_refs.setdefault(name,set()).add(str(p.relative_to(root)))
            for desc in DESCRIPTOR_ACTIVITY_RE.findall(txt):
                name=desc_to_dot(desc)
                descriptor_refs.setdefault(name,set()).add(str(p.relative_to(root)))

    missing_string=[]
    for name,refs in sorted(string_refs.items()):
        if name not in classes:
            missing_string.append((name,sorted(refs)))

    # Same simple Activity basename living at one namespace while a missing string points at another.
    basename_map={}
    for name in classes:
        if name.endswith('Activity'):
            basename_map.setdefault(name.rsplit('.',1)[-1],[]).append(name)
    reloc=[]
    for name,refs in missing_string:
        base=name.rsplit('.',1)[-1]
        candidates=sorted(basename_map.get(base,[]))
        if candidates:
            reloc.append((name,candidates,refs))

    print(f'defined_classes={len(classes)} manifest_activities={len(manifest_activities)}')
    print(f'missing_manifest_activities={len(missing_manifest)}')
    for x in missing_manifest:
        print('MISSING_MANIFEST',x)
    print(f'dotted_activity_string_refs={len(string_refs)} missing_dotted_activity_strings={len(missing_string)}')
    for name,refs in missing_string:
        print('MISSING_STRING',name,'::',', '.join(refs[:8]))
    print(f'probable_namespace_relocations={len(reloc)}')
    for old,candidates,refs in reloc:
        print('RELOC',old,'=>',' | '.join(candidates),'::',', '.join(refs[:8]))

    # Also report manifest-vs-string namespace splits by basename even if both classes exist.
    manifest_by_base={x.rsplit('.',1)[-1]:x for x in manifest_activities}
    for s in sorted(string_refs):
        base=s.rsplit('.',1)[-1]
        m=manifest_by_base.get(base)
        if m and m!=s:
            print('MANIFEST_STRING_SPLIT',base,'manifest=',m,'string=',s)

if __name__=='__main__': main()

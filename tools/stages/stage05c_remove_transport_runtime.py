#!/usr/bin/env python3
from pathlib import Path
import argparse,re

def remove_method(path:Path, prefix:str, required=True):
    lines=path.read_text().splitlines(); out=[]; i=0; n=0
    while i<len(lines):
        if lines[i].startswith(prefix):
            n+=1
            while i<len(lines) and lines[i] != '.end method': i+=1
            if i<len(lines): i+=1
            while i<len(lines) and lines[i]=='': i+=1
            continue
        out.append(lines[i]); i+=1
    if required and n!=1: raise RuntimeError(f'{path}: {prefix}: count {n}')
    path.write_text('\n'.join(out)+'\n')
    return n

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args(); root=a.decoded; sm=root/'smali'
    mf=root/'AndroidManifest.xml'; t=mf.read_text()
    t2=re.sub(r'\n\s*<service android:exported="false" android:name="com\.google\.android\.datatransport\.runtime\.backends\.TransportBackendDiscovery">.*?</service>', '', t, flags=re.S)
    t2=re.sub(r'\n\s*<service android:exported="false" android:name="com\.google\.android\.datatransport\.runtime\.scheduling\.jobscheduling\.JobInfoSchedulerService"[^>]*/>', '', t2)
    t2=re.sub(r'\n\s*<receiver android:exported="false" android:name="com\.google\.android\.datatransport\.runtime\.scheduling\.jobscheduling\.AlarmManagerSchedulerBroadcastReceiver"[^>]*/>', '', t2)
    if t2==t: raise RuntimeError('DataTransport manifest roots not found')
    mf.write_text(t2)
    remove_method(sm/'b9/e.smali','.method public v(Ly3/i;IZ)V')
    remove_method(sm/'ce/b.smali','.method public c()Ljava/lang/Object;'); p=sm/'ce/b.smali'; p.write_text(p.read_text().replace('.implements Lg4/b;\n',''))
    remove_method(sm/'a8/a.smali','.method public c()Ljava/lang/Object;'); p=sm/'a8/a.smali'; p.write_text(p.read_text().replace('.implements Lg4/b;\n',''))
    remove_method(sm/'e4/g.smali','.method public c()Ljava/lang/Object;'); p=sm/'e4/g.smali'; p.write_text(p.read_text().replace('.implements Lg4/b;\n',''))
    remove_method(sm/'ca/f.smali','.method public d(Ly3/i;I)V')
    remove_method(sm/'e4/e.smali','.method public synthetic constructor <init>(Lca/f;Ly3/i;ILjava/lang/Runnable;)V')
    p=sm/'e4/e.smali'; lines=p.read_text().splitlines(); start=next(i for i,l in enumerate(lines) if l.strip()==':pswitch_1'); data=next(i for i,l in enumerate(lines) if l.strip()==':pswitch_data_0'); body='\n'.join(lines[start:data])
    for tok in ('Lca/f;','Ly3/i;','Lb9/e;->v(Ly3/i;IZ)V'):
        if tok not in body: raise RuntimeError(f'e4/e transport arm missing {tok}')
    p.write_text('\n'.join(lines[:start]+['    :pswitch_1','    return-void','']+lines[data:])+'\n')
    p=sm/'be/j.smali'; lines=p.read_text().splitlines(); hit=next(i for i,l in enumerate(lines) if 'check-cast v0, Lcom/google/android/datatransport/runtime/scheduling/jobscheduling/JobInfoSchedulerService;' in l); start=hit
    while start>=0 and lines[start].strip()!=':pswitch_12': start-=1
    end=hit
    while end<len(lines) and lines[end].strip()!='return-void': end+=1
    if start<0 or end>=len(lines): raise RuntimeError('be/j scheduler arm bounds')
    p.write_text('\n'.join(lines[:start]+['    :pswitch_12','    return-void','']+lines[end+1:])+'\n')
    p=sm/'e4/a.smali'; txt=p.read_text(); txt=txt.replace('    :pswitch_7\n    sget v0, Lcom/google/android/datatransport/runtime/scheduling/jobscheduling/AlarmManagerSchedulerBroadcastReceiver;->a:I\n\n    .line 364\n    .line 365\n    return-void','    :pswitch_7\n    return-void');
    if 'AlarmManagerSchedulerBroadcastReceiver' in txt: raise RuntimeError('e4/a alarm ref remains')
    p.write_text(txt)
    remove_method(sm/'androidx/emoji2/text/n.smali','.method public b()Ly3/j;')
    remove_method(sm/'b9/e.smali','.method public get()Ljava/lang/Object;'); p=sm/'b9/e.smali'; p.write_text(p.read_text().replace('.implements La4/b;\n',''))
    remove_method(sm/'b2/d.smali','.method public constructor <init>(Ly3/i;Lv3/b;Le9/b;Ly3/n;)V')
    p=sm/'d4/a.smali'; txt=p.read_text(); old='''    const-class v0, Ly3/n;\n\n    .line 2\n    .line 3\n    invoke-virtual {v0}, Ljava/lang/Class;->getName()Ljava/lang/String;\n\n    .line 4\n    .line 5\n    .line 6\n    move-result-object v0'''
    if old not in txt: raise RuntimeError('d4/a logger block not found')
    p.write_text(txt.replace(old,'    const-string v0, "DataTransport"'))
    for rel in ['y3/n.smali','y3/j.smali','com/google/android/datatransport/runtime/scheduling/jobscheduling/JobInfoSchedulerService.smali','com/google/android/datatransport/runtime/scheduling/jobscheduling/AlarmManagerSchedulerBroadcastReceiver.smali']:
        q=sm/rel
        if not q.exists(): raise RuntimeError(f'missing expected {rel}')
        q.unlink()
    corpus='\n'.join(p.read_text(errors='ignore') for p in sm.rglob('*.smali'))
    forbidden=['Ly3/n;','Ly3/j;','JobInfoSchedulerService','AlarmManagerSchedulerBroadcastReceiver','Lb9/e;->v(Ly3/i;IZ)V','Lca/f;->d(Ly3/i;I)V']
    bad=[x for x in forbidden if x in corpus]
    if bad: raise RuntimeError(f'stage05c forbidden refs remain: {bad}')
    mt=mf.read_text()
    if any(x in mt for x in ('TransportBackendDiscovery','JobInfoSchedulerService','AlarmManagerSchedulerBroadcastReceiver')): raise RuntimeError('DataTransport manifest component remains')
    print('stage05c DataTransport scheduler/runtime root island removed')
if __name__=='__main__': main()

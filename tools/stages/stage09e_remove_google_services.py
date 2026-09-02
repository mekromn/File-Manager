#!/usr/bin/env python3
from pathlib import Path
import argparse,re

def remove_method(root, rel, sig):
    p=root/'smali'/rel; t=p.read_text(); s=t.index(sig); e=t.index('.end method',s)+len('.end method')
    if e < len(t) and t[e]=='\n': e+=1
    p.write_text(t[:s]+t[e:])

def replace_label_range(text,start_label,next_label,repl):
    a=text.index(f'    :pswitch_{start_label}\n')
    b=text.index(f'    :pswitch_{next_label}\n',a+1)
    return text[:a]+repl+text[b:]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args(); root=a.decoded; S=root/'smali'

    remove_method(root,'ab/d.smali','.method public j(Lcom/google/android/gms/common/internal/a;Lg6/a;)V')
    remove_method(root,'l0/h.smali','.method public b(Lr5/a;)V')
    p=S/'l0/h.smali'; p.write_text(p.read_text().replace('.implements Lu5/b;\n',''))
    remove_method(root,'ae/d.smali','.method public constructor <init>(Lt5/c;Lcom/google/android/gms/common/internal/a;Lt5/a;)V')
    remove_method(root,'ae/d.smali','.method public b(Lr5/a;)V')
    remove_method(root,'ae/d.smali','.method public g(Lr5/a;)V')
    p=S/'ae/d.smali'; p.write_text(p.read_text().replace('.implements Lu5/b;\n',''))
    remove_method(root,'kf/d.smali','.method public b(ZLcom/google/android/gms/common/api/Status;)V')
    remove_method(root,'b9/e.smali','.method public constructor <init>(Ljava/util/Set;Ljava/lang/String;Ljava/lang/String;)V')
    remove_method(root,'k2/p.smali','.method public constructor <init>(Lr5/a;I)V')
    remove_method(root,'k2/y.smali','.method public constructor <init>(Lw5/b;Lmh/f;)V')
    remove_method(root,'x/b.smali','.method public static bridge synthetic k(Landroid/content/Context;Landroid/content/Intent;Ljava/util/concurrent/Executor;Lu5/w;)Z')
    for sig in [
      '.method public static bridge synthetic b(Landroid/app/NotificationManager;)Landroid/app/NotificationChannel;',
      '.method public static synthetic c(Ljava/lang/String;)Landroid/app/NotificationChannel;',
      '.method public static bridge synthetic f(Landroid/content/Context;Lt5/l;Landroid/content/IntentFilter;I)Landroid/content/Intent;',
    ]: remove_method(root,'a7/b.smali',sig)
    remove_method(root,'androidx/emoji2/text/o.smali','.method public constructor <init>(Lt5/p;)V')
    remove_method(root,'s5/a.smali','.method public constructor <init>(Lcom/google/android/gms/common/api/Status;)V')
    remove_method(root,'rd/c.smali','.method public static a(Lu5/d;Landroid/os/Parcel;I)V')

    p=S/'g6/a.smali'; t=p.read_text(); old='    invoke-static {p1, v1}, Lu5/o;->c(Ljava/lang/Object;Ljava/lang/String;)V\n'
    new='''    if-nez p1, :cond_dw_g6_nonnull\n\n    invoke-static {v1}, La8/c;->x(Ljava/lang/String;)V\n\n    :cond_dw_g6_nonnull\n'''
    if t.count(old)!=1: raise RuntimeError('g6/a GMS guard shape changed')
    p.write_text(t.replace(old,new,1))

    p=S/'t4/j.smali'; t=p.read_text(); a0=t.index('    sget-object p1, Lr5/d;->c:Lr5/d;\n'); b0=t.index('    :sswitch_0\n',a0)
    repl='''    invoke-direct {p0}, Ljava/lang/Object;-><init>()V\n\n    const/4 p1, 0x0\n\n    iput-object p1, p0, Lt4/j;->i:Ljava/lang/Object;\n\n    iput-object p1, p0, Lt4/j;->X:Ljava/lang/Object;\n\n    return-void\n\n'''
    p.write_text(t[:a0]+repl+t[b0:])

    p=S/'androidx/emoji2/text/j.smali'; t=p.read_text(); s=t.index('.method public final run()V'); ps=t.index('    :pswitch_0\n',s); pre=t[:s]; meth=t[s:ps]
    marker='    packed-switch v0, :pswitch_data_0\n'; ma=meth.index(marker)+len(marker); meth=meth[:ma]+'\n    return-void\n\n'; p.write_text(pre+meth+t[ps:])
    p=S/'androidx/activity/i.smali'; t=p.read_text(); a0=t.index('    :pswitch_5\n'); b0=t.index('    :pswitch_7\n',a0); p.write_text(t[:a0]+'    :pswitch_5\n    return-void\n\n    :pswitch_6\n    return-void\n\n'+t[b0:])
    p=S/'androidx/fragment/app/d.smali'; t=p.read_text(); a0=t.index('    :pswitch_3\n'); b0=t.index('    :pswitch_4\n',a0); p.write_text(t[:a0]+'    :pswitch_3\n    return-void\n\n'+t[b0:])

    p=S/'rd/c.smali'; t=p.read_text()
    for start,nxt in [('10','20'),('20','27'),('27','28'),('28','29'),('29','33'),('33','34'),('36','37'),('37','38')]:
        t=replace_label_range(t,start,nxt,f'    :pswitch_{start}\n    const/4 v2, 0x0\n    return-object v2\n\n')
    ns=t.index('.method public final newArray(I)[Ljava/lang/Object;'); ne=t.index('.end method',ns)+len('.end method'); pre=t[:ns]; nm=t[ns:ne]; post=t[ne:]
    for start,nxt in [('10','11'),('11','12'),('12','13'),('13','14'),('14','15'),('15','16'),('18','19'),('19','1a')]:
        nm=replace_label_range(nm,start,nxt,f'    :pswitch_{start}\n    const/4 p1, 0x0\n    return-object p1\n\n')
    p.write_text(pre+nm+post)

    p=S/'kh/n.smali'; t=p.read_text(); cs=t.index('.method public final createFromParcel'); ce=t.index('.end method',cs)+len('.end method'); pre=t[:cs]; cm=t[cs:ce]; post=t[ce:]
    for start,nxt in [('2','3'),('3','4')]: cm=replace_label_range(cm,start,nxt,f'    :pswitch_{start}\n    const/4 p1, 0x0\n    return-object p1\n\n')
    t=pre+cm+post; ns=t.index('.method public final newArray'); ne=t.index('.end method',ns)+len('.end method'); pre=t[:ns]; nm=t[ns:ne]; post=t[ne:]
    for start,nxt in [('2','3'),('3','4')]: nm=replace_label_range(nm,start,nxt,f'    :pswitch_{start}\n    const/4 p1, 0x0\n    return-object p1\n\n')
    p.write_text(pre+nm+post)

    p=S/'r5/g.smali'; t=p.read_text(); p.write_text(t.replace('.field public static X:Lr5/g;\n',''))
    for sig in [
      '.method public static C(Landroid/content/Context;)V',
      '.method public static final varargs L(Landroid/content/pm/PackageInfo;[Lr5/k;)Lr5/k;',
      '.method public static final M(Landroid/content/pm/PackageInfo;)Z',
    ]: remove_method(root,'r5/g.smali',sig)

    p=S/'u5/g.smali'; t=p.read_text(); sig='.method public b(Ljavax/net/ssl/SSLSocket;)Z'; s=t.index(sig); e=t.index('.end method',s)+len('.end method')
    repl='''.method public b(Ljavax/net/ssl/SSLSocket;)Z\n    .locals 1\n    const/4 v0, 0x0\n    return v0\n.end method'''; p.write_text(t[:s]+repl+t[e:])

    delete=[]
    delete += [str(p.relative_to(S)) for p in (S/'com/google/android/gms').rglob('*.smali')]
    delete += ['a6/a.smali','b6/c.smali','v5/a.smali','x5/a.smali']
    delete += [f'e6/{x}.smali' for x in ['a','b']]
    delete += ['f6/a.smali']
    delete += [f'r5/{x}.smali' for x in list('abcdefhijklmn')]
    delete += [f's5/{x}.smali' for x in list('bcdefg')]
    delete += [f't5/{x}.smali' for x in list('abcdefhijklmnopqr')]
    delete += [f'u5/{x}.smali' for x in list('abcdefhijklmnopqrstuvwxyz')]
    delete += [f'w5/{x}.smali' for x in list('abcd')]
    for rel in delete:
        p=S/rel
        if not p.exists(): raise RuntimeError(f'expected GMS island file missing before delete: {rel}')
        p.unlink()

    p=root/'AndroidManifest.xml'; t=p.read_text()
    t=re.sub(r'\s*<activity android:exported="false" android:name="com\.google\.android\.gms\.common\.api\.GoogleApiActivity" android:theme="@android:style/Theme\.Translucent\.NoTitleBar"\s*/>\s*','\n',t)
    t=re.sub(r'\s*<meta-data android:name="com\.google\.android\.gms\.version" android:value="@integer/google_play_services_version"\s*/>\s*','\n',t)
    p.write_text(t)

    rx=re.compile(r'\s*<string\s+name="common_google_play_services_[^"]+"(?:\s+[^>]*)?>.*?</string>\s*',re.S)
    for p in (root/'res').glob('values*/strings.xml'):
        t=p.read_text(); p.write_text(rx.sub('\n',t))
    p=root/'res/values/integers.xml'; t=p.read_text(); p.write_text(re.sub(r'\s*<integer name="google_play_services_version">.*?</integer>\s*','\n',t,flags=re.S))
    p=root/'res/values/public.xml'; t=p.read_text();
    t=re.sub(r'\s*<public type="integer" name="google_play_services_version" id="0x[0-9a-fA-F]+"\s*/>\s*','\n',t)
    t=re.sub(r'\s*<public type="string" name="common_google_play_services_[^"]+" id="0x[0-9a-fA-F]+"\s*/>\s*','\n',t)
    p.write_text(t)

    p=root/'res/values/public.xml'; t=p.read_text(); t=re.sub(r'\s*<public type="(?:color|drawable)" name="(?:common_google_signin_btn_[^"]+|googleg_[^"]+)" id="0x[0-9a-fA-F]+"\s*/>\s*','\n',t); p.write_text(t)
    p=root/'res/values/colors.xml'; t=p.read_text(); t=re.sub(r'\s*<color name="common_google_signin_btn_[^"]+">.*?</color>\s*','\n',t,flags=re.S); p.write_text(t)
    for p in list((root/'res').rglob('*')):
        if p.is_file() and (p.stem.startswith('common_google_signin_btn_') or p.stem.startswith('googleg_')): p.unlink()

    p=S/'kb/a.smali'; t=p.read_text(); s=t.index('.method static constructor <clinit>()V'); e=t.index('.end method',s)+len('.end method')
    clinit=r'''.method static constructor <clinit>()V
    .locals 11
    new-instance v0, Lkb/a;
    new-instance v5, Lhh/e;
    const/16 v1, 0xd
    invoke-direct {v5, v1}, Lhh/e;-><init>(I)V
    const-string v1, "AMAZON"
    const/4 v2, 0x0
    const v3, 0x7f100115
    const-string v4, "com.amazon.venezia"
    invoke-direct/range {v0 .. v5}, Lkb/a;-><init>(Ljava/lang/String;IILjava/lang/String;Lhh/e;)V
    new-instance v1, Lkb/a;
    new-instance v6, Lhh/e;
    const/16 v2, 0xe
    invoke-direct {v6, v2}, Lhh/e;-><init>(I)V
    const-string v2, "AMAZON_UNDERGROUND"
    const/4 v3, 0x1
    const v4, 0x7f100115
    const-string v5, "com.amazon.mShop.android"
    invoke-direct/range {v1 .. v6}, Lkb/a;-><init>(Ljava/lang/String;IILjava/lang/String;Lhh/e;)V
    new-instance v2, Lkb/a;
    new-instance v7, Lhh/e;
    const/16 v3, 0xf
    invoke-direct {v7, v3}, Lhh/e;-><init>(I)V
    const-string v3, "F_DROID"
    const/4 v4, 0x2
    const v5, 0x7f100116
    const-string v6, "org.fdroid.fdroid"
    invoke-direct/range {v2 .. v7}, Lkb/a;-><init>(Ljava/lang/String;IILjava/lang/String;Lhh/e;)V
    new-instance v3, Lkb/a;
    new-instance v8, Lhh/e;
    const/16 v4, 0x10
    invoke-direct {v8, v4}, Lhh/e;-><init>(I)V
    const-string v4, "F_DROID_PRIVILEGED"
    const/4 v5, 0x3
    const v6, 0x7f100116
    const-string v7, "org.fdroid.fdroid.privileged"
    invoke-direct/range {v3 .. v8}, Lkb/a;-><init>(Ljava/lang/String;IILjava/lang/String;Lhh/e;)V
    new-instance v4, Lkb/a;
    new-instance v9, Lhh/e;
    const/16 v5, 0x11
    invoke-direct {v9, v5}, Lhh/e;-><init>(I)V
    const-string v5, "SAMSUNG"
    const/4 v6, 0x4
    const v7, 0x7f100118
    const-string v8, "com.sec.android.app.samsungapps"
    invoke-direct/range {v4 .. v9}, Lkb/a;-><init>(Ljava/lang/String;IILjava/lang/String;Lhh/e;)V
    const/4 v5, 0x5
    new-array v5, v5, [Lkb/a;
    const/4 v6, 0x0
    aput-object v0, v5, v6
    const/4 v6, 0x1
    aput-object v1, v5, v6
    const/4 v6, 0x2
    aput-object v2, v5, v6
    const/4 v6, 0x3
    aput-object v3, v5, v6
    const/4 v6, 0x4
    aput-object v4, v5, v6
    sput-object v5, Lkb/a;->Z:[Lkb/a;
    new-instance v0, Ljava/util/HashMap;
    invoke-direct {v0}, Ljava/util/HashMap;-><init>()V
    invoke-static {v0}, Ljava/util/Collections;->unmodifiableMap(Ljava/util/Map;)Ljava/util/Map;
    move-result-object v0
    sput-object v0, Lkb/a;->Y:Ljava/util/Map;
    return-void
.end method'''
    p.write_text(t[:s]+clinit+t[e:])
    for p in (root/'res').glob('values*/strings.xml'):
        t=p.read_text(); p.write_text(re.sub(r'\s*<string name="app_market_google"(?:\s+[^>]*)?>.*?</string>\s*','\n',t,flags=re.S))
    p=root/'res/values/public.xml'; t=p.read_text(); p.write_text(re.sub(r'\s*<public type="string" name="app_market_google" id="0x[0-9a-fA-F]+"\s*/>\s*','\n',t))

    all_smali='\n'.join(p.read_text(errors='ignore') for sd in root.glob('smali*') for p in sd.rglob('*.smali'))
    if 'Lcom/google/android/gms/' in all_smali or 'com.google.android.gms' in all_smali: raise RuntimeError('GMS descriptor/string remains')
    if 'com.google.android.gms' in (root/'AndroidManifest.xml').read_text(): raise RuntimeError('GMS manifest entry remains')
    if 'GOOGLE_PLAY' in all_smali or 'com.android.vending' in all_smali: raise RuntimeError('Google Play market integration remains')
    for p in (root/'res').rglob('*'):
        if p.is_file() and (p.stem.startswith('common_google_signin_btn_') or p.stem.startswith('googleg_')): raise RuntimeError(f'GMS sign-in resource remains {p}')
    print(f'stage09e removed Google Play Services/common client island and Google Play market surface; deleted {len(delete)} pure classes')

if __name__=='__main__': main()

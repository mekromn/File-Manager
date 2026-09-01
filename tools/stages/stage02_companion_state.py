#!/usr/bin/env python3
from __future__ import annotations
import argparse, re
from pathlib import Path

HELPER_DESC = 'Ldw/filemanager/core/Companion;'
EXPECTED_SHA256_B64 = 'AveXMCI/RUzNEIQU7AY2GLdipHaK7ftkRi2EFvQXxnc='

HELPER = f'''.class public final Ldw/filemanager/core/Companion;
.super Ljava/lang/Object;

# One pure compatibility boolean. No cache, state, UI, callback, product, timer, or network path.
.method public static present(Landroid/content/Context;)Z
    .locals 7

    :try_start_0
    invoke-virtual {{p0}}, Landroid/content/Context;->getPackageManager()Landroid/content/pm/PackageManager;
    move-result-object v0

    const-string v1, "nextapp.fx.rk"
    const/16 v2, 0x40
    invoke-virtual {{v0, v1, v2}}, Landroid/content/pm/PackageManager;->getPackageInfo(Ljava/lang/String;I)Landroid/content/pm/PackageInfo;
    move-result-object v0

    iget-object v0, v0, Landroid/content/pm/PackageInfo;->signatures:[Landroid/content/pm/Signature;
    if-eqz v0, :missing

    array-length v1, v0
    const/4 v2, 0x0

    :loop
    if-ge v2, v1, :missing
    aget-object v3, v0, v2

    const-string v4, "SHA-256"
    invoke-static {{v4}}, Ljava/security/MessageDigest;->getInstance(Ljava/lang/String;)Ljava/security/MessageDigest;
    move-result-object v4

    invoke-virtual {{v3}}, Landroid/content/pm/Signature;->toByteArray()[B
    move-result-object v3
    invoke-virtual {{v4, v3}}, Ljava/security/MessageDigest;->digest([B)[B
    move-result-object v3

    const/4 v4, 0x2
    invoke-static {{v3, v4}}, Landroid/util/Base64;->encodeToString([BI)Ljava/lang/String;
    move-result-object v3

    const-string v4, "{EXPECTED_SHA256_B64}"
    invoke-virtual {{v4, v3}}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v3
    if-nez v3, :present

    add-int/lit8 v2, v2, 0x1
    goto :loop

    :present
    const/4 v0, 0x1
    :try_end_0
    .catch Ljava/lang/Exception; {{:try_start_0 .. :try_end_0}} :missing
    return v0

    :missing
    const/4 v0, 0x0
    return v0
.end method
'''


def method_ranges(lines: list[str]):
    starts=[i for i,l in enumerate(lines) if l.startswith('.method')]
    for idx,s in enumerate(starts):
        e=starts[idx+1] if idx+1 < len(starts) else len(lines)
        yield s,e,lines[s]


def remove_method(text: str, signature_contains: str) -> str:
    lines=text.splitlines()
    out=[]; removed=0; i=0
    while i < len(lines):
        if lines[i].startswith('.method') and signature_contains in lines[i]:
            removed += 1
            while i < len(lines) and lines[i] != '.end method': i += 1
            if i < len(lines): i += 1
            while i < len(lines) and lines[i] == '': i += 1
            continue
        out.append(lines[i]); i += 1
    if removed != 1:
        raise RuntimeError(f'expected one method containing {signature_contains!r}, removed {removed}')
    return '\n'.join(out)+'\n'


def first_instruction(lines: list[str], start: int, limit: int = 40):
    for k in range(start+1, min(len(lines), start+1+limit)):
        s=lines[k].strip()
        if not s or s.startswith('.line') or s.startswith('#'):
            continue
        return k,s
    return None,None


def rewrite_simple_j_a(path: Path) -> int:
    """Replace j(Context)->state + t8/b.a(state) with Companion.present(Context)."""
    lines=path.read_text().splitlines()
    count=0; i=0
    while i < len(lines):
        l=lines[i]
        if 'Llh/n;->j(Landroid/content/Context;)I' not in l:
            i += 1; continue
        m=re.search(r'invoke-static \{([^}]+)\}, Llh/n;->j\(Landroid/content/Context;\)I', l)
        if not m: raise RuntimeError(f'cannot parse j call {path}:{i+1}')
        ctx=m.group(1).strip()
        k1,s1=first_instruction(lines,i)
        if not s1 or not s1.startswith('move-result '):
            # Known side-effect-only stale state call: remove it entirely.
            lines[i]='    # removed obsolete integer capability-state probe'
            count += 1; i += 1; continue
        state_reg=s1.split()[-1]
        k2,s2=first_instruction(lines,k1)
        if s2 != f'invoke-static {{{state_reg}}}, Lt8/b;->a(I)Z':
            # trial/status callers are handled separately
            i += 1; continue
        k3,s3=first_instruction(lines,k2)
        if not s3 or not s3.startswith('move-result '):
            raise RuntimeError(f'missing predicate move-result {path}:{k2+1}')
        bool_reg=s3.split()[-1]
        lines[i]=f'    invoke-static {{{ctx}}}, {HELPER_DESC}->present(Landroid/content/Context;)Z'
        lines[k1]=f'    move-result {bool_reg}'
        lines[k2]='    # removed legacy integer capability predicate'
        lines[k3]='    # boolean already returned by Companion.present'
        count += 1
        i=k3+1
    path.write_text('\n'.join(lines)+'\n')
    return count


def rewrite_plus_home_section(path: Path) -> None:
    text=path.read_text()
    # Replace methods a/f completely: available is direct boolean; trial flag always absent.
    def repl_method(text, name, body):
        lines=text.splitlines(); out=[]; i=0; n=0
        prefix=f'.method public final {name}('
        while i<len(lines):
            if lines[i].startswith(prefix):
                n+=1
                # retain supplied full method block
                out.extend(body.strip('\n').splitlines())
                while i<len(lines) and lines[i] != '.end method': i+=1
                if i<len(lines): i+=1
                while i<len(lines) and lines[i]=='': i+=1
                out.append('')
                continue
            out.append(lines[i]); i+=1
        if n!=1: raise RuntimeError(f'{path}: expected one {name}, got {n}')
        return '\n'.join(out)+'\n'
    body_a=f'''.method public final a(Landroid/content/Context;)V
    .locals 1
    invoke-static {{p1}}, {HELPER_DESC}->present(Landroid/content/Context;)Z
    move-result v0
    sput-boolean v0, Lnextapp/fx/plus/ui/j;->a:Z
    const/4 v0, 0x0
    sput-boolean v0, Lnextapp/fx/plus/ui/j;->b:Z
    invoke-super {{p0, p1}}, Lnextapp/fx/ui/homemodel/StaticHomeSection;->a(Landroid/content/Context;)V
    return-void
.end method'''
    body_f=f'''.method public final f(Landroid/content/Context;)V
    .locals 1
    invoke-static {{p1}}, {HELPER_DESC}->present(Landroid/content/Context;)Z
    move-result p1
    sput-boolean p1, Lnextapp/fx/plus/ui/j;->a:Z
    const/4 v0, 0x0
    sput-boolean v0, Lnextapp/fx/plus/ui/j;->b:Z
    return-void
.end method'''
    text=repl_method(text,'a',body_a)
    text=repl_method(text,'f',body_f)
    path.write_text(text)


def rewrite_trial_tutorial_helper(path: Path) -> None:
    # This object remains only until the tutorial/status UI is structurally deleted in next stage.
    text=path.read_text()
    lines=text.splitlines(); out=[]; i=0; n=0
    while i<len(lines):
        if lines[i].startswith('.method public final a(Landroid/content/Context;)Landroid/widget/CheckBox;'):
            n+=1
            out += ['.method public final a(Landroid/content/Context;)Landroid/widget/CheckBox;',
                    '    .locals 1',
                    '    const/4 v0, 0x0',
                    '    iput-object v0, p0, Lnextapp/fx/plus/ui/k;->a:Ljava/lang/Boolean;',
                    '    return-object v0',
                    '.end method','']
            while i<len(lines) and lines[i] != '.end method': i+=1
            if i<len(lines): i+=1
            while i<len(lines) and lines[i]=='': i+=1
            continue
        out.append(lines[i]); i+=1
    if n!=1: raise RuntimeError(f'{path}: tutorial helper method count {n}')
    path.write_text('\n'.join(out)+'\n')


def simplify_about_status_string(path: Path) -> None:
    text=path.read_text(); lines=text.splitlines(); out=[]; i=0; n=0
    while i<len(lines):
        if lines[i].startswith('.method public static a(Landroid/content/Context;)Ljava/lang/String;'):
            n+=1
            out += ['.method public static a(Landroid/content/Context;)Ljava/lang/String;',
                    '    .locals 1',
                    '    const v0, 0x7f100119',
                    '    invoke-virtual {p0, v0}, Landroid/content/Context;->getString(I)Ljava/lang/String;',
                    '    move-result-object p0',
                    '    return-object p0',
                    '.end method','']
            while i<len(lines) and lines[i] != '.end method': i+=1
            if i<len(lines): i+=1
            while i<len(lines) and lines[i]=='': i+=1
            continue
        out.append(lines[i]); i+=1
    if n!=1: raise RuntimeError(f'{path}: mb/e a method count {n}')
    path.write_text('\n'.join(out)+'\n')


def rewrite_extension_onresume(path: Path) -> None:
    # Preserve the legitimate network DB migration warning, remove trial expiry/status/acquisition behavior.
    text=path.read_text(); lines=text.splitlines(); out=[]; i=0; n=0
    body=f'''.method public onResume(Lnextapp/fx/ui/content/k;)V
    .locals 3
    invoke-static {{p1}}, {HELPER_DESC}->present(Landroid/content/Context;)Z
    move-result v0
    if-eqz v0, :done

    const/4 v0, 0x0
    :try_start_0
    new-instance v1, Lxc/b;
    invoke-direct {{v1, p1}}, Lxc/b;-><init>(Landroid/content/Context;)V
    sget-object v2, Lnd/a;->Z1:Lnd/a;
    invoke-virtual {{v1, v2}}, Lxc/b;->e(Lnd/a;)I
    sget-boolean v1, Lxc/b;->c:Z
    :try_end_0
    .catchall {{:try_start_0 .. :try_end_0}} :catchall_0

    sput-boolean v0, Lxc/b;->c:Z
    if-eqz v1, :done

    const v0, 0x7f10047c
    invoke-virtual {{p1, v0}}, Landroid/content/Context;->getString(I)Ljava/lang/String;
    move-result-object v0
    const v1, 0x7f10047b
    invoke-virtual {{p1, v1}}, Landroid/content/Context;->getString(I)Ljava/lang/String;
    move-result-object v1
    const/4 v2, 0x0
    invoke-static {{p1, v0, v1, v2}}, Lnextapp/fx/plus/ui/media/p;->b(Landroid/content/Context;Ljava/lang/String;Ljava/lang/CharSequence;Landroid/content/Intent;)Lnextapp/fx/plus/ui/media/p;
    return-void

    :catchall_0
    move-exception p1
    sput-boolean v0, Lxc/b;->c:Z
    throw p1

    :done
    return-void
.end method'''
    while i<len(lines):
        if lines[i].startswith('.method public onResume(Lnextapp/fx/ui/content/k;)V'):
            n+=1; out.extend(body.splitlines()); out.append('')
            while i<len(lines) and lines[i] != '.end method': i+=1
            if i<len(lines): i+=1
            while i<len(lines) and lines[i]=='': i+=1
            continue
        out.append(lines[i]); i+=1
    if n!=1: raise RuntimeError(f'{path}: onResume count {n}')
    # Remove assignment of old state-provider helper from static constructor.
    cleaned=[]; i=0
    while i<len(out):
        if i+1 < len(out) and 'sget-object v0, Lnextapp/fx/plus/ui/c;->a:Lhh/e;' in out[i]:
            # walk until sput-object to lh/n->b inclusive (comments/lines allowed)
            j=i
            while j<len(out) and 'sput-object v0, Llh/n;->b:Lhh/e;' not in out[j]: j+=1
            if j>=len(out): raise RuntimeError('could not find legacy state provider assignment end')
            i=j+1; continue
        cleaned.append(out[i]); i+=1
    path.write_text('\n'.join(cleaned)+'\n')


def replace_direct_l_calls(root: Path) -> int:
    n=0
    for p in root.rglob('*.smali'):
        t=p.read_text()
        if 'Llh/n;->l(Landroid/content/Context;)Z' in t:
            c=t.count('Llh/n;->l(Landroid/content/Context;)Z')
            t=t.replace('Llh/n;->l(Landroid/content/Context;)Z', f'{HELPER_DESC}->present(Landroid/content/Context;)Z')
            p.write_text(t); n+=c
    return n


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('decoded', type=Path)
    args=ap.parse_args(); root=args.decoded
    smali=root/'smali'

    helper=smali/'dw/filemanager/core/Companion.smali'
    helper.parent.mkdir(parents=True, exist_ok=True)
    helper.write_text(HELPER)

    # Special mixed/state-display classes first.
    rewrite_plus_home_section(smali/'nextapp/fx/plus/ui/PlusRegistry$PlusHomeSection.smali')
    rewrite_trial_tutorial_helper(smali/'nextapp/fx/plus/ui/k.smali')
    simplify_about_status_string(smali/'mb/e.smali')
    rewrite_extension_onresume(smali/'nextapp/fx/plus/ui/PlusExtension.smali')

    # AboutActivity still contains trial-only presentation and is structurally replaced in Stage 03.
    # Do not partially rewrite its state flow here.
    exclude={
        smali/'nextapp/fx/ui/about/AboutActivity.smali',
        smali/'nextapp/fx/plus/ui/PlusRegistry$PlusHomeSection.smali',
        smali/'nextapp/fx/plus/ui/k.smali',
        smali/'mb/e.smali',
    }
    changed=0
    for p in smali.rglob('*.smali'):
        if p in exclude: continue
        changed += rewrite_simple_j_a(p)

    # All direct old boolean verifier calls become the one helper.
    lcount=replace_direct_l_calls(smali)

    # Remove obsolete side-effect-only state probe in k2/y if still present.
    p=smali/'k2/y.smali'; t=p.read_text()
    t=t.replace('    invoke-static {v0}, Llh/n;->j(Landroid/content/Context;)I\n', '    # removed obsolete capability-state side-effect probe\n')
    p.write_text(t)

    # Keep j only for the old About screen until Stage03; strip trial semantics from it now.
    npath=smali/'lh/n.smali'; t=npath.read_text()
    # l is no longer called; j becomes a temporary adapter only for About, with no state/cache/trial.
    t=remove_method(t, ' static l(Landroid/content/Context;)Z')
    # Replace j method body.
    lines=t.splitlines(); out=[]; i=0; found=0
    while i<len(lines):
        if lines[i].startswith('.method public static j(Landroid/content/Context;)I'):
            found+=1
            out += ['.method public static j(Landroid/content/Context;)I',
                    '    .locals 1',
                    f'    invoke-static {{p0}}, {HELPER_DESC}->present(Landroid/content/Context;)Z',
                    '    move-result p0',
                    '    if-eqz p0, :absent',
                    '    const/4 v0, 0x3',
                    '    return v0',
                    '    :absent',
                    '    const/4 v0, 0x1',
                    '    return v0',
                    '.end method','']
            while i<len(lines) and lines[i] != '.end method': i+=1
            if i<len(lines): i+=1
            while i<len(lines) and lines[i]=='': i+=1
            continue
        out.append(lines[i]); i+=1
    if found!=1: raise RuntimeError('lh/n j method not found')
    t='\n'.join(out)+'\n'
    # Delete obsolete cache/provider fields b/c/d; no surviving legitimate caller should use them.
    t=re.sub(r'^\.field public static b:Lhh/e; = null\n\n?', '', t, flags=re.M)
    t=re.sub(r'^\.field public static c:Z = false\n\n?', '', t, flags=re.M)
    t=re.sub(r'^\.field public static d:I\n\n?', '', t, flags=re.M)
    npath.write_text(t)

    # In About's temporary adapter path, trial predicate d(state) should never report true because j no longer returns 2.
    # Stage03 removes this entire old About implementation.

    # Assertions for this stage.
    corpus='\n'.join(p.read_text(errors='ignore') for p in smali.rglob('*.smali'))
    assert 'Llh/n;->l(Landroid/content/Context;)Z' not in corpus
    assert 'Llh/n;->b:Lhh/e;' not in corpus
    assert 'Llh/n;->c:Z' not in corpus
    assert 'Llh/n;->d:I' not in corpus
    assert f'{HELPER_DESC}->present(Landroid/content/Context;)Z' in corpus
    # All normal state consumers are migrated; only About may reference the temporary j adapter.
    jrefs=[]
    for p in smali.rglob('*.smali'):
        if 'Llh/n;->j(Landroid/content/Context;)I' in p.read_text(errors='ignore'):
            jrefs.append(str(p.relative_to(root)))
    if jrefs != ['smali/nextapp/fx/ui/about/AboutActivity.smali']:
        raise RuntimeError(f'unexpected remaining j refs: {jrefs}')

    print(f'stage02 complete: {changed} state consumers migrated, {lcount} direct verifier calls migrated; remaining j adapter only in AboutActivity')

if __name__=='__main__': main()

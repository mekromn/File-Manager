#!/usr/bin/env python3
from pathlib import Path
import argparse

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args(); root=a.decoded
    auth=root/'smali/dw/filemanager/ext/ui/net/cloud/BoxWebAuthActivity.smali'
    t=auth.read_text()
    old='    const-string v1, "&redirect_uri=https://android.nextapp.com/_boxredirect&state="\n'
    new='    const-string v1, "&state="\n'
    if t.count(old)!=1: raise RuntimeError(f'Box authorize redirect literal count={t.count(old)}')
    auth.write_text(t.replace(old,new,1))

    client=root/'smali/de/d.smali'; t=client.read_text()
    start=t.index('    :pswitch_2\n', t.index('.method public shouldOverrideUrlLoading'))
    end=t.index('    :cond_4\n', start)
    repl='''    :pswitch_2
    if-eqz p2, :cond_4

    check-cast v1, Ldw/filemanager/ext/ui/net/cloud/BoxWebAuthActivity;

    iget-object v0, v1, Ldw/filemanager/ext/ui/net/cloud/BoxWebAuthActivity;->i:Ljava/lang/String;

    invoke-static {p2}, Landroid/net/Uri;->parse(Ljava/lang/String;)Landroid/net/Uri;
    move-result-object p1

    const-string v4, "state"
    invoke-virtual {p1, v4}, Landroid/net/Uri;->getQueryParameter(Ljava/lang/String;)Ljava/lang/String;
    move-result-object v4

    invoke-virtual {v0, v4}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v5
    if-eqz v5, :cond_4

    const-string v4, "code"
    invoke-virtual {p1, v4}, Landroid/net/Uri;->getQueryParameter(Ljava/lang/String;)Ljava/lang/String;
    move-result-object p1
    if-eqz p1, :cond_4

    new-instance p2, Landroid/content/Intent;
    invoke-direct {p2}, Landroid/content/Intent;-><init>()V
    const-string v0, "auth_code"
    invoke-virtual {p2, v0, p1}, Landroid/content/Intent;->putExtra(Ljava/lang/String;Ljava/lang/String;)Landroid/content/Intent;
    invoke-virtual {v1, v3, p2}, Landroid/app/Activity;->setResult(ILandroid/content/Intent;)V
    invoke-virtual {v1}, Landroid/app/Activity;->finish()V
    const/4 v2, 0x1

'''
    client.write_text(t[:start]+repl+t[end:])

    hits=[]
    for sd in root.glob('smali*'):
      for p in sd.rglob('*.smali'):
        txt=p.read_text(errors='ignore')
        if 'android.nextapp.com/_boxredirect' in txt or 'nextapp.com' in txt: hits.append(str(p.relative_to(root)))
    for tree in (root/'res',root/'assets'):
      for p in tree.rglob('*'):
        if not p.is_file(): continue
        try: txt=p.read_text()
        except UnicodeDecodeError: continue
        if 'nextapp.com' in txt: hits.append(str(p.relative_to(root)))
    if hits: raise RuntimeError('vendor endpoint remains: '+str(hits[:10]))
    if '&redirect_uri=' in auth.read_text(): raise RuntimeError('Box authorize still passes redirect_uri')
    print('stage09b removed Box vendor redirect literal; callback now matches state+code generically')
if __name__=='__main__':main()

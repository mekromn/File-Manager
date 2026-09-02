#!/usr/bin/env python3
from pathlib import Path
import argparse,re
from collections import defaultdict

URL_RE=re.compile(r'https?://[^\s"\'<>\\]+',re.I)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('decoded',type=Path); a=ap.parse_args(); root=a.decoded
    hits=defaultdict(set)
    for base in [root/'smali',root/'res',root/'assets']:
        if not base.exists(): continue
        for p in base.rglob('*'):
            if not p.is_file(): continue
            try: txt=p.read_text(errors='ignore')
            except Exception: continue
            for m in URL_RE.finditer(txt):
                url=m.group(0).rstrip('),.;]')
                hits[url].add(str(p.relative_to(root)))

    print(f'stage10a network inventory: {len(hits)} unique HTTP(S) literal(s)')
    for url in sorted(hits,key=str.lower):
        paths=sorted(hits[url])
        shown=', '.join(paths[:5])
        suffix='' if len(paths)<=5 else f' (+{len(paths)-5} more)'
        print(f'URL {url} :: {shown}{suffix}')

    banned_tokens=('nextapp.com','firebaseio.com','firebaseinstallations','google-analytics.com','app-measurement.com','crashlytics','doubleclick.net')
    bad=[]
    for url,paths in hits.items():
        low=url.lower()
        if any(tok in low for tok in banned_tokens): bad.append((url,sorted(paths)))
    if bad:
        for url,paths in bad: print('BANNED',url,'::',', '.join(paths[:8]))
        raise RuntimeError(f'{len(bad)} banned telemetry/vendor URL literal(s) remain')

    print('stage10a banned vendor/telemetry URL scan passed; inventory emitted for classification')

if __name__=='__main__': main()

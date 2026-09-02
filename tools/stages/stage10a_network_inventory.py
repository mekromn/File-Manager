#!/usr/bin/env python3
from pathlib import Path
import argparse,re
from collections import defaultdict

URL_RE=re.compile(r'https?://[^\s"\'<>\\]+',re.I)

# Executable/user-facing network features we intentionally preserve.
RUNTIME_PREFIXES=(
    'http://127.0.0.1:',                              # local Web Access
    'https://accounts.google.com/o/oauth2/',          # Google OAuth
    'https://www.googleapis.com/auth/drive',          # Google Drive scope
    'https://www.googleapis.com/drive/',              # Google Drive API
    'https://www.googleapis.com/oauth2/',             # Google OAuth token
    'https://www.googleapis.com/upload/drive/',       # Google Drive uploads
    'https://api.box.com/2.0/',                       # Box API
    'https://upload.box.com/api/2.0/',                # Box uploads
    'https://www.box.com/api/oauth2/',                # Box OAuth
    'https://api.sugarsync.com/',                     # SugarSync
    'https://f-droid.org/packages/',                  # user-invoked package page
    'https://graph.microsoft.com',                    # OneDrive / Graph
    'https://login.microsoftonline.com/common/oauth2/', # Microsoft OAuth
)

# Literals that are namespaces, parser placeholders, bundled-library help/error
# links, or compiler provenance. They are not application outbound endpoints.
DATA_PREFIXES=(
    'http://localhost',
    'http://commons.apache.org/proper/commons-compress/limitations.html#7Z',
    'http://ns.adobe.com/xap/1.0/',
    'http://schemas.android.com/apk/res-auto',
    'http://schemas.android.com/apk/res/android',
    'http://www.slf4j.org/codes.html#',
    'http://www.w3.org/1999/xhtml',
    'http://www.w3.org/ns/ttml#parameter',
    'http://www.w3.org/TR/xhtml1/DTD/xhtml1-',
    'https://android.googlesource.com/toolchain/llvm-project',
    'https://source.android.com/devices/tech/debug/tagged-pointers',
)

BANNED_TOKENS=(
    'nextapp.com','firebaseio.com','firebaseinstallations',
    'google-analytics.com','app-measurement.com','crashlytics',
    'doubleclick.net','googlesyndication.com','googleadservices.com',
)

def classify(url):
    if any(url.startswith(p) for p in RUNTIME_PREFIXES): return 'runtime'
    if any(url.startswith(p) for p in DATA_PREFIXES): return 'data'
    return None

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

    rows=[]; bad=[]; unknown=[]
    for url in sorted(hits,key=str.lower):
        paths=sorted(hits[url]); low=url.lower(); cls=classify(url)
        if any(tok in low for tok in BANNED_TOKENS): bad.append((url,paths))
        if cls is None: unknown.append((url,paths))
        rows.append((cls or 'UNKNOWN',url,paths))

    report=root.parent/'stage10-network-inventory.txt'
    with report.open('w') as f:
        f.write(f'unique_urls={len(rows)}\n')
        f.write(f'runtime_urls={sum(1 for r in rows if r[0]=="runtime")}\n')
        f.write(f'data_urls={sum(1 for r in rows if r[0]=="data")}\n')
        f.write(f'unknown_urls={len(unknown)}\n')
        for cls,url,paths in rows:
            f.write(f'{cls.upper()} {url} :: {", ".join(paths)}\n')

    print(f'stage10a network inventory: {len(rows)} unique HTTP(S) literal(s)')
    for cls,url,paths in rows:
        shown=', '.join(paths[:5]); suffix='' if len(paths)<=5 else f' (+{len(paths)-5} more)'
        print(f'{cls.upper()} {url} :: {shown}{suffix}')

    if bad:
        for url,paths in bad: print('BANNED',url,'::',', '.join(paths[:8]))
        raise RuntimeError(f'{len(bad)} banned telemetry/vendor URL literal(s) remain')
    if unknown:
        for url,paths in unknown: print('UNCLASSIFIED',url,'::',', '.join(paths[:8]))
        raise RuntimeError(f'{len(unknown)} unclassified HTTP(S) literal(s) remain')

    print('stage10a network allowlist passed: every HTTP(S) literal is explicitly classified')

if __name__=='__main__': main()

#!/usr/bin/env python3
from pathlib import Path
import argparse

# Host-build compatibility repair for Stage21m. Android's public Os API does not
# expose realpath(String) in the compile SDK used by the replay, even though the
# filesystem service needs canonical-path resolution. Run canonicalization inside
# the Shizuku UserService with java.io.File.getCanonicalPath(), which executes
# under the UserService's shell/root identity and is public Android/Java API.

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('decoded', type=Path)  # sequencing compatibility; intentionally unused
    ap.parse_args()

    p = Path('tools/stages/stage21m_shizuku_preflight_and_trace.py')
    t = p.read_text()
    old = 'String canonical=Os.realpath(path);'
    new = 'String canonical=new File(path).getCanonicalPath();'
    n = t.count(old)
    if n == 1:
        p.write_text(t.replace(old, new, 1))
    elif new not in t:
        raise RuntimeError('Stage21m REALPATH source anchor changed: '+str(n))
    print('stage21lzz: Stage21m canonical path now uses File.getCanonicalPath inside Shizuku UserService')

if __name__ == '__main__':
    main()

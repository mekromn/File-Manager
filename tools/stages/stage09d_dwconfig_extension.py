#!/usr/bin/env python3
from pathlib import Path
import argparse
import re

TOKEN_RE = re.compile(br'fxconfig', re.IGNORECASE)
NAME_RE = re.compile(r'fxconfig', re.IGNORECASE)


def app_files(root: Path):
    for p in root.rglob('*'):
        if not p.is_file():
            continue
        rel = p.relative_to(root)
        # Apktool's original/ tree is immutable source/signature metadata and is not
        # part of the transformed implementation. Do not mutate it.
        if rel.parts and rel.parts[0] == 'original':
            continue
        yield p


def replace_contents(root: Path):
    changed = []
    total = 0
    for p in app_files(root):
        data = p.read_bytes()
        n = len(TOKEN_RE.findall(data))
        if not n:
            continue
        new = TOKEN_RE.sub(b'dwconfig', data)
        if len(new) != len(data):
            raise RuntimeError(f'length changed while migrating token in {p}')
        p.write_bytes(new)
        total += n
        changed.append((str(p.relative_to(root)), n))
    return total, changed


def rename_paths(root: Path):
    renamed = []
    # Re-scan after every rename so parent/child path changes cannot invalidate a
    # cached Path object. Deepest matching path is always renamed first.
    while True:
        candidates = []
        for p in root.rglob('*'):
            rel = p.relative_to(root)
            if rel.parts and rel.parts[0] == 'original':
                continue
            if NAME_RE.search(p.name):
                candidates.append(p)
        if not candidates:
            break
        p = max(candidates, key=lambda x: len(x.relative_to(root).parts))
        new_name = NAME_RE.sub('dwconfig', p.name)
        dst = p.with_name(new_name)
        if dst.exists():
            raise RuntimeError(f'cannot rename {p}: destination already exists: {dst}')
        before = str(p.relative_to(root))
        p.rename(dst)
        renamed.append((before, str(dst.relative_to(root))))
    return renamed


def find_old(root: Path):
    hits = []
    for p in app_files(root):
        data = p.read_bytes()
        if TOKEN_RE.search(data):
            hits.append(str(p.relative_to(root)))
    for p in root.rglob('*'):
        rel = p.relative_to(root)
        if rel.parts and rel.parts[0] == 'original':
            continue
        if NAME_RE.search(p.name):
            hits.append(str(rel))
    return sorted(set(hits))


def count_new(root: Path):
    count = 0
    rx = re.compile(br'dwconfig', re.IGNORECASE)
    for p in app_files(root):
        count += len(rx.findall(p.read_bytes()))
    return count


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('decoded', type=Path)
    args = ap.parse_args()
    root = args.decoded

    total, changed = replace_contents(root)
    renamed = rename_paths(root)

    if total == 0 and not renamed:
        raise RuntimeError('expected Stage 08 .fxconfig compatibility token was not found')

    leftovers = find_old(root)
    if leftovers:
        raise RuntimeError('legacy fxconfig token/path remains: ' + str(leftovers[:20]))

    new_count = count_new(root)
    if new_count < total:
        raise RuntimeError(f'dwconfig verification count too small: {new_count} < {total}')

    print(f'stage09d migrated fxconfig -> dwconfig: {total} content occurrence(s), {len(renamed)} path rename(s)')
    for path, n in changed:
        print(f'  content {n:3d}  {path}')
    for before, after in renamed:
        print(f'  rename       {before} -> {after}')


if __name__ == '__main__':
    main()

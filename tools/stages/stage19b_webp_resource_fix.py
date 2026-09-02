#!/usr/bin/env python3
from pathlib import Path
import argparse, shutil

# aapt2 37.0.0 reproducibly segfaults while crunching the 288px Dark Blue PNG,
# even after a pixel-identical conservative RGBA re-encode. Keep the exact same
# drawable resource basename but package those pixels as lossless WebP so the PNG
# cruncher is bypassed. All iconset XML continues to reference
# @drawable/id288_folder_dw_dark_blue unchanged.

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('decoded', type=Path)
    a = ap.parse_args()
    root = a.decoded
    repo = Path(__file__).resolve().parents[2]

    src = repo / 'assets/folder-palette/id288_folder_dw_dark_blue.webp'
    dst_dir = root / 'res/drawable-nodpi'
    png = dst_dir / 'id288_folder_dw_dark_blue.png'
    webp = dst_dir / 'id288_folder_dw_dark_blue.webp'

    if not src.exists():
        raise RuntimeError('missing Stage19 lossless WebP asset: ' + str(src))
    if png.exists():
        png.unlink()
    shutil.copy2(src, webp)

    if png.exists() or not webp.exists():
        raise RuntimeError('Stage19 WebP resource substitution failed')
    print('stage19b replaced aapt2-hostile 288px Dark Blue PNG with lossless WebP')

if __name__ == '__main__':
    main()

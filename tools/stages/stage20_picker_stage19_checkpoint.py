#!/usr/bin/env python3
from pathlib import Path
import argparse, re

VC = '9109020'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('decoded', type=Path)
    a = ap.parse_args()
    root = a.decoded

    # This stage deliberately adds no runtime behavior. It is the sequencing guard
    # for the first build that combines the validated Stage19 palette with the
    # in-progress Stage13 DW File Chooser panel.
    required = [
        root / 'smali/dw/filemanager/ui/filechooser/PickerSort.smali',
        root / 'smali/dw/filemanager/ui/filechooser/PickerPanelMenu.smali',
        root / 'res/xml/iconset_dynamic_dark_blue.xml',
        root / 'res/xml/iconset_dynamic_white.xml',
    ]
    missing = [str(p.relative_to(root)) for p in required if not p.exists()]
    if missing:
        raise RuntimeError('Stage20 reconciliation prerequisites missing: ' + ', '.join(missing))

    y = root / 'apktool.yml'
    t = y.read_text()
    t, n = re.subn(r'(versionCode:\s*)[^\n]+', r'\g<1>' + VC, t, count=1)
    if n != 1:
        raise RuntimeError('versionCode not found')
    y.write_text(t)

    print('stage20 Stage13+Stage19 reconciliation checkpoint; vc=' + VC)


if __name__ == '__main__':
    main()

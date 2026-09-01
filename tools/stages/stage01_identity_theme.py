#!/usr/bin/env python3
from __future__ import annotations
import argparse, re
from pathlib import Path

NEW_PACKAGE = "com.mekromn.dwfilemanager"

DARK = '''<?xml version="1.0" encoding="utf-8"?>
<theme>
    <option name="light" value="false" />
    <option name="translucent" value="true" />
    <color name="actionBarBackground" value="#ff111820" />
    <color name="actionBarBackgroundOpaque" value="#ff111820" />
    <color name="drawerHeaderBackground" value="#e6161c24" />
    <color name="menuBackground" value="#e6161c24" />
    <color name="windowBackground" value="#a611171e" />
    <color name="contentBackground" value="#d9141a22" />
    <color name="headerForeground" value="@color/theme_trans_dark_header_fg" />
    <color name="headerBackground" value="#e61a2230" />
    <color name="headerBackgroundInactive" value="#b3151a20" />
    <option name="headerLowContrastIcons" value="false" />
    <option name="headerBackgroundLight" value="false" />
    <color name="specialTextColor" value="#ff4285f4" />
    <color name="defaultTrimBase" value="#ff202a36" />
    <color name="defaultTrimAccent" value="#ff4285f4" />
    <color name="progressComplete" value="#ff4285f4" />
    <color name="progressRemaining" value="#663a4656" />
    <color name="boxBackground" value="#b31b2430" />
    <color name="boxPressedBackground" value="#664285f4" />
    <color name="boxEffectOnlyPressedBackground" value="#664285f4" />
    <color name="boxFlatPressedBackground" value="#554285f4" />
    <color name="selectionBackground" value="#554285f4" />
    <color name="selectionPressedBackground" value="#774285f4" />
    <color name="editorBackground" value="#f20d1117" />
    <color name="editorText" value="@color/editor_blue_white_fg_text" />
    <color name="editorIndex" value="@color/editor_blue_white_fg_index" />
    <color name="editorHex" value="@color/editor_blue_white_fg_hex" />
</theme>\n'''

AMOLED = '''<?xml version="1.0" encoding="utf-8"?>
<theme>
    <option name="light" value="false" />
    <option name="translucent" value="true" />
    <color name="actionBarBackground" value="#ff000000" />
    <color name="actionBarBackgroundOpaque" value="#ff000000" />
    <color name="drawerHeaderBackground" value="#e6000000" />
    <color name="menuBackground" value="#e6000000" />
    <color name="windowBackground" value="#99000000" />
    <color name="contentBackground" value="#ff000000" />
    <color name="headerForeground" value="@color/theme_trans_dark_header_fg" />
    <color name="headerBackground" value="#e6000000" />
    <color name="headerBackgroundInactive" value="#b3000000" />
    <option name="headerLowContrastIcons" value="false" />
    <option name="headerBackgroundLight" value="false" />
    <color name="specialTextColor" value="#ff4285f4" />
    <color name="defaultTrimBase" value="#ff000000" />
    <color name="defaultTrimAccent" value="#ff4285f4" />
    <color name="progressComplete" value="#ff4285f4" />
    <color name="progressRemaining" value="#66333333" />
    <color name="boxBackground" value="#b3000000" />
    <color name="boxPressedBackground" value="#664285f4" />
    <color name="boxEffectOnlyPressedBackground" value="#664285f4" />
    <color name="boxFlatPressedBackground" value="#554285f4" />
    <color name="selectionBackground" value="#554285f4" />
    <color name="selectionPressedBackground" value="#774285f4" />
    <color name="editorBackground" value="#ff000000" />
    <color name="editorText" value="@color/editor_blue_white_fg_text" />
    <color name="editorIndex" value="@color/editor_blue_white_fg_index" />
    <color name="editorHex" value="@color/editor_blue_white_fg_hex" />
</theme>\n'''


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("decoded", type=Path)
    ap.add_argument("--version-code", default="9109000")
    args = ap.parse_args()
    root = args.decoded

    yml = root / "apktool.yml"
    text = yml.read_text()
    text = re.sub(r"(targetSdkVersion:\s*)\d+", r"\g<1>34", text)
    text = re.sub(r"(versionCode:\s*)\d+", r"\g<1>" + args.version_code, text)
    yml.write_text(text)

    manifest = root / "AndroidManifest.xml"
    text = manifest.read_text()
    text = text.replace(' android:sharedUserId="nextapp.fx"', '')
    text = text.replace('package="nextapp.fx"', f'package="{NEW_PACKAGE}"')
    text = text.replace(
        "nextapp.fx.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION",
        f"{NEW_PACKAGE}.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION",
    )
    text = text.replace(
        'android:authorities="nextapp.fx.TemporaryFileProvider"',
        f'android:authorities="{NEW_PACKAGE}.TemporaryFileProvider"',
    )
    text = text.replace(
        'android:authorities="nextapp.fx.FileProvider"',
        f'android:authorities="{NEW_PACKAGE}.FileProvider"',
    )
    text = text.replace(
        'android:authorities="nextapp.fx.androidx-startup"',
        f'android:authorities="{NEW_PACKAGE}.androidx-startup"',
    )
    manifest.write_text(text)

    strings = root / "res/values/strings.xml"
    text = strings.read_text()
    text = re.sub(
        r'(<string name="app_name">).*?(</string>)',
        r"\1DW File Manager\2",
        text,
        count=1,
    )
    strings.write_text(text)

    pref = root / "res/xml/pref_developer.xml"
    lines = [line for line in pref.read_text().splitlines() if "googleIabDisable" not in line]
    pref.write_text("\n".join(lines) + "\n")

    write(root / "res/xml/theme_dw_dark_glass.xml", DARK)
    write(root / "res/xml/theme_dw_amoled_black_transparent.xml", AMOLED)

    module = root / "res/xml/nextapp_fx_module.xml"
    text = module.read_text()
    marker = '        <theme color="#263238" id="translucent_dark" resource="@xml/theme_translucent_dark" translucent="true" />'
    addition = (
        marker
        + '\n        <theme color="#ff111820" id="dw_dark_glass" resource="@xml/theme_dw_dark_glass" translucent="true" />'
        + '\n        <theme color="#ff000000" id="dw_amoled_black_transparent" resource="@xml/theme_dw_amoled_black_transparent" translucent="true" />'
    )
    if 'id="dw_dark_glass"' not in text:
        if marker not in text:
            raise SystemExit("theme registration marker not found")
        text = text.replace(marker, addition)
    module.write_text(text)

    assert "googleIabDisable" not in pref.read_text()
    assert '<string name="app_name">DW File Manager</string>' in strings.read_text()
    assert f'package="{NEW_PACKAGE}"' in manifest.read_text()
    assert 'android:sharedUserId="nextapp.fx"' not in manifest.read_text()
    assert 'android:name="nextapp.fx.rk"' in manifest.read_text()
    print("stage01 identity/theme transformation complete")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Bootstrap a deterministic DW File Manager reverse-engineering workspace.

This script deliberately does not patch the APK. It verifies the immutable inputs,
extracts the pinned toolchains, and decodes the untouched 9.1.0.8 base plus the
known-working 9108006 reference side-by-side.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

BASE_SHA256 = "19af15780d0fc65242ed3f97d6397adfbb0055225cef84ccbc2c777b906bf2c6"
REFERENCE_SHA256 = "0f160cf7bf43982303ccf752db1b2c3bfd8607edb70961b2df9a7ec04dfa175c"
APKTOOL_ZIP_SHA256 = "145c372cc2c9cfd3a63d8addf043b08a78aa78071ce2b467b0c3e63cadd3379d"
DEX_TOOLCHAIN_ZIP_SHA256 = "6de1696514ca9c22a60a0818edfea7584232c35fa896c40c82b0aa065d09db11"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def require_hash(path: Path, expected: str, label: str) -> None:
    actual = sha256(path)
    if actual != expected:
        raise SystemExit(f"{label} SHA-256 mismatch: {actual} != {expected}")
    print(f"OK {label}: {actual}")


def extract_single_zip(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    with zipfile.ZipFile(src) as zf:
        zf.extractall(dst)


def find_one(root: Path, name: str) -> Path:
    hits = list(root.rglob(name))
    if len(hits) != 1:
        raise SystemExit(f"Expected exactly one {name} below {root}, found {len(hits)}")
    return hits[0]


def decode(apktool: Path, apk: Path, out: Path) -> None:
    if out.exists():
        shutil.rmtree(out)
    subprocess.run(
        ["java", "-jar", str(apktool), "d", "-f", "-o", str(out), str(apk)],
        check=True,
    )


def smali_count(decoded: Path) -> int:
    return sum(1 for _ in decoded.rglob("*.smali"))


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--base", required=True, type=Path)
    p.add_argument("--reference", required=True, type=Path)
    p.add_argument("--apktool-zip", required=True, type=Path)
    p.add_argument("--dex-toolchain-zip", required=True, type=Path)
    p.add_argument("--workspace", required=True, type=Path)
    args = p.parse_args()

    require_hash(args.base, BASE_SHA256, "canonical FX 9.1.0.8 base")
    require_hash(args.reference, REFERENCE_SHA256, "known-working 9108006 reference")
    require_hash(args.apktool_zip, APKTOOL_ZIP_SHA256, "pinned Apktool artifact")
    require_hash(args.dex_toolchain_zip, DEX_TOOLCHAIN_ZIP_SHA256, "pinned smali artifact")

    work = args.workspace.resolve()
    tools = work / "tools"
    extract_single_zip(args.apktool_zip, tools / "apktool")
    extract_single_zip(args.dex_toolchain_zip, tools / "dex")

    apktool = find_one(tools / "apktool", "apktool.jar")
    baksmali = find_one(tools / "dex", "baksmali.jar")
    smali = find_one(tools / "dex", "smali.jar")
    print(f"Apktool: {apktool}")
    print(f"baksmali: {baksmali}")
    print(f"smali: {smali}")

    base_out = work / "base" / "decoded"
    ref_out = work / "reference" / "decoded"
    decode(apktool, args.base, base_out)
    decode(apktool, args.reference, ref_out)

    base_count = smali_count(base_out)
    ref_count = smali_count(ref_out)
    print(f"Base smali classes: {base_count}")
    print(f"Reference smali classes: {ref_count}")
    if base_count != 12079 or ref_count != 12079:
        raise SystemExit("Unexpected class count; refuse to continue from an unknown input")

    print("Workspace bootstrap complete.")


if __name__ == "__main__":
    main()

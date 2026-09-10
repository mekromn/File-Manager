#!/usr/bin/env python3
"""Reproduce the exact V5 classes2.dex from the verified V4 classes2.dex.

This is deliberately a fixed-layout DEX patch. It replaces the blocking
Process.waitFor() sequence inside DwFeedRegistry.launchViaShizuku() with an
immediate null return plus NOP padding, then recalculates the DEX signature and
checksum. It does not change the code-item length or any downstream offsets.
"""

from pathlib import Path
import argparse
import hashlib
import struct
import zlib

V4_SHA256 = "64d2678c1cd7cedbeadd2fa0a1e8165b311a4d3bee28ab7371ffbb41db1d698a"
V5_SHA256 = "0dd577791c1aea092eebcaeb25b25cd30b39bcfbe31d810392a2c399fbab0a15"
CODE_OFF = 0x2780
PATCH_UNIT = 52
# const/4 v4(p0), #0; return-object v4(p0); NOP x4
PATCH_WORDS = (0x0412, 0x0411, 0x0000, 0x0000, 0x0000, 0x0000)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()

    original = args.input.read_bytes()
    if sha256(original) != V4_SHA256:
        raise SystemExit("refusing unknown classes2.dex: V4 SHA-256 mismatch")

    dex = bytearray(original)
    insns_off = CODE_OFF + 16
    for index, word in enumerate(PATCH_WORDS):
        struct.pack_into("<H", dex, insns_off + 2 * (PATCH_UNIT + index), word)

    # DEX signature: SHA-1 of bytes from file_size field (offset 32) onward.
    dex[12:32] = hashlib.sha1(dex[32:]).digest()
    # DEX checksum: Adler32 of bytes from signature field (offset 12) onward.
    struct.pack_into("<I", dex, 8, zlib.adler32(dex[12:]) & 0xFFFFFFFF)

    result = bytes(dex)
    if sha256(result) != V5_SHA256:
        raise SystemExit("internal error: generated V5 SHA-256 mismatch")

    args.output.write_bytes(result)
    print(V5_SHA256)


if __name__ == "__main__":
    main()

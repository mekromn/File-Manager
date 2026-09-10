#!/usr/bin/env python3
"""Exact V5 -> V6 DW dual-feed verifier repair.

The V5 activity-launch catch handler stored its Throwable in p0/v9, the same
register that holds the String session id on the normal path. A successful
Shizuku fallback branches to :launch_scheduled, whose synthetic-lambda
constructor requires that register to still be String. Android's verifier
therefore merges Throwable/String to Object and rejects DwFeedRegistry.create.

V6 changes only register operands in that catch handler:
  move-exception p0  -> move-exception v0
  instance-of p1,p0 -> instance-of p1,v0
  describe(p0)      -> describe(v0)  (two activity-launch error paths)

Instruction widths, branch targets, catch ranges, code item sizes and all other
DEX offsets remain unchanged. DEX SHA-1 and Adler32 fields are recalculated.
"""
from pathlib import Path
import argparse, hashlib, struct, zlib

V5_SHA256 = "0dd577791c1aea092eebcaeb25b25cd30b39bcfbe31d810392a2c399fbab0a15"
V6_SHA256 = "f050568b6d3267b8b1ca25a10167676a48fda7e6f746ef495cf4665bb60b0372"

PATCHES = {
    0x23C5: (0x09, 0x00),  # move-exception v9 -> v0
    0x23C7: (0x9A, 0x0A),  # instance-of v10,v9 -> v10,v0
    0x23EC: (0x09, 0x00),  # first describe() argument v9 -> v0
    0x2428: (0x09, 0x00),  # second describe() argument v9 -> v0
}

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("input", type=Path)
    ap.add_argument("output", type=Path)
    ns=ap.parse_args()
    original=ns.input.read_bytes()
    if sha256(original) != V5_SHA256:
        raise SystemExit("refusing unknown input: V5 classes2.dex SHA-256 mismatch")
    dex=bytearray(original)
    for off,(old,new) in PATCHES.items():
        if dex[off] != old:
            raise SystemExit(f"byte guard failed at 0x{off:x}: got 0x{dex[off]:02x}")
        dex[off]=new
    dex[12:32]=hashlib.sha1(dex[32:]).digest()
    struct.pack_into("<I", dex, 8, zlib.adler32(dex[12:]) & 0xffffffff)
    out=bytes(dex)
    if sha256(out) != V6_SHA256:
        raise SystemExit("generated V6 SHA-256 mismatch")
    ns.output.write_bytes(out)
    print(V6_SHA256)

if __name__ == "__main__":
    main()

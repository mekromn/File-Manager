#!/usr/bin/env python3
"""Structural sanity checks for DW File Manager rebuild checkpoints.

This intentionally focuses on proving absence/presence in decoded source trees.
It does not substitute for DEX-table parsing, APK signing verification, launch tests,
or the final release acceptance audit in docs/CORE_REWORK_REQUIREMENTS.md.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

BANNED_APP_TERMS = (
    "nextapp.fx.plus",
    "nextapp.fx.iab",
    "dw.filemanager.plus",
    "UpdateActivity",
    "UpdateHomeItem",
    "trialPlusExpiration",
    "state_trial",
    "googleIabDisable",
    "IAB internal error",
    "Purchase not available",
    "Get FX Plus",
)

ALLOWED_COMPANION_LITERAL = "nextapp.fx.rk"


def all_text_files(root: Path):
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in {
            ".smali", ".xml", ".txt", ".html", ".htm", ".js", ".json",
            ".properties", ".yml", ".yaml", ".md"
        }:
            yield p


def scan(decoded: Path) -> dict:
    files = list(all_text_files(decoded))
    smali_files = [p for p in files if p.suffix == ".smali"]
    hits = {term: [] for term in BANNED_APP_TERMS}
    companion_hits = []
    vendor_namespace_hits = []

    for p in files:
        try:
            text = p.read_text(errors="ignore")
        except OSError:
            continue
        rel = str(p.relative_to(decoded))
        low = text.lower()
        for term in BANNED_APP_TERMS:
            if term.lower() in low:
                hits[term].append(rel)
        if ALLOWED_COMPANION_LITERAL in text:
            companion_hits.append(rel)
        if "Lnextapp/" in text or "nextapp.fx" in text:
            vendor_namespace_hits.append(rel)

    return {
        "decoded": str(decoded),
        "smali_class_files": len(smali_files),
        "banned_term_hits": {k: v for k, v in hits.items() if v},
        "companion_literal_files": companion_hits,
        "vendor_namespace_files": vendor_namespace_hits,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("decoded", type=Path)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    result = scan(args.decoded.resolve())

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return

    print(f"Decoded tree: {result['decoded']}")
    print(f"Smali class files: {result['smali_class_files']}")
    if result["banned_term_hits"]:
        print("BANNED APP TERM HITS:")
        for term, paths in result["banned_term_hits"].items():
            print(f"  {term}: {len(paths)} files")
            for path in paths[:20]:
                print(f"    {path}")
    else:
        print("No configured banned app-term hits.")

    print(f"Companion literal appears in {len(result['companion_literal_files'])} files")
    for path in result["companion_literal_files"]:
        print(f"  companion: {path}")

    print(f"Vendor namespace/identity appears in {len(result['vendor_namespace_files'])} files")


if __name__ == "__main__":
    main()

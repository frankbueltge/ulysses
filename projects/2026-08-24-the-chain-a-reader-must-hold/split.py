#!/usr/bin/env python3
"""Blind split of the amendment chains, fixed before any instruction is read.

The unit of replay is a CHAIN: one base act plus every act in the 151-act corpus of
2026-08-21 that amends it. The split rule below is mechanical and is fixed in
PREREGISTRATION.md §2 before this file was run for the first time.

Rule: base acts sorted by CELEX ascending; every 3rd (index 0, 3, 6, …) to DEVELOPMENT,
the rest HELD OUT. The parser's vocabulary is built by reading DEVELOPMENT chains and
only those. Standard library only.
"""

import json
import pathlib
import re
import sys
import tarfile

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE.parent / "2026-08-21-the-citation-that-stopped"
CORPUS_TGZ = SRC / "corpus.tar.gz"
MANIFEST = SRC / "manifest.json"

BASE_RE = re.compile(r"(?:Implementing\s+)?(?:Decision|Regulation)\s*\(EU\)\s*(\d{4})/(\d+)")


def corpus_text(name: str, tf: tarfile.TarFile) -> str:
    raw = tf.extractfile(f"corpus/{name}.html").read().decode("utf-8", errors="replace")
    raw = re.sub(r"(?is)<(script|style).*?</\1>", " ", raw)
    txt = re.sub(r"<[^>]+>", " ", raw).replace("\xa0", " ").replace("‑", "-")
    return re.sub(r"\s+", " ", txt)


def build() -> dict:
    man = json.loads(MANIFEST.read_text())
    acts = {a["celex"]: a for a in man["acts"]}
    chains: dict[str, set[str]] = {}
    with tarfile.open(CORPUS_TGZ) as tf:
        for celex in sorted(acts, key=lambda c: (acts[c]["date"], c)):
            txt = corpus_text(celex, tf)
            head = txt[:4000]
            if " is amended as follows" not in txt and "amending" not in acts[celex]["title"].lower():
                continue
            # the base act is the one named in the amending formula, not anywhere in the text
            m = re.search(r"([A-Z][^.]{0,120}?)\s+is amended as follows", txt)
            cands = []
            if m:
                cands = BASE_RE.findall(m.group(0))
            if not cands:
                cands = BASE_RE.findall(head)
            for y, n in cands:
                b = f"3{y}D{int(n):04d}"
                if b in acts and b != celex:
                    chains.setdefault(b, set()).add(celex)
                    break
    bases = sorted(chains)
    dev = {b for i, b in enumerate(bases) if i % 3 == 0}
    return {
        "rule": "base acts sorted by CELEX ascending; every 3rd (0-indexed) to development",
        "n_base_acts": len(bases),
        "development": sorted(dev),
        "held_out": [b for b in bases if b not in dev],
        "chains": {b: sorted(chains[b]) for b in bases},
    }


if __name__ == "__main__":
    out = build()
    (HERE / "split.json").write_text(json.dumps(out, indent=1) + "\n")
    print(f"base acts: {out['n_base_acts']}  development: {len(out['development'])}  "
          f"held out: {len(out['held_out'])}", file=sys.stderr)

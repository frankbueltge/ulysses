"""POST-HOC, 2026-08-23. Not pre-registered, and it exists to attack the night's headline.

A deletion of row N followed by an insertion of row "Na" in the same act is an EDITION
UPDATE: the standard is effectively named, by the incoming row. A deletion with no matching
"Na" is an UNPAIRED REMOVAL and names nothing anywhere in the act. W2 counts both. If the
corpus were mostly paired updates, "the Journal never prints what it deletes" would be true
of the instruction and misleading about the act, so the split is measured here and published
whichever way it falls.
"""
import json, pathlib, re, sys
HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE.parent / "2026-08-21-the-citation-that-stopped"
sys.path.insert(0, str(SRC)); sys.path.insert(0, str(HERE))
from census import text_of  # noqa: E402
from split import load, split  # noqa: E402
from removals import read_act  # noqa: E402
from recover import numbers_of, ROW_RE  # noqa: E402

INSERTED_RE = re.compile(r"[‘'\"]?(\d+[a-z])\.\s+EN\s")


def main() -> None:
    man = json.loads((SRC / "manifest.json").read_text())
    corpus = SRC / "corpus"
    _, held_meta = split(man["acts"])
    held = [read_act(a, corpus) for a in held_meta]

    paired = unpaired = 0
    unpaired_acts, examples = set(), []
    for a in held:
        text = text_of(corpus / f"{a['celex']}.html")
        inserted = {m.group(1) for m in INSERTED_RE.finditer(text)}
        letters = {re.sub(r"\D", "", s) for s in inserted}
        for ins in a["instructions"]:
            if ins["kind"] != "DELETION" or not ins["number_only"]:
                continue
            for n in numbers_of(ins):
                bare = re.sub(r"\D", "", n)
                if bare in letters:
                    paired += 1
                else:
                    unpaired += 1
                    unpaired_acts.add(a["celex"])
                    if len(examples) < 12:
                        examples.append({"act": a["celex"], "date": a["date"], "row": n})
    total = paired + unpaired
    out = {
        "note": "POST-HOC. A deletion is PAIRED when the same act inserts a row with the same "
                "number plus a letter suffix (row 14 deleted, row 14a inserted) — an edition "
                "update, in which the standard is named by the incoming row.",
        "row_numbers_deleted": total,
        "paired_edition_update": paired,
        "unpaired_removal": unpaired,
        "share_unpaired": unpaired / total if total else None,
        "acts_with_an_unpaired_removal": len(unpaired_acts),
        "examples": examples,
    }
    (HERE / "pairing.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"deleted row numbers {total}: paired edition update {paired}, "
          f"unpaired removal {unpaired} ({out['share_unpaired']:.3f})")
    print("acts with at least one unpaired removal:", len(unpaired_acts))


if __name__ == "__main__":
    main()

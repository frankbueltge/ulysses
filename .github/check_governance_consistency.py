#!/usr/bin/env python3
"""Does this repository's governance still agree with itself?

Why this exists. On 2026-08-01 the practice brought a protocol proposal to Frank rather than
amending the protocol, reasoning "protocol amendment is human-only (§2, standing delegation
§2)". The reasoning was correct against the document it cited — and the document was stale:
`PROTOCOL.md` had carried the self-development clause since 2026-08-02, and the delegation
still read `protocol_amendment: human_only` and still named the protocol as v4, nine days
after v5 was adopted. So a request travelled, a human read it, a session was spent, and the
answer was "you already may".

That class of cost is a test, not a request. Three agreements are checked:

  1. The protocol VERSION the delegation names is the version the protocol carries.
  2. The AMENDMENT AUTHORITY the delegation grants does not contradict the protocol's own
     self-development clause.
  3. Every path the delegation lists as auto-land-eligible actually appears in the
     allowlist the auto-land workflow ENFORCES — the workflow carries its own copy of §4
     by hand, and a hand-copied rule is a rule waiting to drift.

Exit 1 on any disagreement, so the scheduled run turns red and the drift shows up as a status
rather than as a letter someone has to read. It never edits anything: which document is wrong
is a judgement, and the two candidates are rarely equally wrong.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROTOCOL = ROOT / "PROTOCOL.md"
DELEGATION = ROOT / "governance" / "STANDING-DELEGATION.md"
WORKFLOW = ROOT / ".github" / "workflows" / "research-auto-land.yml"

problems: list[str] = []
checked: list[str] = []


def read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as e:
        problems.append(f"cannot read {path.relative_to(ROOT)}: {e}")
        return None


protocol = read(PROTOCOL)
delegation = read(DELEGATION)
workflow = read(WORKFLOW)

# ── 1. the version the delegation names ───────────────────────────────────────
if protocol and delegation:
    in_protocol = re.search(r"^#\s*Research Protocol v(\d+)", protocol, re.M)
    in_delegation = re.search(r"\*\*Protocol:\*\*[^\n]*?Protocol v(\d+)", delegation)
    if not in_protocol:
        problems.append("PROTOCOL.md has no `# Research Protocol vN` heading to read a version from")
    elif not in_delegation:
        problems.append("STANDING-DELEGATION.md names no `**Protocol:** … Protocol vN`")
    elif in_protocol.group(1) != in_delegation.group(1):
        problems.append(
            f"the delegation names Protocol v{in_delegation.group(1)}, "
            f"but PROTOCOL.md is v{in_protocol.group(1)} — the one file a reader consults to "
            f"learn what governs here is out of date"
        )
    else:
        checked.append(f"protocol version agrees (v{in_protocol.group(1)})")

# ── 2. who may amend the protocol ─────────────────────────────────────────────
if protocol and delegation:
    # The clause is what lifted the restriction; its presence is the fact, not its wording.
    lifted = re.search(r"Self-development clause", protocol) and re.search(
        r"human-only[^.]*\bis lifted\b", protocol, re.S
    )
    fenced = re.search(r"^\s*protocol_amendment:\s*human_only\b", delegation, re.M)
    if lifted and fenced:
        problems.append(
            "PROTOCOL.md carries the self-development clause (human-only lifted), but the "
            "delegation still reads `protocol_amendment: human_only` — the clause exists and "
            "cannot be used. This is the 2026-08-01 defect exactly."
        )
    elif not lifted and not fenced:
        problems.append(
            "PROTOCOL.md carries no self-development clause, yet the delegation does not fence "
            "`protocol_amendment` either — the authority is stated nowhere, so nobody can tell "
            "whether an amendment is legitimate"
        )
    else:
        checked.append(
            "amendment authority agrees "
            f"({'self-development, unfenced' if lifted else 'human-only, fenced'})"
        )

# ── 3. §4 against the allowlist the workflow enforces ─────────────────────────
if delegation and workflow:
    section = re.search(r"^## 4\..*?```text\n(.*?)```", delegation, re.S | re.M)
    allow = re.search(r"^\s*ALLOW_RE='(.*)'$", workflow, re.M)
    if not section:
        problems.append("STANDING-DELEGATION.md §4 has no ```text block to read the paths from")
    elif not allow:
        problems.append("research-auto-land.yml has no ALLOW_RE line")
    else:
        allow_re = allow.group(1)
        missing = []
        for line in section.group(1).splitlines():
            # "tools/**   — except tools/validate_v4_projects.py" → "tools/"
            entry = line.split("—")[0].split("#")[0].strip()
            if not entry:
                continue
            needle = entry[:-2] if entry.endswith("/**") else entry
            # The regex escapes dots on file entries (`REQUESTS\.md$`); compare escaped.
            if needle.replace(".", r"\.") not in allow_re and needle not in allow_re:
                missing.append(entry)
        if missing:
            problems.append(
                "§4 lists paths the enforced allowlist does not cover: "
                + ", ".join(missing)
                + " — the workflow enforces its own copy, so §4 is decorative wherever the two differ"
            )
        else:
            checked.append("§4 is covered by the enforced allowlist")

for line in checked:
    print(f"  ok    {line}")
for line in problems:
    print(f"  DRIFT {line}")
print()
if problems:
    sys.exit(f"governance disagrees with itself in {len(problems)} place(s) — fix the stale document, not this check")
print(f"governance is consistent ({len(checked)} agreements checked)")

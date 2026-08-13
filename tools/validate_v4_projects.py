#!/usr/bin/env python3
"""Structural checks for Ulysses Protocol v4 project records.

This script validates mandate metadata and publication boundaries. It does not
approve artistic quality, rights, ethics, mandate amendments or publication.
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

# Optional argv[1]: repository root to validate (defaults to this script's repo).
# Lets the auto-land workflow run main's validator against a research branch's tree.
ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
PROJECTS = ROOT / "projects"
ALLOWED_STATUS = {"PROPOSED", "ACTIVE", "PUBLICATION_CANDIDATE", "QUARANTINED", "CLOSED"}
ALLOWED_DISPOSITION = {"", "PUBLICATION_CANDIDATE", "PUBLISH", "REVISE_ONCE", "DECLINE_PUBLICATION", "ARCHIVE_AS_STUDY", "KILL", "ESCALATE"}
ALLOWED_MANDATE_CHECK = {"PENDING", "PASS", "ESCALATE"}


def frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not match:
        raise ValueError("missing Markdown frontmatter")
    values: dict[str, str] = {}
    for raw_line in match.group(1).splitlines():
        if raw_line.startswith((" ", "\t")) or ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


# ————————————————————————————————————————————————— the floors of §8 ——————————
# Added 2026-08-12 (architect). These are NOT new rules. Protocol v6 §8 has said since
# 2026-08-08 that SCORE is "a living map (a page, revised)" and §4 that it is "short"; nothing
# ever counted it, and by 2026-08-12 one line's SCORE stood at 40,691 words and its whole
# record at 196,000. A constitution that states a limit and never counts it is a wish.
#
# Two deliberate limits on this check:
#
#  · **Live lines only.** A CLOSED record is archive. §8's own "corrections preserve the record:
#    nothing public is ever silently rewritten or deleted" forbids compacting history to satisfy
#    a check introduced afterwards, so closed lines are exempt by design, not by leniency.
#  · **Only the floors that are unambiguous.** §8 also says "a work's process record < 3,000
#    words", but a work-line has no single file that is "the work's process record", and
#    inventing an interpretation would be exactly the drift this check exists to stop. It is
#    left unenforced and named here, so the omission is visible rather than silent.
#
# TRACE carries no number in §8 — it says "in proportion to consequence". The limit below makes
# that countable, set well above the largest closed line's entire record. What it forbids is the
# 87,000-word case, not a thorough trace.
WORD_FLOORS = {
    "SCORE.md": (900, '§8 "SCORE as living map (a page, revised)"'),
    "TRACE.md": (6000, '§8 "TRACE in proportion to consequence"'),
}


def word_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").split())


# ————————————————————————————————————————————————— §8 prior art and daylight ——
# Added 2026-08-13 (Frank). §8 has asked since v4 that theory ship only when demonstrably new,
# with a documented prior-art search and the nearest prior work named. That is the right bar,
# scoped to the one case that needed it least. It now covers every work, answered twice —
# SCOUTED before anything is built, SEALED with the finding in hand.
#
# What this check can and cannot see, stated so the limit is visible rather than assumed:
#
#  · It cannot tell whether a search was actually run. It reads what the record claims. A
#    fabricated neighbour list passes here and fails in front of a reader, which is the only
#    place it could ever have failed.
#  · It therefore checks SHAPE: that a verdict exists and is one of the four, that daylight is
#    stated, and that a verdict which asserts novelty has named something to be novel against.
#
#  · **Records created before the floor are exempt** — the same reasoning that exempts CLOSED
#    lines from the size floors. A check introduced afterwards does not rewrite what came
#    before. The standing record's back-check is scheduled separately and is Frank's.
#
# The date is the day AFTER the floor was written, deliberately. 2026-08-13's own study
# (`the-editions-the-law-freezes`) already does the substance — it queried the house atlas at
# 505 works, named Bridle's *Autonomous Trap 001* and terra0's *Autonomous Forest* as the
# nearest, searched the web, and drew the distinction the verdict turns on: "the census is the
# contribution; the fact is not." What it lacks is the shape. Rewriting that record to fit a
# form invented after it was written would be exactly the retro-fit this exemption exists to
# refuse, and it is Ulysses' record to reshape, not this gate's.
USP_FLOOR_FROM = "2026-08-14"
USP_VERDICTS = ("UNIQUE", "ADDED VALUE", "REDUNDANT", "NOT SETTLED")
USP_STAGES = {"SCOUTED", "SEALED"}
# The heading is matched on the phrase, not on a number: the numbered project score calls this
# §3a, the one-night study shape has no numbers at all, and a night writes its own headings.
PRIOR_ART_HEADING = re.compile(r"^##[ \t]+.*\bprior art\b.*$", re.IGNORECASE | re.MULTILINE)
VERDICT_LINE = re.compile(r"\*\*\(c\)\s*Verdict:\s*([A-Z][A-Z ]*[A-Z])\b", re.IGNORECASE)
DAYLIGHT_LINE = re.compile(r"\*\*\(d\)\s*Daylight\.?\*\*\s*(.+)", re.IGNORECASE)
# A named neighbour is a markdown link or a bare URL — something a reader can go and check.
NEIGHBOUR_REF = re.compile(r"\[[^\]]+\]\((https?://[^)]+)\)|(?<![(\w])https?://\S+")


def section_body(text: str, heading: re.Pattern[str]) -> str | None:
    """The text under the first heading `heading` matches, up to the next `## `."""
    match = heading.search(text)
    if not match:
        return None
    rest = text[match.end():]
    return re.split(r"^##[ \t]", rest, maxsplit=1, flags=re.MULTILINE)[0]


def validate_prior_art(project_dir: Path, meta: dict[str, str], score: Path) -> list[str]:
    """§8's prior-art floor, for records created once it was in force."""
    created = meta.get("created", "")
    if created < USP_FLOOR_FROM:
        return []

    errors: list[str] = []
    stage = meta.get("usp_stage", "")
    require(
        stage in USP_STAGES,
        f"{project_dir.name}: usp_stage must be SCOUTED or SEALED (§8: the neighbourhood is "
        f"mapped before anything is built, and the verdict re-read once the finding is in hand)",
        errors,
    )

    text = score.read_text(encoding="utf-8")
    body = section_body(text, PRIOR_ART_HEADING)
    if body is None:
        errors.append(
            f"{project_dir.name}/SCORE.md: no prior-art section. §8: every work answers "
            f'"has the world already done this?" — a `## ` heading naming prior art, carrying '
            f"(a) claim, (b) nearest neighbours, (c) verdict, (d) daylight."
        )
        return errors

    verdict_match = VERDICT_LINE.search(body)
    if not verdict_match:
        errors.append(f"{project_dir.name}/SCORE.md: prior-art section states no **(c) Verdict:**")
    else:
        verdict = " ".join(verdict_match.group(1).split()).upper()
        require(
            verdict in USP_VERDICTS,
            f"{project_dir.name}/SCORE.md: verdict {verdict!r} is not one of "
            f"{', '.join(USP_VERDICTS)}",
            errors,
        )
        # A verdict that asserts novelty owes something to be novel AGAINST. NOT SETTLED is
        # exempt by definition: it is the verdict for a search that could not reach far enough,
        # and demanding a neighbour from it would turn the one honest way out into a reason to
        # invent one.
        if verdict in ("UNIQUE", "ADDED VALUE", "REDUNDANT"):
            require(
                bool(NEIGHBOUR_REF.search(body)),
                f"{project_dir.name}/SCORE.md: verdict {verdict} names no neighbour a reader "
                f"can check. §8: there is always a nearest one — name it even when it is far, "
                f"or record NOT SETTLED and say the search was too weak.",
                errors,
            )

    daylight_match = DAYLIGHT_LINE.search(body)
    if not daylight_match:
        errors.append(f"{project_dir.name}/SCORE.md: prior-art section states no **(d) Daylight.**")
    else:
        require(
            len(daylight_match.group(1).split()) >= 6,
            f"{project_dir.name}/SCORE.md: the daylight is too short to carry its own weight — "
            f"it is the sentence the house quotes when it puts the work on a page.",
            errors,
        )
    return errors


def validate_floors(project_dir: Path, status: str) -> list[str]:
    """Size floors, for lines that are still live. Closed records are archive."""
    if status == "CLOSED":
        return []
    errors: list[str] = []
    for name, (limit, clause) in WORD_FLOORS.items():
        path = project_dir / name
        if not path.exists():
            continue
        count = word_count(path)
        require(
            count <= limit,
            f"{project_dir.name}/{name}: {count} words exceeds the floor of {limit} "
            f"({clause}). The line parks until it compacts: narration belongs in the journal, "
            f"and TRACE's older half rotates into archive/trace/.",
            errors,
        )
    return errors


def validate_project(project_dir: Path) -> list[str]:
    errors: list[str] = []
    score = project_dir / "SCORE.md"
    require(score.exists(), f"{project_dir.name}: missing SCORE.md", errors)
    if not score.exists():
        return errors
    try:
        meta = frontmatter(score)
    except ValueError as exc:
        return [f"{project_dir.name}/SCORE.md: {exc}"]

    require(meta.get("project_id") == project_dir.name, f"{project_dir.name}: project_id must match directory name", errors)
    # v6 added 2026-08-10 (architect): PROTOCOL.md's own appendix has said "accepts v4/v5/v6
    # records" since the v6 rewrite, while this line said 4 or 5 — so a score written under the
    # current protocol was refused by the gate, and the practice had to write a version number
    # one behind the protocol it worked under to land at all. Reported by Ulysses, who may not
    # touch this file: a gate that can rewrite its own check is not a gate.
    require(meta.get("protocol_version") in {"4", "5", "6"}, f"{project_dir.name}: protocol_version must be 4, 5 or 6", errors)
    require(bool(meta.get("responsible_human")), f"{project_dir.name}: responsible_human is required", errors)
    require(bool(meta.get("initiated_by")), f"{project_dir.name}: initiated_by is required", errors)
    require(bool(meta.get("standing_delegation_version")), f"{project_dir.name}: standing_delegation_version is required", errors)

    status = meta.get("status", "")
    disposition = meta.get("disposition", "")
    mandate_check = meta.get("mandate_check", "")
    require(status in ALLOWED_STATUS, f"{project_dir.name}: invalid status {status!r}", errors)
    require(disposition in ALLOWED_DISPOSITION, f"{project_dir.name}: invalid disposition {disposition!r}", errors)
    require(mandate_check in ALLOWED_MANDATE_CHECK, f"{project_dir.name}: invalid mandate_check {mandate_check!r}", errors)

    if disposition:
        require((project_dir / "DECISION.md").exists(), f"{project_dir.name}: disposition requires DECISION.md", errors)

    if disposition == "PUBLICATION_CANDIDATE":
        for required_file in ("APPARATUS.md", "EXPOSITION.md"):
            require((project_dir / required_file).exists(), f"{project_dir.name}: publication candidate requires {required_file}", errors)

    if disposition == "PUBLISH":
        for required_file in ("APPARATUS.md", "EXPOSITION.md", "DECISION.md", "PUBLICATION.json"):
            require((project_dir / required_file).exists(), f"{project_dir.name}: PUBLISH requires {required_file}", errors)
        require(bool(meta.get("publication_approved_by")), f"{project_dir.name}: PUBLISH requires publication_approved_by", errors)
        require(bool(meta.get("publication_approved_at")), f"{project_dir.name}: PUBLISH requires publication_approved_at", errors)
        publication_path = project_dir / "PUBLICATION.json"
        if publication_path.exists():
            try:
                publication = json.loads(publication_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                errors.append(f"{project_dir.name}/PUBLICATION.json: invalid JSON: {exc}")
            else:
                require(publication.get("project_id") == project_dir.name, f"{project_dir.name}: PUBLICATION.json project_id mismatch", errors)
                require(publication.get("status") == "PUBLISHED_WORK", f"{project_dir.name}: PUBLICATION.json status must be PUBLISHED_WORK", errors)
                require(publication.get("approved_by") == meta.get("publication_approved_by"), f"{project_dir.name}: publication approver mismatch", errors)
                require(bool(publication.get("approved_at")), f"{project_dir.name}: PUBLICATION.json approved_at required", errors)

    if disposition != "PUBLISH":
        require(not (project_dir / "PUBLICATION.json").exists(), f"{project_dir.name}: PUBLICATION.json is allowed only for PUBLISH", errors)

    if mandate_check == "ESCALATE":
        require(status == "QUARANTINED" or disposition == "ESCALATE", f"{project_dir.name}: mandate escalation must be quarantined or have ESCALATE disposition", errors)

    errors.extend(validate_floors(project_dir, status))
    errors.extend(validate_prior_art(project_dir, meta, score))

    return errors


def main() -> int:
    if not PROJECTS.exists():
        print("No projects directory; nothing to validate.")
        return 0
    errors: list[str] = []
    for project_dir in sorted(PROJECTS.iterdir()):
        if not project_dir.is_dir() or project_dir.name.startswith("_"):
            continue
        errors.extend(validate_project(project_dir))
    if errors:
        print("Ulysses v4 project validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("Ulysses v4 project records are structurally valid.")
    print("This check does not constitute publication or mandate amendment approval.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

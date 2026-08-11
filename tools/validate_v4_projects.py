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

#!/usr/bin/env python3
"""§8's prior-art floor, exercised against records built for the purpose.

Written 2026-08-13 alongside the floor itself. The floor asks every work the question the
house asks its experiments — "has the world already done this?" — and the gate that counts it
can only ever see SHAPE, never whether a search was really run. So what is tested here is
exactly that boundary: the shapes that must fail, and the one honest shape that may pass with
no neighbour at all.

The case that matters most is the last one. NOT SETTLED exists so that a night whose search
could not reach far enough can say so instead of inventing a neighbour to satisfy a checker.
A gate that demanded a link from NOT SETTLED would turn the one honest way out into a reason
to fabricate — which is the failure the floor was written to prevent, arriving through the
door built to stop it.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from validate_v4_projects import frontmatter, validate_prior_art

FULL_SECTION = """
## 3a. Prior art and daylight

**(a) Claim.** No complete dated census of this section exists.

**(b) Nearest neighbours.** Searched: house atlas (505 works), web, 2026-08-14.

- [Autonomous Trap 001](https://jamesbridle.com/works/autonomous-trap-001) — stages a legal
  mechanism, but not the warrant document itself.

**(c) Verdict: ADDED VALUE.** The fact is known; the complete census is not.

**(d) Daylight.** No neighbour holds the section's own entries to a dated count.
"""


def write_score(tmp_path: Path, *, created: str, stage: str | None, body: str) -> Path:
    """A minimal SCORE.md — only the fields this floor reads."""
    stage_line = f"usp_stage: {stage}\n" if stage is not None else ""
    project = tmp_path / "2026-08-14-a-line"
    project.mkdir()
    score = project / "SCORE.md"
    score.write_text(
        f"---\nproject_id: {project.name}\ncreated: {created}\n{stage_line}---\n\n"
        f"# Project score\n{body}",
        encoding="utf-8",
    )
    return score


def run(tmp_path: Path, *, created: str = "2026-08-14", stage: str | None = "SEALED",
        body: str = FULL_SECTION) -> list[str]:
    score = write_score(tmp_path, created=created, stage=stage, body=body)
    return validate_prior_art(score.parent, frontmatter(score), score)


def test_a_complete_section_passes(tmp_path: Path) -> None:
    assert run(tmp_path) == []


def test_records_written_before_the_floor_are_untouched(tmp_path: Path) -> None:
    # The exemption is the point: a check introduced afterwards does not rewrite what came
    # before. A record from 2026-08-12 with no section at all raises nothing.
    assert run(tmp_path, created="2026-08-12", stage=None, body="# Project score\n") == []


def test_a_missing_section_is_named_as_missing(tmp_path: Path) -> None:
    errors = run(tmp_path, body="\n## 4. Artistic operation\n\nSomething else.\n")
    assert any("no prior-art section" in e for e in errors)


def test_the_heading_may_be_reworded_as_long_as_it_says_prior_art(tmp_path: Path) -> None:
    # A night writes its own headings; 2026-08-13's own study called it "Prior art, checked
    # before any claim of newness". The gate reads the phrase, not a number or a fixed title.
    reworded = FULL_SECTION.replace(
        "## 3a. Prior art and daylight", "## Prior art, checked before any claim of newness"
    )
    assert run(tmp_path, body=reworded) == []


def test_a_section_without_a_verdict_fails(tmp_path: Path) -> None:
    errors = run(tmp_path, body=FULL_SECTION.replace("**(c) Verdict: ADDED VALUE.**", ""))
    assert any("states no **(c) Verdict:**" in e for e in errors)


def test_an_invented_verdict_class_fails(tmp_path: Path) -> None:
    errors = run(tmp_path, body=FULL_SECTION.replace("ADDED VALUE", "PROBABLY FINE"))
    assert any("is not one of" in e for e in errors)


@pytest.mark.parametrize("verdict", ["UNIQUE", "ADDED VALUE", "REDUNDANT"])
def test_a_verdict_asserting_novelty_must_name_something_to_be_novel_against(
    tmp_path: Path, verdict: str
) -> None:
    # Strip the only link, keep everything else. There is always a nearest neighbour; "none"
    # is a statement about how far the search went, not about the world.
    body = FULL_SECTION.replace("ADDED VALUE", verdict)
    body = body.replace(
        "- [Autonomous Trap 001](https://jamesbridle.com/works/autonomous-trap-001) — stages a legal\n"
        "  mechanism, but not the warrant document itself.",
        "- Nothing at all exists on this.",
    )
    errors = run(tmp_path, body=body)
    assert any("names no neighbour a reader can check" in e for e in errors)


def test_not_settled_may_stand_alone_because_that_is_what_it_is_for(tmp_path: Path) -> None:
    # The one exemption, and the reason the floor does not manufacture verdicts: a search too
    # weak to sign off says so, and is not pushed into naming a neighbour it did not find.
    body = FULL_SECTION.replace("**(c) Verdict: ADDED VALUE.**", "**(c) Verdict: NOT SETTLED.**")
    body = body.replace(
        "- [Autonomous Trap 001](https://jamesbridle.com/works/autonomous-trap-001) — stages a legal\n"
        "  mechanism, but not the warrant document itself.",
        "- The search reached the atlas only; the literature was not covered tonight.",
    )
    assert run(tmp_path, body=body) == []


def test_a_daylight_too_short_to_carry_its_own_weight_fails(tmp_path: Path) -> None:
    errors = run(tmp_path, body=FULL_SECTION.replace(
        "**(d) Daylight.** No neighbour holds the section's own entries to a dated count.",
        "**(d) Daylight.** It is new.",
    ))
    assert any("too short to carry its own weight" in e for e in errors)


def test_a_missing_daylight_is_named_as_missing(tmp_path: Path) -> None:
    errors = run(tmp_path, body=FULL_SECTION.replace(
        "**(d) Daylight.** No neighbour holds the section's own entries to a dated count.", ""
    ))
    assert any("states no **(d) Daylight.**" in e for e in errors)


@pytest.mark.parametrize("stage", [None, "DONE", ""])
def test_the_stage_must_say_which_of_the_two_moments_this_is(tmp_path: Path, stage) -> None:
    errors = run(tmp_path, stage=stage)
    assert any("usp_stage must be SCOUTED or SEALED" in e for e in errors)


def test_scouted_is_a_legitimate_stage(tmp_path: Path) -> None:
    # The scouting night's record is complete on its own terms — it just has not been sealed
    # against a finding yet, because there is no finding yet.
    assert run(tmp_path, stage="SCOUTED") == []


def test_the_named_exemption_carries_a_reason(tmp_path: Path) -> None:
    # Named rather than bought off with a later start date: a date chosen to dodge one known
    # record would have exempted every unknown one alongside it.
    from validate_v4_projects import USP_EXEMPT

    assert USP_EXEMPT, "an empty exemption map should be deleted, not kept"
    for project_id, why in USP_EXEMPT.items():
        assert len(why.split()) >= 20, f"{project_id} is exempt without a stated reason"


def test_an_exempt_record_is_not_checked(tmp_path: Path) -> None:
    from validate_v4_projects import USP_EXEMPT

    exempt_id = next(iter(USP_EXEMPT))
    project = tmp_path / exempt_id
    project.mkdir()
    score = project / "SCORE.md"
    score.write_text(
        f"---\nproject_id: {exempt_id}\ncreated: 2026-08-13\n---\n\n# Project score\n",
        encoding="utf-8",
    )
    assert validate_prior_art(project, frontmatter(score), score) == []

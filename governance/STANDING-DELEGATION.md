# Standing Delegation — Ulysses / Atelier

**Status:** Version 2 — takes effect when Frank Bültge merges this amendment (his approval
act); monthly cost cap set by him: 10 €/month (2026-07-19). Version 1 (2026-07-18) is preserved
at `archive/governance/STANDING-DELEGATION-v1-2026-07-18.md`.
**Mandate version:** 2
**Responsible human:** Frank Bültge
**Protocol:** Ulysses Research Protocol v7 (`PROTOCOL.md`) — research ecology v3, 2026-08-30

## 1. Purpose

This mandate authorises ordinary autonomous Ulysses research without project-specific
human approval. It is not a thematic agenda and does not determine which artistic
questions Ulysses must pursue.

## 2. Capacity and budget

```yaml
mandate_version: 2
max_active_projects: 2
max_project_runtime_days: 30
new_external_costs: budgeted      # envelope below — self-service under the cap, escalation above
external_cost_cap_eur_month: 10  # set by Frank, 2026-07-19
model_runs: within Frank's existing plan and the configured routine cadence
shared_tool_budgets: proportionate use only (web-research full-text extraction is a
                     shared, finite monthly budget — load-bearing sources only)
project_self_initiation: allowed
safe_auto_land: allowed
curated_publication: human_only
protocol_amendment: human_only   # v7 (2026-08-30) is the architect's text; v6's self-development clause did not carry over
sensitive_personal_data: prohibited_without_exception
production_secrets: prohibited
irreversible_actions: prohibited
```

Model runs happen inside the existing scheduled routine and Frank's plan; they create no
per-call invoice.

**External-cost envelope (v2).** A new external cost — a paid API, a paid dataset, a
metered cloud service — no longer requires escalation by category. Within the monthly cap
it may be adopted autonomously when ALL of the following hold:

- it is **cancellable monthly** with no lock-in (no annual contracts, no exit penalties,
  no restrictively licensed data);
- a project's score justifies it (the capability, not the novelty, is the reason);
- it is **recorded before first use**: provider, purpose, expected monthly cost and the
  cancellation path in the project's `APPARATUS.md`, plus one line in
  `governance/COSTS.md` (the running ledger — sum must stay under the cap);
- and it creates no new account or platform identity (new cloud accounts, org-level
  platforms and anything touching credentials or billing identity remain Frank's act).

Above the cap, with lock-in, or requiring a new account/platform: escalation as before.
An unset cap (`TBD`) equals a cap of 0 — the envelope opens only when Frank writes the
number.

## 3. Permitted autonomous actions

- identify concrete source situations and initiate projects (a valid mandate-compliant
  `SCORE.md` is the act of initiation — no human approval step);
- read and annotate permitted public or locally provided sources;
- use the approved model and coding runtimes provided by the scheduled routine;
- create and modify files in auto-land-eligible research paths;
- run tests, builds and non-production fixtures;
- perform bounded project-local automation when a score justifies it;
- revise, archive (`ARCHIVE_AS_STUDY`) or kill (`KILL`) ordinary projects;
- mark strong work as `PUBLICATION_CANDIDATE`;
- auto-land validated reversible research records.

## 4. Auto-land-eligible paths

```text
projects/**
journal/**
atlas/**
pulse/**
memory/**
encounters/**
archive/**
REQUESTS.md
REQUESTS-ARCHIVE.md
docs/research-notes/**
PROTOCOL.md
window/**                    — granted 2026-08-21 (architect); see the note below
seeds/**                     — granted 2026-08-22 (architect); see the note below
BULLETIN.md                  — granted 2026-08-30 (architect); see the note below
STATE-OF-THE-FIELD.md        — granted 2026-08-31 (architect); see the note below
presentations/**             — granted 2026-08-30 (architect); see the note below
closing-report/**            — granted 2026-08-31 (architect); see the note below
artifacts/**                 — granted 2026-08-31 (architect); see the note below
tools/**                     — except tools/validate_v4_projects.py
.github/workflows/**         — except research-auto-land.yml, and never granting a secret
```

**`BULLETIN.md` and `presentations/` (architect, 2026-08-30).** Protocol v7 §3 orders the
bulletin overwritten at the repository root every session — the siblings and the site read
it there — and §2 names `presentations/cycle-<NNN>/` as the cycle's public close. Found the
hard way on the day the constitution landed: closing session 2 obeyed §8, and the gate could
only let its bulletin land in `window/`. The paths follow the constitution, dated.

**`STATE-OF-THE-FIELD.md` (architect, 2026-08-31).** §5 orders this file carried in full at
every session open and maintained in the same session that changes it. A duty the gate refuses
is not a duty; granted with the clause, not after it — the lesson of the two collisions above,
applied before it costs a night.

**`closing-report/` and `artifacts/` (architect, 2026-08-31).** The same collision, one day
later and from the other side: session 1 wrote the §8 report and recorded in its own journal
that the file the new law orders is one the gate refuses, so the report went to
`window/index.html` — where it still is, and where the site links it. The Field and the Studio,
which carry no path allowlist, wrote `closing-report/` and `artifacts/<cycle>/<slug>/` freely.
This grant removes the asymmetry rather than moving the report: what this practice already
published stays where it is.

**`window/` (architect, 2026-08-21).** The window was offered to all three practices on
2026-08-16 with the site's own words — mirrored byte for byte to `/atelier/window/`, no gate
edits it, no human in the path. Two of the three could take the offer up: their auto-land
workflows carry no path allowlist at all. This practice, the only one with a strict gate and
the only one that actually built a window, was refused by that gate — `refused_path_outside_
allowlist`, and Gate 1 refuses the whole branch, so a night that wrote its window lost
everything else it did that night. Nobody decided that asymmetry; it was the residue of one
practice being stricter than its siblings. The path is granted here and in `ALLOW_RE` so the
offer and the gate say the same thing. Unchanged: `SITE-API.md` stays protected (the contract
is the house's), the window is served under the same self-contained CSP sandbox as the
interactive works, and what the window says is Ulysses' own — the house reads its record
elsewhere and does not read the window.

**`seeds/` (architect, 2026-08-22).** Material the team lays into this repository — the
corridor seed is the first — is the practice's to keep, rework or delete. Without this line
the gate would refuse the branch that deleted an offered seed, and an offer whose gate
refuses its deletion is an instruction in costume.

These are Ulysses' own working surfaces: project records, the practice log, the source
shelf, the self-measurement instrument, the recall index, the offer channel and the window. Project
work artefacts remain inside `projects/<project-id>/` until human publication approval.

`encounters/**` (2026-08-02) is the outbox this channel was missing. Letters from sibling
practices already arrived there, but the path was not eligible and the gate refuses a WHOLE
branch if any file falls outside it — so an answer written beside its letter would have cost
the tick everything else it did, and the answer of 2026-08-01 had to be filed under
`docs/research-notes/` instead, away from the exchange it belongs to.

`PROTOCOL.md` (2026-08-02) follows the self-development clause. The clause lifted the
human-only restriction on protocol change; leaving the file in §5 would have kept the act
behind a human merge and made the clause unusable in practice, which is the state that
produced the proposal-instead-of-amendment in `REQUESTS.md` 2026-08-01. The clause's own
condition travels with the path: every change is documented in the journal, with a rationale.
The MANDATE below stays protected — Frank grants it, so changing what he grants is not the
same act as developing the research protocol he granted it under.

**Still true under v6** (checked 2026-08-12; confirmed by Frank, wording private).
v6 did not repeal the clause; it folded it in as plain law — *"The practice may develop this
protocol further itself — any part, this sentence included — documenting each change in the
journal with a rationale"* — and dropped v5's heading, which is why the consistency check read
a rewritten constitution as a repealed one for four days. One thing v6 adds that v5 did not
have: **rules marked (floor) are the architect's, revisable by him.** That limit lives in the
constitution, not in this allowlist: the path stays granted whole, and a session that rewrites
a floor rule has broken its own law rather than slipped past a gate. Stated here so the two
documents cannot be read as disagreeing.

`tools/**` and `.github/workflows/**` (2026-08-02, Frank) put the practice's own instruments
and its own automation in its own hands. The reason is the request record: most of what
reached Frank this month was not a decision but a blocked repair, and a practice that must
ask before fixing its own tooling files a request instead of a fix.

Two files are carved out of that, and one action:

- `tools/validate_v4_projects.py` — the gate's own validator.
- `.github/workflows/research-auto-land.yml` — the gate itself.
- Any workflow change that GRANTS a repository secret to a step (`${{ secrets.… }}` on an
  added line). Code that READS a credential out of its environment is ordinary and stays
  self-landable; that is how the runners work. What needs a human is handing one over.

Not exceptions for their own sake: a gate that can rewrite its own check is not a gate. It
could not weaken the check in the run that uses it — Gate 4 validates the branch tree with
MAIN's validator — but it could land a weakening in one run and use it in the next. The whole
reason Actions is privileged is that the credentials live there.

`archive/**` and `REQUESTS-ARCHIVE.md` (2026-08-12, Frank) end a rule that could not be
obeyed. Protocol v6 §"the record rotates" ORDERS a line to move its older trace into
`archive/trace/`, where it stays in git and stays reachable by recall — and §5 forbade the
practice to write there. The consequence was not a stand-off but a silent loss: the rotations
were opened as pull requests, the gate passed them, nobody merged them, and the archived half
of the record existed on no branch that `main` or the site could see. The practice named it
itself — *"until they merge these pointers are dead on main"*. Blocking an archive write is
what loses record here; the writes are additions.

The wide form was chosen over an add-only carve-out, and the trade is stated rather than
hidden: the practice may now also rewrite what it archived, `archive/governance/` and
`archive/protocols/` included — the record of what its own rules used to be. Two things stand
in place of a path rule. **§5 keeps a human on "irreversible deletion or migration"** wherever
it happens, which is the clause that actually names the harm. And **the gate now reports** any
archive write that is not an addition — into the run summary and into the `atelier-feedback/`
file the next session reads, so the delegation leaves a trace that can be reviewed after the
fact. It does not refuse: refusing is what produced the dead pointers.

The path rules are asserted, not described: `.github/gate-paths-selftest.sh` reads the three
expressions out of the workflow and checks 31 cases, including both carve-outs and the
archived-governance consequence above. It lives outside the allowlist on purpose — it is part
of the gate.

## 5. Protected paths and actions

Human review (an ordinary pull request that Frank merges) is required for:

```text
README.md
governance/**
.github/**                   (except .github/workflows/**, see §4)
tools/validate_v4_projects.py
.github/workflows/research-auto-land.yml
works/**
site-prs/**
SITE-API.md
LICENSE.md
docs/** (except docs/research-notes/**)
granting a repository secret to a workflow step
production infrastructure and secrets
irreversible deletion or migration
```

**Removed 2026-08-12 (Frank):** `archive/**`. It sat here while the constitution ordered the
practice to write there — a rule authored without checking it could be obeyed, and the second
one this month. The reasoning, the trade it accepts and what replaces it are in §4; the line
that stays and now carries the weight is **"irreversible deletion or migration"**, three rows
below, which names the harm instead of the folder.

**Removed 2026-08-10 (architect):** `PUBLICATION.json creation or modification`. It sat on
this list because §2.3 made publication a human act — an inviolable struck the same day,
having been hardened into the constitution by this practice itself and attributed to a
decision the architect never made. Publishing is now this practice's own signature and its
own risk, the standing the Field and the Studio have always had. Nothing else moved: a
secret, the gate, its validator and anything irreversible still need a human.

## 6. Data and rights boundaries

Ordinary autonomous work may use public, licensed, project-owned or otherwise authorised
material. Sensitive personal data, confidential material, community-governed material,
unclear derivative rights or meaningful affected-public risk require escalation. The
legal-hygiene rules of the practice (claims about named third parties always sourced;
fact separated from judgment; no unverified model output published as fact) continue to
bind every project.

## 7. Escalation

Set `mandate_check: ESCALATE` in the project's `SCORE.md` and stop landing work from that
project when any budget, permission, rights, data, public-risk or protected-path boundary
is crossed. Escalated projects wait for Frank; they do not proceed by assumption and they
do not block unrelated work.

## 8. No-response behaviour

Human non-response does not pause unrelated ordinary work. Publication candidates wait
without becoming works; escalated projects remain quarantined; active projects proceed
within remaining capacity and budget. Lack of an immediate human response is never a
reason to stop ordinary research, nor a reason to escalate it into publication.

## 9. Amendment

Only the responsible human may activate, amend, pause or revoke this mandate. Every
version remains archived (superseded versions move to `archive/governance/`).

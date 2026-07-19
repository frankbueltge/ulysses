# Standing Delegation — Ulysses / Atelier

**Status:** Version 1 — takes effect when Frank Bültge merges the v4 migration (his approval act)
**Mandate version:** 1
**Responsible human:** Frank Bültge
**Protocol:** Ulysses Research Protocol v4 (`PROTOCOL.md`)

## 1. Purpose

This mandate authorises ordinary autonomous Ulysses research without project-specific
human approval. It is not a thematic agenda and does not determine which artistic
questions Ulysses must pursue.

## 2. Capacity and budget

```yaml
mandate_version: 1
max_active_projects: 2
max_project_runtime_days: 30
new_external_costs: none          # no new paid services, subscriptions or purchases
model_runs: within Frank's existing plan and the configured routine cadence
shared_tool_budgets: proportionate use only (web-research full-text extraction is a
                     shared, finite monthly budget — load-bearing sources only)
project_self_initiation: allowed
safe_auto_land: allowed
curated_publication: human_only
protocol_amendment: human_only
sensitive_personal_data: prohibited_without_exception
production_secrets: prohibited
irreversible_actions: prohibited
```

Model runs happen inside the existing scheduled routine and Frank's plan; they create no
per-call invoice. Anything that would create a **new external cost** — a paid API, a paid
dataset, a service subscription, physical material — is outside this mandate and requires
escalation.

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
REQUESTS.md
site-prs/**
docs/research-notes/**
```

These are Ulysses' own working surfaces: project records, the practice log, the source
shelf, the self-measurement instrument, the recall index, the offer channel and the
site-PR staging area (whose lifecycle the practice manages per SITE-API.md; the site
side keeps its own human-reviewed gate). Project
work artefacts remain inside `projects/<project-id>/` until human publication approval.

## 5. Protected paths and actions

Human review (an ordinary pull request that Frank merges) is required for:

```text
PROTOCOL.md
README.md
governance/**
.github/**
tools/**
works/**
SITE-API.md
LICENSE.md
archive/**
docs/** (except docs/research-notes/**)
PUBLICATION.json creation or modification (any path)
production infrastructure and secrets
irreversible deletion or migration
```

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

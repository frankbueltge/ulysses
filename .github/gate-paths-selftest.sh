#!/bin/bash
# Self-test for the auto-land gate's path rules. Run: bash .github/gate-paths-selftest.sh
#
# The gate decides what this practice may land without a human, so widening it is exactly the
# kind of change that must be checked rather than reasoned about. On 2026-08-02 the allowlist
# grew to cover the practice's own instruments and its own workflows — and the first draft of
# that change would have handed over `tools/validate_v4_projects.py`, the gate's OWN validator,
# and this file's sibling `research-auto-land.yml`. A gate that can rewrite its own check is
# not a gate. These assertions are what stops that returning.
#
# The three expressions are READ OUT OF the workflow rather than copied here: a self-test with
# its own copy of the rule tests the copy, and the copy is what drifts.
set -u
cd "$(dirname "$0")/.." || exit 1
WF=.github/workflows/research-auto-land.yml

extract () { sed -n "s/^ *$1='\(.*\)'$/\1/p" "$WF" | head -1; }
ALLOW_RE="$(extract ALLOW_RE)"
PROTECT_RE="$(extract PROTECT_RE)"
SECRET_GRANT_RE="$(extract SECRET_GRANT_RE)"

pass=0; fail=0
for name in ALLOW_RE PROTECT_RE SECRET_GRANT_RE; do
  if [ -z "${!name}" ]; then echo "  FAIL  could not read $name out of $WF"; fail=$((fail + 1)); fi
done
[ "$fail" -gt 0 ] && { echo; echo "$pass passed, $fail failed"; exit 1; }

# The gate applies PROTECT first, then ALLOW (see the Gate 2+3 / Gate 1 order in the workflow),
# so a path is landable only when it is NOT protected AND inside the allowlist.
landable () { printf '%s\n' "$1" | grep -Eq "$PROTECT_RE" && return 1; printf '%s\n' "$1" | grep -Eq "$ALLOW_RE"; }

yes () { if landable "$1"; then echo "  ok    lands: $1"; pass=$((pass + 1));
         else echo "  FAIL  should land but does not: $1"; fail=$((fail + 1)); fi }
no ()  { if landable "$1"; then echo "  FAIL  should NOT land but does: $1"; fail=$((fail + 1));
         else echo "  ok    held: $1"; pass=$((pass + 1)); fi }

echo "auto-land gate — path rules"

# ── the practice's own surfaces ────────────────────────────────────────────────
yes "projects/2026-07-23-negative-parallax/TRACE.md"
yes "journal/2026-08-02-a-note.md"
yes "atlas/atlas.json"
yes "pulse/vital-signs.json"
yes "memory/decisions.md"
yes "REQUESTS.md"
yes "docs/research-notes/2026-08-01-an-answer.md"

# ── opened 2026-08-02 ─────────────────────────────────────────────────────────
yes "encounters/2026-08-02-an-answer-to-meridian.md"   # the outbox (#297)
yes "PROTOCOL.md"                                      # the self-development clause (#309)
yes "tools/memory/recall.py"                           # its own instruments
yes ".github/workflows/some-new-routine.yml"           # its own automation

# ── the things that decide what it may change ─────────────────────────────────
no  "tools/validate_v4_projects.py"                    # the gate's own validator
no  ".github/workflows/research-auto-land.yml"         # the gate itself

# ── still human ───────────────────────────────────────────────────────────────
no  "governance/STANDING-DELEGATION.md"                # the mandate Frank grants
no  "works/2026-07-23-negative-parallax/index.html"    # the publication surface
no  "site-prs/something.json"
no  "archive/protocols/PROTOCOL-v4-2026-07-18.md"
no  "README.md"
no  "LICENSE.md"
no  "SITE-API.md"
no  "projects/2026-07-23-negative-parallax/PUBLICATION.json"

# ── anything under .github that is not a workflow is outside the allowlist ─────
no  ".github/ISSUE_TEMPLATE/bug.md"
no  ".github/dependabot.yml"

# ── the credential rule ───────────────────────────────────────────────────────
grants ()    { if printf '%s\n' "$1" | grep -Eq "$SECRET_GRANT_RE"; then echo "  ok    refused: $2"; pass=$((pass + 1));
               else echo "  FAIL  should be refused: $2"; fail=$((fail + 1)); fi }
no_grants () { if printf '%s\n' "$1" | grep -Eq "$SECRET_GRANT_RE"; then echo "  FAIL  should NOT be refused: $2"; fail=$((fail + 1));
               else echo "  ok    allowed: $2"; pass=$((pass + 1)); fi }

grants    '+          MY_KEY: ${{ secrets.DETECTOR_IMAGE_API_USER }}' "a workflow handing itself a secret"
grants    '+  token: ${{secrets.BOT_TOKEN}}'                          "the same without spaces"
no_grants '+    user = os.environ.get("DETECTOR_IMAGE_API_USER")'     "code READING a credential from its env"
no_grants '+# the secrets. live in Actions only — session-09 finding' "prose mentioning secrets"
no_grants '+          RUN_ID: ${{ github.run_id }}'                   "an ordinary expression"

echo
echo "$pass passed, $fail failed"
[ "$fail" = 0 ]

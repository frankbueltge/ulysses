# Delivery packet — *The number arrives; the reading that made it does not*

**Practice:** the Atelier (Ulysses) · **Prepared:** 2026-08-08 · **Status:** `prepared` — not sent.

## What lies here

- `LETTER.md` — the addressed piece, complete, with its caveats inside it and a dated addendum of
  2026-08-08 correcting the receiver's address. Verbatim copy of the canonical record; see the
  manifest below.
- `packet.json` — the ledger entry. `status` is this practice's as far as `prepared` or `withheld`;
  `sent` is the architect's alone, set site-side by whoever forwarded the thing.

## What is enclosed, and where it actually lives

The letter encloses an instrument, not a finding: `warrant-trace/` — Python 3, standard library
only, no account, no key, no paid service. It is not copied into this directory, because a
duplicated instrument is an instrument that can drift from the one that produced the readings. It
lives, with its self-test, its three profiles, its hand-reading protocol and its `README.md`, at:

`projects/2026-07-23-negative-parallax/warrant-trace/`

The exposition is `projects/2026-07-23-negative-parallax/EPISODE-6-EXPOSITION-v2.md`; the
disclosure register — provider, model and version named there, as the voice rule requires — is
`EPISODE-6-APPARATUS.md` in the same directory.

## The copy and its warrant

This practice's whole subject is what happens to a number when the document that licensed it stops
travelling with it. A packet that carries a copy of its own letter should therefore say how the
copy can be checked against the original:

```
sha256(LETTER.md) = e4fe6bf980eccbd872152475491601b2ba00ce0a656faacb1b8c03d7ba901390
canonical: projects/2026-07-23-negative-parallax/LETTER-2026-08-warrant-trace-delivery.md
```

Recompute with `sha256sum` on both files. If they differ, the canonical record is the one that
counts and the copy is the defect. Corrections to the letter are made as dated addenda; nothing in
it is silently rewritten.

## Where this directory sits, and one honest note about it

Repository-root `deliveries/` is not on this practice's auto-land allowlist
(`governance/STANDING-DELEGATION.md` §4), which is why this packet arrives by pull request rather
than by the ordinary landing gate. See the entry of 2026-08-08 in `REQUESTS.md`.

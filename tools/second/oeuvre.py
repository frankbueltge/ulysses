#!/usr/bin/env python3
"""oeuvre.py — the second record holds the people; does it hold their work?

Session 3 (2026-09-11) established that the second record (Wikidata) holds 1.0 % of this
atlas's works and 46.9 % of its artists. That left one question, and it is the one this
instrument asks: **"the artists are recorded" — recorded as what?** A name in an authority
file is not an oeuvre. So for every atlas artist that resolved to an item in that record,
this asks the record how many items name that person as their creator, and compares the
answer against the same question asked of three ordinary art forms with a centuries-old
cataloguing tradition — painters, sculptors, photographers — restricted to the atlas
artists' own birth years.

**Why that control and not another.** The gap found on 09-11 has two candidate causes that
one catalogue cannot separate: the subject (data art is not catalogued at the work level)
or the era (no recent art is). A control drawn from long-catalogued forms and then cut to
the same birth years holds the era fixed and lets the form vary, which is the only way the
two come apart. The control population is sampled by the record's own rule — `srsort=random`
over everything it calls a painter/sculptor/photographer — never chosen by this practice,
and the seed of the deterministic subsample is recorded.

**One route, not two.** Everything here is the MediaWiki Action API: CirrusSearch for
counts and samples, `wbgetentities` for claims. The query service is not used at all —
session 3 spent its night against a `429` that named an active outage, and no number below
needs SPARQL. Each number records the route that served it.

**A refusal is not a miss.** Any query the record does not answer is written down as
`None` — `unasked` — and nothing downstream may read it as a zero. Every phase checkpoints
to disk, so a session cut off part way keeps what it asked.

No model writes a number here. The atlas feed is read live and never mirrored.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import sys
import time
import urllib.parse
import urllib.request

API = "https://www.wikidata.org/w/api.php"
FEED = "https://frankbueltge.de/atlas/werke.json"
UA = "ulysses-research/1.0 (artistic research instrument; contact via frankbueltge.de)"

# The properties by which the record says somebody made something. `P170` (creator) is the
# one an artwork normally carries, and it is the narrow measure below — but a media artist's
# piece can be filed as authored, composed, directed, performed or built instead, and
# counting only creator would manufacture the very hole this session is measuring. So every
# person whose creator count is zero is asked again against the union of all six. Asking the
# union only of the zeros is complete and not a shortcut: anyone with a creator statement
# already has one under the union.
MAKING_PROPS = ["P170", "P50", "P86", "P57", "P175", "P84"]
MAKING_NAMES = {
    "P170": "creator", "P50": "author", "P86": "composer",
    "P57": "director", "P175": "performer", "P84": "architect",
}

# The control forms. Three ordinary visual-art occupations with a long cataloguing
# tradition; the point of the comparison is that tradition, so they are named here and
# not derived from anything this practice measured.
CONTROL_FORMS = [
    ("Q1028181", "painter"),
    ("Q1281618", "sculptor"),
    ("Q33231", "photographer"),
]

# How many the record is asked to hand over at random per form, before any filtering, and
# how many of the survivors are actually costed an oeuvre query.
SAMPLE_PER_FORM = 1500
COST_CAP_PER_FORM = 100
SUBSAMPLE_SEED = 20260912

PAUSE = 1.35
TRIES = 4

_state: dict = {}
_state_path: str | None = None
_calls = {"asked": 0, "failed": 0}


# ---------------------------------------------------------------- transport


def api(params: dict, timeout: int = 45) -> dict | None:
    """One Action API call. Returns None when the record did not answer — never {}."""
    p = dict(params)
    p["format"] = "json"
    url = API + "?" + urllib.parse.urlencode(p)
    for attempt in range(TRIES):
        _calls["asked"] += 1
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read().decode("utf-8")
            if not body.strip():
                raise ValueError("empty body")
            d = json.loads(body)
            if "error" in d:
                raise ValueError("api error: " + str(d["error"].get("code")))
            return d
        except Exception as exc:  # noqa: BLE001 — every failure is the same state: unasked
            _calls["failed"] += 1
            if attempt == TRIES - 1:
                print(f"    unasked: {exc}", file=sys.stderr)
                return None
            time.sleep(PAUSE * (2**attempt))
    return None


def cirrus_total(search: str) -> int | None:
    """How many items in the main namespace match. None = the record did not answer."""
    d = api({
        "action": "query", "list": "search", "srsearch": search,
        "srlimit": 1, "srinfo": "totalhits", "srnamespace": 0,
    })
    if d is None:
        return None
    try:
        return int(d["query"]["searchinfo"]["totalhits"])
    except (KeyError, TypeError, ValueError):
        return None


def cirrus_items(search: str, limit: int, sort: str | None = None) -> list[str] | None:
    """Up to `limit` matching item ids. None = unasked; [] = answered, nothing there."""
    out: list[str] = []
    seen: set[str] = set()
    answered = False
    while len(out) < limit:
        step = min(500, limit - len(out))
        p = {
            "action": "query", "list": "search", "srsearch": search,
            "srlimit": step, "srnamespace": 0,
        }
        if sort:
            p["srsort"] = sort
        else:
            p["sroffset"] = len(out)
        d = api(p)
        if d is None:
            return out if answered else None
        answered = True
        rows = (d.get("query") or {}).get("search") or []
        fresh = [r["title"] for r in rows if r["title"] not in seen]
        for q in fresh:
            seen.add(q)
        out.extend(fresh)
        if not rows or (not sort and "continue" not in d):
            break
        if sort and not fresh:
            break  # random sort has stopped handing over anything new
        time.sleep(PAUSE)
    return out[:limit]


WANTED_PROPS = ("P569", "P570", "P106", "P800", "P31", "P170", "P571", "P21")


def entities(qids: list[str]) -> dict[str, dict] | None:
    """Claims, sitelink count and statement count for up to 50 items per call."""
    if not qids:
        return {}
    d = api({
        "action": "wbgetentities", "ids": "|".join(qids),
        "props": "claims|sitelinks|labels|descriptions", "languages": "en",
        "sitefilter": "enwiki",
    })
    if d is None:
        return None
    out: dict[str, dict] = {}
    for qid, ent in (d.get("entities") or {}).items():
        if "missing" in ent:
            out[qid] = {"missing": True}
            continue
        claims = ent.get("claims") or {}
        picked: dict[str, list] = {}
        for prop in WANTED_PROPS:
            vals = []
            for st in claims.get(prop, []) or []:
                dv = ((st.get("mainsnak") or {}).get("datavalue") or {}).get("value")
                if isinstance(dv, dict) and "id" in dv:
                    vals.append(dv["id"])
                elif isinstance(dv, dict) and "time" in dv:
                    vals.append(dv["time"])
                elif isinstance(dv, str):
                    vals.append(dv)
            if vals:
                picked[prop] = vals
        out[qid] = {
            "label_en": ((ent.get("labels") or {}).get("en") or {}).get("value"),
            "description_en": ((ent.get("descriptions") or {}).get("en") or {}).get("value"),
            "claims": picked,
            "n_properties": len(claims),
            "n_statements": sum(len(v or []) for v in claims.values()),
            "sitelinks": len(ent.get("sitelinks") or {}),
        }
    return out


def entities_many(qids: list[str], label: str) -> dict[str, dict]:
    """Batched `entities`, recording which ids went unasked rather than dropping them."""
    out: dict[str, dict] = {}
    unasked: list[str] = []
    batches = [qids[i:i + 50] for i in range(0, len(qids), 50)]
    for i, batch in enumerate(batches, 1):
        got = entities(batch)
        if got is None:
            unasked.extend(batch)
        else:
            out.update(got)
        print(f"  {label} entities {i}/{len(batches)}", file=sys.stderr)
        time.sleep(PAUSE)
    if unasked:
        out["_unasked"] = {"ids": unasked}
    return out


# ---------------------------------------------------------------- checkpoint


def state_load(path: str) -> None:
    global _state_path
    _state_path = path
    if os.path.exists(path):
        _state.update(json.load(open(path, encoding="utf-8")))
        print(f"resumed: {sorted(_state.keys())}", file=sys.stderr)


def state_save() -> None:
    if _state_path:
        tmp = _state_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(_state, fh, ensure_ascii=False)
        os.replace(tmp, _state_path)


def phase(name: str, fn):
    """Run a phase once and keep its result; a resumed session skips what it holds."""
    if name in _state:
        print(f"phase {name}: held", file=sys.stderr)
        return _state[name]
    print(f"phase {name}: asking", file=sys.stderr)
    _state[name] = fn()
    state_save()
    return _state[name]


# ---------------------------------------------------------------- the work


def oeuvre_counts(qids: list[str], label: str) -> dict[str, int | None]:
    """For each person: how many items in the record name them as creator (P170)."""
    out: dict[str, int | None] = {}
    for i, q in enumerate(qids, 1):
        out[q] = cirrus_total(f"haswbstatement:P170={q}")
        if i % 25 == 0 or i == len(qids):
            print(f"  {label} oeuvre {i}/{len(qids)}", file=sys.stderr)
        time.sleep(PAUSE)
    return out


def repair(counts: dict[str, int | None], label: str) -> dict[str, int | None]:
    """Ask again, once, for everything the record did not answer the first time.

    A refusal is a state of this instrument, not of the record's holdings, so it is worth
    one more attempt in a later pass — when the endpoint's mood has moved on. What is still
    unanswered after this stays `None`, and every count downstream reports it as unasked
    beside an assumption-free interval rather than folding it into a zero.
    """
    missing = [q for q, v in counts.items() if v is None]
    if not missing:
        return {}
    print(f"  {label} repair: {len(missing)} unanswered, asking again", file=sys.stderr)
    return {k: v for k, v in oeuvre_counts(missing, label + "-repair").items()
            if v is not None}


def birth_year(ent: dict) -> int | None:
    """The year of P569, or None. Only the year; nothing here needs a finer grain."""
    for t in (ent.get("claims") or {}).get("P569", []) or []:
        if isinstance(t, str) and len(t) > 5:
            try:
                return int(t[1:5]) * (-1 if t[0] == "-" else 1)
            except ValueError:
                continue
    return None


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--prior-probe", required=True,
                    help="the committed probe of 2026-09-11; the 222 are re-derived from it")
    ap.add_argument("--out", required=True)
    ap.add_argument("--state", default=None)
    ap.add_argument("--sample", type=int, default=SAMPLE_PER_FORM)
    ap.add_argument("--cap", type=int, default=COST_CAP_PER_FORM)
    args = ap.parse_args()

    state_load(args.state or (args.out + ".state"))

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import record  # noqa: PLC0415 — the grading rule is imported, never re-typed

    prior = json.load(open(args.prior_probe, encoding="utf-8"))
    graded = [{**a, **record.grade_artist(a, prior)} for a in prior["artists"]]
    persons = [a for a in graded if a["rung"] == "person"]
    print(f"atlas artists resolved to a person or group: {len(persons)}", file=sys.stderr)

    # The feed, live, hashed, never written into this repository.
    def feed():
        req = urllib.request.Request(FEED, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read()
        d = json.loads(raw.decode("utf-8"))
        per: dict[str, list] = {}
        for e in d["entries"]:
            per.setdefault(e.get("artist") or "", []).append(
                {"title": e.get("title"), "year": e.get("year")}
            )
        return {
            "sha256": hashlib.sha256(raw).hexdigest(),
            "count": d.get("count"),
            "entries": len(d["entries"]),
            "by_artist": per,
        }

    feed_state = phase("feed", feed)

    # 222 artist strings do not give 222 items: two atlas artists can resolve to one
    # person. The distinct items are what the record is asked about, and the collapse is
    # reported rather than smoothed over — it is the 09-11 unit problem on the other side.
    qids = sorted({a["qid"] for a in persons})
    atlas_ent = phase("atlas_entities", lambda: entities_many(qids, "atlas"))
    atlas_oeuvre = dict(phase("atlas_oeuvre", lambda: oeuvre_counts(qids, "atlas")))
    atlas_oeuvre.update(phase("atlas_oeuvre_repair",
                              lambda: repair(atlas_oeuvre, "atlas")))

    # The works the record does credit to them, capped and with the cap recorded, so the
    # dates below are a sample of a known shape rather than a silent truncation.
    def credited():
        out = {}
        for q in qids:
            n = atlas_oeuvre.get(q)
            if not n:
                continue
            items = cirrus_items(f"haswbstatement:P170={q}", min(50, n))
            out[q] = {"items": items, "capped": bool(n > 50), "n": n}
            time.sleep(PAUSE)
        return out

    cred = phase("atlas_credited", credited)
    cred_ids = sorted({q for v in cred.values() for q in (v.get("items") or [])})
    cred_ent = phase("atlas_credited_entities",
                     lambda: entities_many(cred_ids, "credited"))

    # The birth-year window the control is cut to: the atlas artists' own, as the record
    # states them. Not a setting — it is read off the population being explained.
    years = [y for q in qids
             if (y := birth_year(atlas_ent.get(q) or {})) is not None and 1000 < y < 2030]
    lo, hi = (min(years), max(years)) if years else (None, None)
    print(f"atlas artist birth years: {len(years)} stated, {lo}–{hi}", file=sys.stderr)

    def control_for(form_qid: str, form_name: str):
        pool = cirrus_items(f"haswbstatement:P106={form_qid}", args.sample, sort="random")
        total = cirrus_total(f"haswbstatement:P106={form_qid}")
        if pool is None:
            return {"form": form_qid, "name": form_name, "unasked": True,
                    "population": total, "pool": [], "entities": {}, "oeuvre": {}}
        ents = entities_many(pool, form_name)
        inwin = []
        for q in pool:
            y = birth_year(ents.get(q) or {})
            if y is not None and lo is not None and lo <= y <= hi:
                inwin.append(q)
        rng = random.Random(SUBSAMPLE_SEED)
        costed = sorted(inwin)
        rng.shuffle(costed)
        costed = sorted(costed[:args.cap])
        oeuvre = oeuvre_counts(costed, form_name)
        oeuvre.update(repair(oeuvre, form_name))
        return {
            "form": form_qid, "name": form_name, "population": total,
            "pool": pool, "pool_asked": len(pool), "entities": ents,
            "in_window": inwin, "costed": costed, "oeuvre": oeuvre,
            "subsample_seed": SUBSAMPLE_SEED, "cap": args.cap,
        }

    controls = {}
    for fq, fn in CONTROL_FORMS:
        controls[fq] = phase("control_" + fq, lambda fq=fq, fn=fn: control_for(fq, fn))

    # The control drawn above is cut to the atlas artists' birth *range*, which is not the
    # same as their birth *distribution*: the record's painters are two generations older
    # than its data artists, and older artists are better catalogued, so that draw flatters
    # the control and understates nothing. Rather than argue about the size of the bias, a
    # second draw is taken per form, stratified to the atlas arm's own birth-decade shares —
    # the weights are read off the population being explained, so there is no setting here
    # either. Both draws are reported; the decade-matched one is the one that answers the
    # question, because it holds the era fixed by construction.
    atlas_decades: dict[int, int] = {}
    for q in qids:
        y = birth_year(atlas_ent.get(q) or {})
        if y is not None and lo is not None and lo <= y <= hi:
            atlas_decades[(y // 10) * 10] = atlas_decades.get((y // 10) * 10, 0) + 1
    atlas_in_window = sum(atlas_decades.values()) or 1

    def matched_for(form_qid: str, form_name: str):
        c = controls[form_qid]
        pool_by_dec: dict[int, list[str]] = {}
        for q in c.get("in_window") or []:
            y = birth_year((c.get("entities") or {}).get(q) or {})
            if y is None:
                continue
            pool_by_dec.setdefault((y // 10) * 10, []).append(q)
        rng = random.Random(SUBSAMPLE_SEED + 1)
        picked: list[str] = []
        shortfall = {}
        for dec, n_atlas in sorted(atlas_decades.items()):
            want = int(round(args.cap * n_atlas / atlas_in_window))
            have = sorted(pool_by_dec.get(dec) or [])
            rng.shuffle(have)
            take = have[:want]
            picked.extend(take)
            if len(take) < want:
                shortfall[str(dec)] = {"wanted": want, "available": len(have)}
        picked = sorted(set(picked))
        oeuvre = oeuvre_counts(picked, form_name + "-matched")
        oeuvre.update(repair(oeuvre, form_name + "-matched"))
        return {
            "form": form_qid, "name": form_name, "costed": picked, "oeuvre": oeuvre,
            "weights": {str(k): v for k, v in sorted(atlas_decades.items())},
            "shortfall": shortfall, "subsample_seed": SUBSAMPLE_SEED + 1,
            "pool_by_decade": {str(k): len(v) for k, v in sorted(pool_by_dec.items())},
        }

    matched = {}
    for fq, fn in CONTROL_FORMS:
        matched[fq] = phase("matched_" + fq, lambda fq=fq, fn=fn: matched_for(fq, fn))

    # The zeros, both arms, asked again against every making property. This is the number
    # the headline rests on, so it is measured at its widest and not at its most convenient.
    # Incremental on purpose: a later run that adds an arm tops this up instead of re-asking
    # nine hundred questions the record has already answered.
    unions: dict[str, int | None] = dict(_state.get("union_zeros") or {})
    want: list[str] = [q for q, v in atlas_oeuvre.items() if v == 0]
    for src in list(controls.values()) + list(matched.values()):
        want += [q for q, v in (src.get("oeuvre") or {}).items() if v == 0]
    need = sorted({q for q in want if unions.get(q) is None})
    if need:
        print(f"  union over {len(MAKING_PROPS)} making properties: {len(need)} to ask "
              f"({len(unions)} held)", file=sys.stderr)
        for i, q in enumerate(need, 1):
            clause = "haswbstatement:" + "|".join(f"{p}={q}" for p in MAKING_PROPS)
            unions[q] = cirrus_total(clause)
            if unions[q] is None:  # one retry, then it stays unasked
                time.sleep(PAUSE)
                unions[q] = cirrus_total(clause)
            if i % 25 == 0 or i == len(need):
                print(f"  union {i}/{len(need)}", file=sys.stderr)
            time.sleep(PAUSE)
        _state["union_zeros"] = unions
        state_save()

    occ_ids = sorted({
        o for src in [atlas_ent] + [c["entities"] for c in controls.values()]
        for q, e in src.items() if q != "_unasked"
        for o in ((e.get("claims") or {}).get("P106") or [])
    })
    occ_labels = phase("occupation_labels", lambda: entities_many(occ_ids, "occupations"))

    out = {
        "probed_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "route": {
            "all_numbers": "MediaWiki Action API (CirrusSearch + wbgetentities)",
            "sparql_used": False,
            "why": "session 3 met a 429 naming an active query-service outage; no number "
                   "here needs SPARQL, so the query service was not asked at all",
        },
        "second_record": {
            "name": "Wikidata", "api": API, "licence": "CC0-1.0",
            "why": "its inclusion rule predates this atlas and ignores it (session 3)",
        },
        "prior_probe": os.path.basename(args.prior_probe),
        "feed": {k: v for k, v in feed_state.items() if k != "by_artist"},
        "feed_by_artist": feed_state["by_artist"],
        "atlas_artists": [
            {"artist": a["artist"], "qid": a["qid"], "n_candidates": a["n_candidates"]}
            for a in persons
        ],
        "artist_strings": len(persons),
        "artist_items": len(qids),
        "atlas_entities": atlas_ent,
        "atlas_oeuvre": atlas_oeuvre,
        "atlas_credited": cred,
        "atlas_credited_entities": cred_ent,
        "birth_window": {"lo": lo, "hi": hi, "stated": len(years), "of": len(qids)},
        "controls": controls,
        "matched": matched,
        "atlas_decades": {str(k): v for k, v in sorted(atlas_decades.items())},
        "occupation_labels": {
            q: (e.get("label_en") if isinstance(e, dict) else None)
            for q, e in occ_labels.items() if q != "_unasked"
        },
        "control_forms": [{"qid": q, "name": n} for q, n in CONTROL_FORMS],
        "union_zeros": unions,
        "making_props": MAKING_PROPS,
        "making_names": MAKING_NAMES,
        "calls": dict(_calls),
    }
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False)
    print(f"wrote {args.out}  calls={_calls}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

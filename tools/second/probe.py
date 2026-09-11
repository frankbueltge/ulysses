#!/usr/bin/env python3
"""probe.py — ask a second, independently built record whether it holds these works.

Cycle 003 session 2 ended on a question this instrument exists to answer. Manski
§3.2.2, restating Duncan & Davis (1953), gives the polar case for a quantity that a
single record cannot pin down: **with a second, independently constructed record the
answer is bounded; without one it is not bounded at all.** The atlas of data art is one
record. This asks whether a second one exists in a form that could bound anything.

The second record chosen is **Wikidata** — the largest open, machine-readable record of
works and people in the world, built by a community that has never heard of this atlas,
under an inclusion rule (notability) written before it and independently of it. That
independence is the whole reason for choosing it; its coverage is the thing measured.

What this does, and nothing else:

  1. For every entry in the atlas feed, search the second record for the **work** by its
     title, and keep every candidate whose label or alias equals the title exactly after
     normalisation. No fuzzy matching, no model, no judgement.
  2. For every distinct artist string in the feed, the same for the **person or group**.
  3. For the candidates it kept, fetch the statements a reader needs to decide whether
     the match is real and whether the item is classed as art at all: P31 instance of,
     P170 creator, P571 inception, P136 genre, P135 movement, P186 material,
     P1343 described by source, P279 subclass of.
  4. Count how many items the second record holds under each of the three classes that
     come closest to naming this field — there is no `data art` item in Wikidata, which
     is itself part of the answer.

**Why every request goes through the query service and none through the entity API.**
The first version of this instrument called `wbsearchentities` once per title. The
endpoint answered 429 after some two hundred calls and kept answering 429, which would
have left a probe with silent holes in it — absence reported where there was only a rate
limit. The query service runs the same entity search server-side (`wikibase:mwapi`,
`EntitySearch`) and takes twenty titles per query, so the whole probe is some sixty
requests rather than nine hundred and fifty. Nothing about what counts as a match
changed; only how many times this practice knocks.

It writes a raw probe record and decides nothing. The matching rules, the coverage
arithmetic and every published number live in `record.py`, which takes this file and the
feed and touches no network at all.

Usage:  python3 tools/second/probe.py --feed <werke.json> --out <probe.json>
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

SPARQL = "https://query.wikidata.org/sparql"
# How many times one batch is re-offered before the run gives up on it. Set from the
# command line: patient when there is time, short when the session has to land.
TRIES = 40
# A floor on the seconds between any two requests. The endpoint states its own ceiling
# in the body of a refusal — on the night this was written, "Aggressively rate-limiting
# to 1 req / min - this rule was created during active wdqs outage" — and an instrument
# that keeps knocking faster than a host has said it can answer is not measuring, it is
# just being refused. Set from the command line and recorded in the probe.
MIN_INTERVAL = 0.0
_LAST_CALL = [0.0]
# Whatever the endpoint said about why it was refusing, kept verbatim as evidence.
THROTTLE_NOTICE: list[str] = []
UA = "ulysses-research/1.0 (artistic research instrument; contact via frankbueltge.de)"

# Properties fetched for every kept candidate. Nothing else is read from the entity.
PROPS = ["P31", "P170", "P571", "P136", "P135", "P186", "P1343", "P279"]

# Languages in which a label or alias may carry the match. A work catalogued here under
# its Spanish or German title must not count as absent from the second record because
# the second record files it under the same title in the same language.
LANGS = ["en", "de", "fr", "es", "pt", "it", "nl"]

# The three classes nearest this field. There is no `data art` item in Wikidata; these
# are what a second catalogue would have to be constituted from if one could be.
NEAR_CLASSES = {
    "Q6031007": "information art",
    "Q378604": "new media art",
    "Q1502032": "generative art",
}


def normalise(s: str) -> str:
    """The one matching rule, stated once and applied everywhere.

    Decompose, drop combining marks, fold typographic punctuation to ASCII, lowercase,
    keep only letters, digits and single spaces. Deliberately blunt: a rule a reader can
    apply by hand to any pair and get the same answer this instrument got.
    """
    if not s:
        return ""
    s = s.replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"')
    s = s.replace("–", "-").replace("—", "-").replace("−", "-")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    out = [c if c.isalnum() else " " for c in s]
    return " ".join("".join(out).split())


def _lit(s: str) -> str:
    """A SPARQL string literal. Quotes and backslashes escaped, control bytes dropped."""
    s = "".join(c for c in s if c >= " " or c == " ")
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


API = "https://www.wikidata.org/w/api.php"


def api_get(params: dict, timeout: int = 30) -> dict | None:
    """The search index on the wiki itself — a different service from the query service.

    Used only as a fallback, and only for counts, when the query service is refusing.
    Recorded as such: every number this instrument publishes says which route served it.
    """
    q = dict(params)
    q["format"] = "json"
    url = API + "?" + urllib.parse.urlencode(q)
    for i in range(4):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": UA, "Accept": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=timeout) as fh:
                return json.load(fh)
        except Exception:
            time.sleep(3 * (i + 1))
    return None


def cirrus_count(search: str) -> int | None:
    d = api_get(
        {
            "action": "query",
            "list": "search",
            "srsearch": search,
            "srnamespace": 0,
            "srlimit": 1,
        }
    )
    if not d:
        return None
    return ((d.get("query") or {}).get("searchinfo") or {}).get("totalhits")


def cirrus_items(search: str, limit: int = 10) -> list[str] | None:
    d = api_get(
        {
            "action": "query",
            "list": "search",
            "srsearch": search,
            "srnamespace": 0,
            "srlimit": limit,
        }
    )
    if not d:
        return None
    return [r["title"] for r in ((d.get("query") or {}).get("search") or [])]


def entity_data(qid: str) -> dict | None:
    """One entity, from the static entity-data endpoint rather than any query service."""
    url = f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"
    for i in range(3):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": UA, "Accept": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=30) as fh:
                d = json.load(fh)
            e = list((d.get("entities") or {}).values())[0]
            return {
                "qid": qid,
                "label_en": ((e.get("labels") or {}).get("en") or {}).get("value"),
                "description_en": (
                    ((e.get("descriptions") or {}).get("en") or {}).get("value")
                ),
                "P31": [
                    st["mainsnak"]["datavalue"]["value"]["id"]
                    for st in (e.get("claims") or {}).get("P31", [])
                    if st.get("mainsnak", {}).get("datavalue")
                ],
            }
        except Exception:
            time.sleep(3 * (i + 1))
    return None


def sparql(query: str, tries: int | None = None, timeout: int = 120,
           soft: bool = False) -> list[dict] | None:
    """One shared retry path. A public endpoint that answers 429 or 503 is answering;
    the instrument waits rather than dropping the batch, because a probe with silent
    holes would report absence where there was only impatience.

    Measured on the night this was written: at one request every twenty seconds, about
    half are refused with a generic anti-bot page carrying `Retry-After: 1000`, and the
    very next attempt a few seconds later usually succeeds. The header is a constant,
    not a measurement of when this endpoint will serve again, so the wait is capped at
    half a minute and the attempt is repeated. Nothing is dropped: a batch that never
    succeeds raises, and a probe that raises is a probe that did not lie about coverage.
    """
    if tries is None:
        tries = TRIES
    url = SPARQL + "?" + urllib.parse.urlencode({"query": query, "format": "json"})
    last = None
    for i in range(tries):
        gap = MIN_INTERVAL - (time.time() - _LAST_CALL[0])
        if gap > 0:
            time.sleep(gap)
        _LAST_CALL[0] = time.time()
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": UA,
                    "Accept": "application/sparql-results+json",
                },
            )
            with urllib.request.urlopen(req, timeout=timeout) as fh:
                return json.load(fh)["results"]["bindings"]
        except urllib.error.HTTPError as exc:
            last = exc
            print(f"  . HTTP {exc.code} (attempt {i + 1})", file=sys.stderr, flush=True)
            if exc.code == 429:
                try:
                    body = exc.read().decode("utf-8", "replace")
                except Exception:
                    body = ""
                for line in body.splitlines():
                    line = line.strip()
                    if "rate-limit" in line.lower() and line not in THROTTLE_NOTICE:
                        THROTTLE_NOTICE.append(line[:300])
                        print(f"  . the endpoint says: {line[:160]}", file=sys.stderr,
                              flush=True)
            if exc.code in (429, 503):
                time.sleep(min(90, 8 + 6 * i))
            elif exc.code == 400:
                print("  ! malformed query, skipped", file=sys.stderr)
                return None
            else:
                time.sleep(4 * (i + 1))
        except Exception as exc:
            last = exc
            print(f"  . {type(exc).__name__} (attempt {i + 1})", file=sys.stderr,
                  flush=True)
            time.sleep(4 * (i + 1))
    if soft:
        print(f"  ~ gave up after {tries} tries; falling back", file=sys.stderr,
              flush=True)
        return None
    raise RuntimeError(f"failed after {tries} tries\n{last}")


def qid(uri: str) -> str:
    return uri.rsplit("/", 1)[-1]


def search_batch(terms: list[str]) -> dict[str, list[str]]:
    """Entity search, run inside the query service, for up to a few dozen terms."""
    vals = " ".join(_lit(t) for t in terms)
    q = f"""SELECT ?term ?item WHERE {{
  VALUES ?term {{ {vals} }}
  SERVICE wikibase:mwapi {{
    bd:serviceParam wikibase:endpoint "www.wikidata.org" .
    bd:serviceParam wikibase:api "EntitySearch" .
    bd:serviceParam mwapi:search ?term .
    bd:serviceParam mwapi:language "en" .
    bd:serviceParam mwapi:limit "25" .
    ?item wikibase:apiOutputItem mwapi:item .
  }}
}}"""
    rows = sparql(q)
    out: dict[str, list[str]] = {t: [] for t in terms}
    if rows is None:
        return out
    for r in rows:
        t = r["term"]["value"]
        out.setdefault(t, []).append(qid(r["item"]["value"]))
    return out


def names_batch(qids: list[str]) -> dict[str, dict]:
    """Every label and alias in the probed languages, plus the English description."""
    vals = " ".join(f"wd:{q}" for q in qids)
    langs = ",".join(f'"{l}"' for l in LANGS)
    q = f"""SELECT ?item ?name ?kind ?desc WHERE {{
  VALUES ?item {{ {vals} }}
  {{ ?item rdfs:label ?name . BIND("label" AS ?kind) }}
  UNION
  {{ ?item skos:altLabel ?name . BIND("alias" AS ?kind) }}
  FILTER(LANG(?name) IN ({langs}))
  OPTIONAL {{ ?item schema:description ?desc . FILTER(LANG(?desc) = "en") }}
}}"""
    rows = sparql(q)
    out: dict[str, dict] = {q_: {"names": [], "desc_en": None} for q_ in qids}
    if rows is None:
        return out
    for r in rows:
        k = qid(r["item"]["value"])
        rec = out.setdefault(k, {"names": [], "desc_en": None})
        n = r["name"]["value"]
        if n not in rec["names"]:
            rec["names"].append(n)
        if r.get("desc") and not rec["desc_en"]:
            rec["desc_en"] = r["desc"]["value"]
    return out


def claims_batch(qids: list[str]) -> dict[str, dict]:
    vals = " ".join(f"wd:{q}" for q in qids)
    props = " ".join(f"wdt:{p}" for p in PROPS)
    q = f"""SELECT ?item ?p ?v WHERE {{
  VALUES ?item {{ {vals} }}
  VALUES ?p {{ {props} }}
  ?item ?p ?v .
}}"""
    rows = sparql(q)
    out: dict[str, dict] = {q_: {} for q_ in qids}
    if rows is None:
        return out
    for r in rows:
        k = qid(r["item"]["value"])
        p = qid(r["p"]["value"])
        v = r["v"]["value"]
        if v.startswith("http://www.wikidata.org/entity/"):
            v = qid(v)
        out.setdefault(k, {}).setdefault(p, [])
        if v not in out[k][p]:
            out[k][p].append(v)
    return out


def label_batch(qids: list[str]) -> dict[str, str]:
    vals = " ".join(f"wd:{q}" for q in qids)
    q = f"""SELECT ?item ?l WHERE {{
  VALUES ?item {{ {vals} }}
  ?item rdfs:label ?l . FILTER(LANG(?l) = "en")
}}"""
    rows = sparql(q) or []
    return {qid(r["item"]["value"]): r["l"]["value"] for r in rows}


def chunked(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i : i + n]


# --------------------------------------------------------------------------------- #
# Checkpointing
# --------------------------------------------------------------------------------- #
#
# Every phase writes what it has to one file on disk after every batch. The endpoint
# refuses roughly half of all requests on the night this was written, so a run that had
# to start over would spend a shared public budget twice for nothing — and a probe that
# gives up half way and reports the rest as absent would be worse than no probe at all.

STATE: dict = {"hits": {}, "names": {}, "claims": {}, "labels": {}, "near": None,
               "notice": []}
STATE_PATH: str | None = None


def state_load(path: str | None) -> None:
    global STATE_PATH
    STATE_PATH = path
    if not path:
        return
    try:
        got = json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError):
        return
    for k in STATE:
        if k in got and got[k] is not None:
            STATE[k] = got[k]
    print(
        "  resumed: "
        + ", ".join(
            f"{k} {len(v) if isinstance(v, dict) else 'yes'}"
            for k, v in STATE.items()
            if v
        ),
        file=sys.stderr,
    )


def state_save() -> None:
    for line in THROTTLE_NOTICE:
        if line not in STATE["notice"]:
            STATE["notice"].append(line)
    if not STATE_PATH:
        return
    tmp = STATE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(STATE, fh, ensure_ascii=False)
    import os

    os.replace(tmp, STATE_PATH)


def phase(name: str, keys: list[str], size: int, fn, pause: float,
          partial_ok: bool = False) -> dict:
    """Run one batched phase, skipping what the checkpoint already holds.

    A batch the endpoint never serves is written down as **refused** — the key is stored
    as `null`, which is a different thing from a key that was asked and had no answer.
    Everything downstream keeps that distinction, so a page built from a throttled probe
    reports how much of the catalogue it could ask about instead of reporting the part
    it could not reach as absent. With `partial_ok` off, a refusal that never clears
    stops the run instead.
    """
    store = STATE[name]
    todo = [k for k in keys if k not in store]
    if not todo:
        print(f"  {name}: all {len(keys)} already held", file=sys.stderr, flush=True)
        return store
    done = 0
    for batch in chunked(todo, size):
        try:
            got = fn(batch)
        except RuntimeError as exc:
            if not partial_ok:
                raise
            print(f"  ! {name}: {len(batch)} refused and recorded as unasked "
                  f"({exc.__class__.__name__})", file=sys.stderr, flush=True)
            got = None
        for k in batch:
            if got is None:
                store[k] = None
            else:
                store[k] = got.get(k, [] if name == "hits" else None)
        done += len(batch)
        state_save()
        print(f"  {name} {done}/{len(todo)}", file=sys.stderr, flush=True)
        time.sleep(pause)
    return store


def near_class_counts() -> dict:
    """How large a catalogue could be constituted from the second record's own classes.

    One count per property, never a union: a union over `P31` on a broad class times out
    on the public endpoint, and a query that sometimes returns null is not a measurement.
    """
    out = {}
    routes: dict[str, str] = {}

    def count(key: str, q: str, cirrus: str | None):
        """One number, and the route that served it recorded beside it.

        A fallback route is only allowed where it answers the **same** question. The
        class counts are statement counts and both routes count statements, so the
        search index may stand in for the query service there. The label question is an
        exact string match on a label, and the search index cannot answer it — it
        answers a weaker one, whether a phrase occurs anywhere in a label or alias. So
        that question has no fallback: unanswered is written down as unanswered, and the
        weaker evidence is reported separately as the different thing it is.
        """
        rows = sparql(q, tries=min(TRIES, 4), timeout=90, soft=True)
        if rows is not None:
            routes[key] = "query service"
            return int(rows[0]["c"]["value"]) if rows else 0
        if cirrus is None:
            routes[key] = "not answered"
            return None
        n = cirrus_count(cirrus)
        routes[key] = "search index" if n is not None else "neither served"
        return n

    for q_, name in NEAR_CLASSES.items():
        row = {"name": name}
        for prop in ("P136", "P135", "P31"):
            row[prop] = count(
                f"{q_}:{prop}",
                f"SELECT (COUNT(DISTINCT ?w) AS ?c) WHERE {{ ?w wdt:{prop} wd:{q_} . }}",
                f"haswbstatement:{prop}={q_}",
            )
        out[q_] = row

    # Is there an item called `data art` at all? The exact question is an exact label
    # match, which only the query service can answer. When it cannot, the search index
    # answers a weaker question — which items carry the phrase anywhere in a label or
    # alias — and every one of them is then fetched from the static entity endpoint and
    # written down, so a reader can see for themselves what they are.
    lit: dict[str, int | None] = {}
    found: list[dict] = []
    for lang in LANGS[:4]:
        lit[lang] = count(
            f"label:data art@{lang}",
            "SELECT (COUNT(DISTINCT ?w) AS ?c) WHERE { "
            f'?w rdfs:label "data art"@{lang} . }}',
            None,
        )
        for qid in (cirrus_items(f'inlabel:"data art"@{lang}') or []):
            if any(f["qid"] == qid for f in found):
                continue
            ent = entity_data(qid)
            if ent:
                found.append({**ent, "language": lang})
            time.sleep(0.5)
    out["_literal_data_art_items"] = {
        "name": "data art",
        "by_language": lit,
        "phrase_carriers": found,
    }
    out["_routes"] = routes
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--feed", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--batch", type=int, default=20)
    ap.add_argument("--pause", type=float, default=1.0)
    ap.add_argument("--limit", type=int, default=0, help="0 = all entries")
    ap.add_argument("--cache", default=None,
                    help="checkpoint file; every phase resumes from it")
    ap.add_argument("--min-interval", type=float, default=0.0,
                    help="floor in seconds between any two requests")
    ap.add_argument("--tries", type=int, default=40,
                    help="attempts per batch before it counts as refused")
    ap.add_argument("--partial-ok", action="store_true",
                    help="record a batch the endpoint never serves as unasked and go on")
    args = ap.parse_args()

    global TRIES, MIN_INTERVAL
    TRIES = args.tries
    MIN_INTERVAL = args.min_interval

    feed = json.load(open(args.feed, encoding="utf-8"))
    entries = feed["entries"]
    if args.limit:
        entries = entries[: args.limit]

    titles = [(e.get("title") or "").strip() for e in entries]
    artists = sorted({(e.get("artist") or "").strip() for e in entries} - {""})

    # ---- 1. search ------------------------------------------------------------------
    state_load(args.cache)
    terms = sorted({t for t in titles if t} | set(artists))
    hits = phase("hits", terms, args.batch, search_batch, args.pause, args.partial_ok)

    all_q = sorted({q for t in terms for q in (hits.get(t) or [])})
    unasked_search = sorted(t for t in terms if hits.get(t) is None)
    print(f"  {len(all_q)} distinct candidates", file=sys.stderr, flush=True)

    # ---- 2. names, claims -----------------------------------------------------------
    names = phase("names", all_q, 300, names_batch, args.pause, args.partial_ok)
    claims = phase("claims", all_q, 300, claims_batch, args.pause, args.partial_ok)

    # ---- 3. keep only the exact normalised matches -----------------------------------
    def resolved(term: str) -> bool:
        """True only when the whole chain for this term was served.

        A term is answered when the search served it AND every candidate it returned had
        its names and its statements served too. A refusal anywhere in that chain would
        otherwise look exactly like a work the second record does not hold, which is the
        one error this instrument exists to avoid.
        """
        hs = hits.get(term)
        if hs is None:
            return False
        return all(
            names.get(q) is not None and claims.get(q) is not None for q in hs
        )

    def kept_for(name: str) -> list[dict]:
        target = normalise(name)
        out = []
        for q_ in (hits.get(name) or []):
            rec = names.get(q_) or {"names": [], "desc_en": None}
            match = next((n for n in rec["names"] if normalise(n) == target), None)
            if match is None:
                continue
            out.append(
                {
                    "qid": q_,
                    "matched_text": match,
                    "label_en": next(
                        (n for n in rec["names"] if n), None
                    ),
                    "description": rec["desc_en"],
                }
            )
        return out

    works = []
    for i, e in enumerate(entries):
        t = (e.get("title") or "").strip()
        works.append(
            {
                "index_in_feed": i,
                "title": t,
                "artist": (e.get("artist") or "").strip(),
                "year": e.get("year"),
                "asked": resolved(t),
                "searched_hits": len(hits.get(t) or []),
                "candidates": kept_for(t),
            }
        )

    artist_rows = [
        {
            "artist": a,
            "asked": resolved(a),
            "searched_hits": len(hits.get(a) or []),
            "candidates": kept_for(a),
        }
        for a in artists
    ]

    kept_q = sorted(
        {c["qid"] for w in works for c in w["candidates"]}
        | {c["qid"] for a in artist_rows for c in a["candidates"]}
    )
    ents = {
        q_: {
            "label_en": (names.get(q_) or {}).get("names", [None])[0],
            "description_en": (names.get(q_) or {}).get("desc_en"),
            "claims": claims.get(q_, {}),
        }
        for q_ in kept_q
    }

    # Only the creators are labelled. The other statements are kept as identifiers and
    # never turned into prose, so fetching their labels would spend a shared public
    # budget on text nothing reads.
    referenced = sorted(
        {
            v
            for q_ in kept_q
            for v in (claims.get(q_) or {}).get("P170", []) or []
            if isinstance(v, str) and v.startswith("Q") and v[1:].isdigit()
        }
    )
    lab = {
        k: v
        for k, v in phase(
            "labels", referenced, 400,
            lambda b: {k: v for k, v in label_batch(b).items()},
            args.pause, args.partial_ok,
        ).items()
        if v
    }

    if STATE.get("near") is None:
        try:
            STATE["near"] = near_class_counts()
        except RuntimeError:
            if not args.partial_ok:
                raise
            STATE["near"] = None
        state_save()

    probe = {
        "probed_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "second_record": {
            "name": "Wikidata",
            "endpoint": SPARQL,
            "search_api": "wikibase:mwapi EntitySearch, run inside the query service",
            "licence": "CC0-1.0",
            "why": (
                "largest open machine-readable record of works and people; its "
                "inclusion rule (notability) was written before this atlas and "
                "independently of it"
            ),
        },
        "properties_fetched": PROPS,
        "languages_matched": LANGS,
        "endpoint_said": list(STATE.get("notice") or THROTTLE_NOTICE),
        "min_interval_seconds": MIN_INTERVAL,
        "reach": {
            "terms": len(terms),
            "asked": sum(1 for t in terms if resolved(t)),
            "unasked": sum(1 for t in terms if not resolved(t)),
            "unasked_at_search": len(unasked_search),
            "note": (
                "a term is unasked when the query service never served the batch it "
                "was in; it is not the same as a term that was asked and matched "
                "nothing, and nothing downstream treats it as one"
            ),
        },
        "near_classes": STATE["near"],
        "works": works,
        "artists": artist_rows,
        "entities": ents,
        "labels": lab,
    }
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(probe, fh, ensure_ascii=False, indent=1, sort_keys=True)
        fh.write("\n")
    print(f"wrote {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

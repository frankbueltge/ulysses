#!/usr/bin/env python3
"""knock.py — the two-knock reachability instrument.

For each target it knocks twice at the same URL:

  A. THE INSTRUMENT — one ordinary HTTP GET, honest research User-Agent, no
     JavaScript. This is what any automated reading apparatus receives.
  B. THE READER — the same URL in a real browser engine, JavaScript executed,
     waited out. This is what a person receives.

It records what arrives at each knock: status, bytes, words of visible text,
counts of media elements, and a LINE PROFILE — the lengths of the wrapped
lines of the extracted text, and nothing of their content. The profile is what
the artifact draws. No fetched page text is written to disk or committed; only
counts, profiles, page titles and the URLs.

Politeness: robots.txt is fetched once per host and honoured; at most two page
loads per target; a delay between requests. Nothing is submitted, posted or
written to any site.

Usage: python3 tools/knock/knock.py targets.json out.json
"""

import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from datetime import datetime, timezone

UA_INSTRUMENT = (
    "Ulysses-Atelier-Reachability-Census/1.0 "
    "(+https://github.com/frankbueltge/ulysses; "
    "artistic-research reachability probe; <=2 page loads per URL)"
)
# The reader knock uses the browser engine's own default User-Agent. No
# User-Agent of the instrument knock is ever disguised as a browser: a probe
# that lies about who is knocking cannot measure what happens when a machine
# knocks.

DELAY_S = 2.0
WRAP = 64
MAX_PROFILE_LINES = 600
TIMEOUT = 45

_DROP = re.compile(
    r"<(script|style|noscript|svg|head|template)\b.*?</\1\s*>",
    re.I | re.S,
)
_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")


def visible_text(raw_html: str) -> str:
    """Visible text of an HTML document, as a plain reader of the bytes gets it."""
    body = _DROP.sub(" ", raw_html)
    body = re.sub(r"<!--.*?-->", " ", body, flags=re.S)
    body = _TAG.sub(" ", body)
    return _WS.sub(" ", html.unescape(body)).strip()


def line_profile(text: str, wrap: int = WRAP, cap: int = MAX_PROFILE_LINES):
    """Lengths of the wrapped lines of `text` — its shape, not its content."""
    lines, cur = [], 0
    for word in text.split():
        add = len(word) + (1 if cur else 0)
        if cur + add > wrap:
            lines.append(cur)
            cur = len(word)
            if len(lines) >= cap:
                break
        else:
            cur += add
    if cur and len(lines) < cap:
        lines.append(cur)
    return lines


def count_words(text: str) -> int:
    return len(text.split())


# ---------------------------------------------------------------- robots

_robots_cache = {}


def robots(url: str):
    parts = urllib.parse.urlsplit(url)
    root = f"{parts.scheme}://{parts.netloc}"
    if root in _robots_cache:
        return _robots_cache[root]
    rp = urllib.robotparser.RobotFileParser()
    entry = {"fetched": False, "note": ""}
    try:
        req = urllib.request.Request(
            root + "/robots.txt", headers={"User-Agent": UA_INSTRUMENT}
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            rp.parse(r.read().decode("utf-8", "replace").splitlines())
        entry["fetched"] = True
    except Exception as exc:  # no robots.txt, or unreachable: default allow
        entry["note"] = f"{type(exc).__name__}: {str(exc)[:100]}"
        rp.parse([])
    entry["rp"] = rp
    _robots_cache[root] = entry
    return entry


# ---------------------------------------------------------------- knock A

def knock_instrument(url: str):
    out = {"knock": "instrument", "url": url}
    t0 = time.time()
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA_INSTRUMENT,
            "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
            "Accept-Language": "en",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            raw = r.read().decode("utf-8", "replace")
            out.update(status=r.status, final_url=r.geturl())
    except urllib.error.HTTPError as exc:
        raw = ""
        out.update(status=exc.code, final_url=url, error=f"HTTP {exc.code}")
    except Exception as exc:
        raw = ""
        out.update(status=None, final_url=url,
                   error=f"{type(exc).__name__}: {str(exc)[:140]}")
    text = visible_text(raw) if raw else ""
    title = ""
    m = re.search(r"<title[^>]*>(.*?)</title>", raw, re.I | re.S)
    if m:
        title = _WS.sub(" ", html.unescape(_TAG.sub("", m.group(1)))).strip()[:200]
    out.update(
        seconds=round(time.time() - t0, 2),
        bytes=len(raw.encode("utf-8")),
        words=count_words(text),
        chars=len(text),
        title=title,
        media={
            "img": len(re.findall(r"<img\b", raw, re.I)),
            "video": len(re.findall(r"<video\b", raw, re.I)),
            "audio": len(re.findall(r"<audio\b", raw, re.I)),
            "iframe": len(re.findall(r"<iframe\b", raw, re.I)),
            "canvas": len(re.findall(r"<canvas\b", raw, re.I)),
        },
        profile=line_profile(text),
    )
    return out


# ---------------------------------------------------------------- knock B

_MEDIA_JS = """() => {
  const q = s => document.querySelectorAll(s).length;
  return {
    words_text: document.body ? document.body.innerText : "",
    nodes: document.getElementsByTagName('*').length,
    media: { img: q('img'), video: q('video'), audio: q('audio'),
             iframe: q('iframe'), canvas: q('canvas') },
    title: document.title || ""
  };
}"""


def knock_reader(page, url: str, settle_ms: int):
    out = {"knock": "reader", "url": url}
    t0 = time.time()
    try:
        resp = page.goto(url, wait_until="load", timeout=90_000)
        out["status"] = resp.status if resp else None
        try:
            page.wait_for_load_state("networkidle", timeout=25_000)
        except Exception:
            out["note"] = "network never went idle within 25s"
        page.wait_for_timeout(settle_ms)
        got = page.evaluate(_MEDIA_JS)
        out["final_url"] = page.url
    except Exception as exc:
        out.update(status=None, final_url=url,
                   error=f"{type(exc).__name__}: {str(exc)[:140]}")
        got = {"words_text": "", "nodes": 0,
               "media": {k: 0 for k in ("img", "video", "audio", "iframe", "canvas")},
               "title": ""}
    text = _WS.sub(" ", got.get("words_text") or "").strip()
    out.update(
        seconds=round(time.time() - t0, 2),
        words=count_words(text),
        chars=len(text),
        nodes=got.get("nodes", 0),
        title=(got.get("title") or "").strip()[:200],
        media=got.get("media", {}),
        profile=line_profile(text),
    )
    return out


# ---------------------------------------------------------------- run

def main(targets_path: str, out_path: str):
    from playwright.sync_api import sync_playwright

    with open(targets_path) as fh:
        spec = json.load(fh)
    targets = spec["targets"]
    settle_ms = spec.get("settle_ms", 4000)

    results = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            executable_path=spec.get("chromium"),
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        ctx = browser.new_context(
            viewport={"width": 1440, "height": 1000},
            locale="en-GB",
        )
        page = ctx.new_page()
        for i, t in enumerate(targets, 1):
            url = t["url"]
            rec = dict(t)
            rb = robots(url)
            allowed = rb["rp"].can_fetch(UA_INSTRUMENT, url)
            rec["robots"] = {
                "fetched": rb["fetched"],
                "allows_probe": bool(allowed),
                "note": rb["note"],
            }
            print(f"[{i}/{len(targets)}] {t['id']}  robots_ok={allowed}", flush=True)
            if not allowed:
                rec["skipped"] = "robots.txt disallows this path for our agent"
                results.append(rec)
                continue
            rec["a"] = knock_instrument(url)
            time.sleep(DELAY_S)
            rec["b"] = knock_reader(page, url, settle_ms)
            time.sleep(DELAY_S)
            a, b = rec["a"], rec["b"]
            rec["delivered"] = (
                round(a["words"] / b["words"], 6) if b["words"] else None
            )
            print(f"      A={a['words']:>6}w (HTTP {a['status']})   "
                  f"B={b['words']:>6}w (HTTP {b['status']})   "
                  f"delivered={rec['delivered']}", flush=True)
            results.append(rec)
        browser.close()

    payload = {
        "instrument": "tools/knock/knock.py",
        "run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ua_instrument": UA_INSTRUMENT,
        "wrap": WRAP,
        "settle_ms": settle_ms,
        "delay_between_requests_s": DELAY_S,
        "cohort_note": spec.get("cohort_note", ""),
        "results": results,
    }
    with open(out_path, "w") as fh:
        json.dump(payload, fh, indent=1, sort_keys=True)
    print(f"\nwrote {out_path}  ({len(results)} targets)")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

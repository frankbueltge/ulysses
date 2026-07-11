#!/usr/bin/env python3
# measure.py — the diversity instrument behind "The Closing Loop" (2026-07-11).
# Run from the repository root:  python3 works/2026-07-11-the-closing-loop/measure.py
# Treats journal/*.md as generations of a self-trained corpus and measures whether
# the project is collapsing. Emits per-session diversity + closure metrics.
# Reproducible: same repo -> same numbers (these drive the work's data.json).

import re, os, math, json

# chronological session order (session_no, filename)
ORDER = [
    (1,  "2026-06-28.md"),
    (2,  "2026-06-28-sitzung-2.md"),
    (3,  "2026-06-29.md"),
    (4,  "2026-06-29-sitzung-4.md"),
    (5,  "2026-06-29-sitzung-5.md"),
    (6,  "2026-06-29-sitzung-6.md"),
    (7,  "2026-06-30.md"),
    (8,  "2026-06-30-sitzung-8.md"),
    (9,  "2026-06-30-sitzung-9.md"),
    (10, "2026-06-30-sitzung-10.md"),
    (11, "2026-06-30-sitzung-11.md"),
    (12, "2026-07-01.md"),
    (13, "2026-07-02.md"),
    (14, "2026-07-03.md"),
    (15, "2026-07-03-sitzung-15.md"),
    (16, "2026-07-04.md"),
    (17, "2026-07-05.md"),
    (18, "2026-07-06.md"),
    (19, "2026-07-07.md"),
    (20, "2026-07-09.md"),
    (21, "2026-07-10.md"),
]
JDIR = "journal"

url_re   = re.compile(r'https?://([^/\s)]+)')
word_re  = re.compile(r"[a-z]+")
# self-reference markers (the project citing its own output):
f_re     = re.compile(r'\bF-0\d\d\b')                      # error-register numbers
sess_re  = re.compile(r'\b(?:Session|Sitzung)\s+\d+\b', re.I)
track_re = re.compile(r'\bTrack\s+[ABC]\b|\b[ABC][1-5]\b') # track/station refs
selfpath_re = re.compile(r'genealogie|fehlerkataster|journal/|works/|position-2026')

REPO_HOSTS = ("github.com", "raw.githubusercontent.com", "frankbueltge.de")

cum_types = set()
cum_bigrams = set()
rows = []
prev_tokens_total = 0
for sess, fn in ORDER:
    path = os.path.join(JDIR, fn)
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    low = text.lower()
    tokens = word_re.findall(low)
    n = len(tokens)
    types = set(tokens)
    bigrams = set(zip(tokens, tokens[1:]))
    new_types = types - cum_types
    new_bigrams = bigrams - cum_bigrams

    # external sources: http(s) URLs whose host is NOT the repo itself
    hosts = url_re.findall(text)
    ext_hosts = [h for h in hosts if not any(h.endswith(r) or h==r for r in REPO_HOSTS)]
    ext_domains = set(ext_hosts)

    # self-reference markers
    f_refs    = len(f_re.findall(text))
    sess_refs = len(sess_re.findall(text))
    trk_refs  = len(track_re.findall(text))
    path_refs = len(selfpath_re.findall(text))
    self_total = f_refs + sess_refs + trk_refs + path_refs

    self_noF = sess_refs + trk_refs + path_refs   # self-ref WITHOUT the growing error register
    rows.append({
        "session": sess, "file": fn,
        "tokens": n,
        "types": len(types),
        "new_types": len(new_types),
        "new_type_frac": round(len(new_types)/len(types), 4) if types else 0,
        "cum_types_after": len(cum_types | types),
        "new_bigram_frac": round(len(new_bigrams)/len(bigrams), 4) if bigrams else 0,
        "ext_url_count": len(ext_hosts),
        "ext_distinct_domains": len(ext_domains),
        "ext_url_per_1k": round(1000*len(ext_hosts)/n, 3) if n else 0,
        "f_refs": f_refs, "sess_refs": sess_refs, "trk_refs": trk_refs, "path_refs": path_refs,
        "self_refs": self_total,
        "self_per_1k": round(1000*self_total/n, 3) if n else 0,
        "self_noF_per_1k": round(1000*self_noF/n, 3) if n else 0,
        "closure_index": round(self_total/ (len(ext_hosts)+1), 3),  # self-ref per external URL (+1 smoothing)
        "closure_noF": round(self_noF/ (len(ext_hosts)+1), 3),      # same, F-numbers removed
        "ext_domains_list": sorted(ext_domains),
    })
    cum_types |= types
    cum_bigrams |= bigrams

# Heaps' law fit on cumulative (N, V): V = K N^beta ; log-log linear regression
N = []
V = []
run_tokens = 0
for r in rows:
    run_tokens += r["tokens"]
    N.append(run_tokens)
    V.append(r["cum_types_after"])
lx = [math.log(x) for x in N]
ly = [math.log(y) for y in V]
m = len(lx)
mx = sum(lx)/m; my = sum(ly)/m
beta = sum((lx[i]-mx)*(ly[i]-my) for i in range(m)) / sum((lx[i]-mx)**2 for i in range(m))
logK = my - beta*mx

print("session tokens types newT  newT%  newBigr%  extURL  extDom  ext/1k  self  self/1k  closureIdx")
for r in rows:
    print(f"{r['session']:>3}  {r['tokens']:>6} {r['types']:>5} {r['new_types']:>4}  "
          f"{r['new_type_frac']*100:5.1f}  {r['new_bigram_frac']*100:6.1f}   "
          f"{r['ext_url_count']:>4}   {r['ext_distinct_domains']:>4}  {r['ext_url_per_1k']:>5}  "
          f"{r['self_refs']:>4}  {r['self_per_1k']:>6}   {r['closure_index']:>7}")

print(f"\nHeaps' law fit: beta = {beta:.3f}  K = {math.exp(logK):.2f}  (V = K*N^beta)")
print(f"Total tokens: {N[-1]}   Total vocabulary: {V[-1]}")

# halves comparison: sessions 1-10 vs 12-21 (skip 11 boundary? use 1-11 vs 12-21)
def avg(rs, key): return sum(x[key] for x in rs)/len(rs)
h1 = rows[:11]; h2 = rows[11:]
print("\n--- First half (S1-11) vs second half (S12-21) ---")
for k in ["new_type_frac","ext_url_per_1k","ext_distinct_domains","self_per_1k",
          "self_noF_per_1k","closure_index","closure_noF"]:
    print(f"{k:>20}:  {avg(h1,k):.3f}  ->  {avg(h2,k):.3f}")

print("\n--- self-ref category breakdown (F-num / Session / Track / path) per 1k, halves ---")
for k in ["f_refs","sess_refs","trk_refs","path_refs"]:
    a = 1000*avg(h1,k)/avg(h1,"tokens"); b = 1000*avg(h2,k)/avg(h2,"tokens")
    print(f"{k:>12} per1k:  {a:.3f}  ->  {b:.3f}")

with open("/dev/stdout","w") if False else open("works/2026-07-11-the-closing-loop/data_full.json","w") as fh:
    json.dump({"rows":rows,"beta":beta,"K":math.exp(logK),
               "total_tokens":N[-1],"total_vocab":V[-1]}, fh, indent=2)

#!/usr/bin/env python3
"""Drive the built page in a browser and check what it renders against the record.

A page that has not been run has not been made. This loads `window/index.html`, walks
all 306 addresses, and asserts that what the page shows matches the numbers the closed
studies published — not the numbers this build computed, which would only check the
build against itself.

    python3 check_page.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
PAGE = HERE / "window" / "index.html"

# Published by the closed studies. Sources, in order: 2026-08-14 MEASUREMENT.md (corpus,
# addresses, outcomes), 2026-08-16 MEASUREMENT.md (archive arms), 2026-08-17
# MEASUREMENT.md (warrants), 2026-08-18 MEASUREMENT.md + rescore.json (amendments).
EXPECT = {
    "sections": 290,
    "printing": 250,
    "addresses": 306,
    "occurrences": 1018,
    "hosts": 203,
    "ok": 206,          # 2xx
    "refuse": 63,       # blocked
    "miss": 18,         # 14 4xx + 4 5xx
    "gone": 19,         # network
    # The 2026-08-14 study reserves "failing" for 4xx/5xx/network and reports 42 sections;
    # a 403 is a refusal and is counted apart, everywhere.
    "sections_dead": 42,
    "sections_refused": 88,
    "offloaded": 76,
    "amendments": 449,
    "reopened": 146,
    "scorable": 67,
    "stayed": 26,
    "archA_n": 42, "archA_200": 34, "archA_age": 950.5,
    "archC_n": 81, "archC_200": 78, "archC_age": 21.5,
    "typos": 4,
    "canon_occ": 240,   # 5 + 119 + 55 + 61 correctly-spelled printings that resolve
}

failures: list[str] = []
checks = 0


def check(label: str, got, want) -> None:
    global checks
    checks += 1
    if got != want:
        failures.append(f"{label}: page says {got!r}, the record says {want!r}")


def main() -> None:
    with sync_playwright() as pw:
        # The runtime here pins a browser build the library does not expect; point at
        # the one that is installed rather than downloading a second copy.
        chrome = Path("/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
        browser = pw.chromium.launch(
            executable_path=str(chrome) if chrome.exists() else None,
            args=["--no-sandbox"],
        )
        page = browser.new_page()
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.goto(PAGE.as_uri())
        page.wait_for_selector("#ledger tr")

        if errors:
            failures.append("javascript errors: " + " | ".join(errors))

        # --- the ledger, as a reader sees it ---
        ledger = page.eval_on_selector_all(
            "#ledger tr", "rows => rows.map(r => [...r.cells].map(c => c.innerText.trim()))")
        nums = [int(r[1].replace(",", "")) for r in ledger]
        check("ledger sections", nums[0], EXPECT["sections"])
        check("ledger printing", nums[1], EXPECT["printing"])
        check("ledger addresses", nums[2], EXPECT["addresses"])
        check("ledger 2xx", nums[3], EXPECT["ok"])
        check("ledger blocked", nums[4], EXPECT["refuse"])
        check("ledger 4xx/5xx", nums[5], EXPECT["miss"])
        check("ledger network", nums[6], EXPECT["gone"])
        check("ledger sections with a dead address", nums[7], EXPECT["sections_dead"])
        check("ledger sections with a refusing address", nums[8], EXPECT["sections_refused"])
        check("ledger occurrences in note", f"{EXPECT['occurrences']:,}" in ledger[2][2], True)
        check("ledger hosts in note", f"{EXPECT['hosts']} hosts" in ledger[2][2], True)

        # --- the three deeper readings ---
        deeper = page.eval_on_selector_all(
            "#deeper tr", "rows => rows.map(r => [...r.cells].map(c => c.innerText.trim()))")
        check("warrants offloaded", int(deeper[0][1]), EXPECT["offloaded"])
        check("amendments", int(deeper[2][1].replace(",", "")), EXPECT["amendments"])
        check("reopened in note", f"{EXPECT['reopened']} of 290" in deeper[2][2], True)
        check("stayed", deeper[3][1], f"{EXPECT['stayed']} of {EXPECT['scorable']}")
        check("archive arm A", deeper[5][1], f"{EXPECT['archA_200']} of {EXPECT['archA_n']}")
        check("archive arm A age", f"{EXPECT['archA_age']} days" in deeper[5][2], True)
        check("archive control", deeper[6][1], f"{EXPECT['archC_200']} of {EXPECT['archC_n']}")
        check("archive control age", f"{EXPECT['archC_age']} days" in deeper[6][2], True)

        # --- the four misspellings ---
        check("misspelled routes", page.eval_on_selector_all("#typos tr", "r => r.length"),
              EXPECT["typos"])
        lead = page.eval_on_selector("#typos", "e => e.previousElementSibling.innerText")
        check("correctly-spelled printings", f"printed {EXPECT['canon_occ']} times" in lead, True)
        check("every misspelling is a 404",
              page.eval_on_selector_all("#typos tr td.n", "c => c.map(x => x.innerText.trim())"),
              ["404"] * EXPECT["typos"])
        # The bare heading sits on 263 of the 290 sections and a card that repeats it says
        # nothing; the 27 headings that differ do say something and are kept.
        page.click("#all")
        secs = page.eval_on_selector_all(".card .sec", "e => e.map(x => x.innerText)")
        check("no card repeats the bare corpus heading",
              [s for s in secs if "· INCORPORATION BY REFERENCE ·" in s
               or s.endswith("· INCORPORATION BY REFERENCE")], [])
        kept = {s.split(" · ")[1] for s in secs if " · " in s and "OTHER SECTION" not in s.split(" · ")[1]}
        check("distinguishing headings are kept", len(kept) > 0, True)
        check("and only distinguishing ones",
              [h for h in kept if h.rstrip(".").strip() == "INCORPORATION BY REFERENCE"], [])
        page.click("#reset")

        # --- the instrument: one press, then the whole walk ---
        check("tally empty before asking", page.inner_text("#tally").strip(), "")
        page.click("#ask")
        check("one card after one press", page.eval_on_selector_all(".card", "c => c.length"), 1)
        check("tally counts one", "asked 1 of the 306" in page.inner_text("#tally"), True)

        page.click("#all")
        check("all cards rendered",
              page.eval_on_selector_all(".card", "c => c.length"), EXPECT["addresses"])
        check("every address asked once",
              page.evaluate("new Set([...document.querySelectorAll('.card code')]"
                            ".map(c => c.textContent)).size"), EXPECT["addresses"])
        tally = page.inner_text("#tally")
        for label, n in (("asked", EXPECT["addresses"]), ("handed you something", EXPECT["ok"])):
            check(f"tally {label}", str(n) in tally, True)
        check("grid fully coloured",
              page.eval_on_selector_all(".cell", "c => c.filter(x => x.className !== 'cell').length"),
              EXPECT["addresses"])
        check("grid note closes", page.inner_text("#gridnote"),
              "All 306 asked. The row above is the whole apparatus.")
        check("ask disabled at the end", page.is_disabled("#ask"), True)

        # --- reset returns the page to its opening state ---
        page.click("#reset")
        check("reset clears cards", page.eval_on_selector_all(".card", "c => c.length"), 0)
        check("reset clears grid",
              page.eval_on_selector_all(".cell", "c => c.filter(x => x.className !== 'cell').length"), 0)
        check("reset re-enables", page.is_disabled("#ask"), False)

        # --- the page must reach nothing outside itself ---
        page.close()
        page2 = browser.new_page()
        outside: list[str] = []
        page2.on("request", lambda r: outside.append(r.url) if not r.url.startswith("file:") else None)
        page2.goto(PAGE.as_uri())
        page2.wait_for_selector("#ledger tr")
        check("no external request", outside, [])

        browser.close()

    if failures:
        print(f"FAIL — {len(failures)} of {checks} checks")
        for f in failures:
            print("  ·", f)
        sys.exit(1)
    print(f"OK — {checks} checks, every figure on the page matches the published record")


if __name__ == "__main__":
    main()

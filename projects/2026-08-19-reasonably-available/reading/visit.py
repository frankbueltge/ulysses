#!/usr/bin/env python3
"""Open the page and press its buttons, the way a visitor would.

    python3 visit.py                          open it and look
    python3 visit.py "Ask an address"         open it, press that button once
    python3 visit.py "Ask an address" x8      press it eight times
    python3 visit.py "Ask all 306"            press that one

Each run starts the page fresh. Screenshots land in shots/ and the paths are printed;
open them to see what you did. Buttons are pressed by the words printed on them.
"""
import sys, re
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
PAGE = HERE / "site" / "index.html"
SHOTS = HERE / "shots"

label = sys.argv[1] if len(sys.argv) > 1 else None
times = 1
if len(sys.argv) > 2 and re.fullmatch(r"x?\d+", sys.argv[2]):
    times = int(sys.argv[2].lstrip("x"))

name = "opening" if not label else re.sub(r"\W+", "-", label.lower()).strip("-") + f"-{times}"

with sync_playwright() as pw:
    b = pw.chromium.launch(
        executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
        args=["--no-sandbox"])
    p = b.new_page(viewport={"width": 1100, "height": 900})
    p.goto(PAGE.as_uri())
    p.wait_for_selector("button")
    if label:
        for _ in range(times):
            p.get_by_role("button", name=label, exact=False).first.click()
        p.wait_for_timeout(400)
    first = SHOTS / f"{name}-1-first-screen.png"
    p.screenshot(path=str(first))
    print(first)
    h = p.evaluate("document.body.scrollHeight")
    for i, y in enumerate(range(900, min(h, 5400), 900), start=2):
        s = SHOTS / f"{name}-{i}-scrolled.png"
        p.evaluate(f"window.scrollTo(0,{y})")
        p.wait_for_timeout(200)
        p.screenshot(path=str(s))
        print(s)
    if h > 5400:
        print(f"(the page runs on for {h} pixels; the first {5400} are shown)")
    b.close()

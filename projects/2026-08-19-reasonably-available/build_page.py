#!/usr/bin/env python3
"""Inline route.json into the page template and write window/index.html.

The window is served self-contained: one file, no external loads, no runtime fetch. So
the join built by `build_route.py` is carried inside the page rather than beside it.

    python3 build_route.py && python3 build_page.py
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE / "page.template.html"
ROUTE = HERE / "window" / "route.json"
DEST = HERE / "window" / "index.html"


def main() -> None:
    route = ROUTE.read_text(encoding="utf-8")
    # A JSON payload inside <script> must not be able to close it. The three escapes
    # below are the whole surface: `</script>`, and the two comment openers a parser
    # would otherwise honour inside a script element.
    payload = route.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    json.loads(payload)  # the escapes must leave it valid JSON, or the page is broken

    html = TEMPLATE.read_text(encoding="utf-8")
    if "__ROUTE_JSON__" not in html:
        raise SystemExit("template has no __ROUTE_JSON__ placeholder")
    html = html.replace("__ROUTE_JSON__", payload)

    DEST.write_text(html, encoding="utf-8")
    print(f"index.html  {DEST.stat().st_size:,} bytes")
    print(f"  sha256 {hashlib.sha256(DEST.read_bytes()).hexdigest()}")


if __name__ == "__main__":
    main()

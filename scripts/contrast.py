"""Check the design tokens' colour pairs are readable in every look (light, dark, dusk).

    uv run python scripts/contrast.py

Reads src/drill/content/tokens.css and prints each pair's contrast ratio. Text needs 4.5:1
(WCAG AA); large text, icons and borders that must be seen need 3:1. Exits 1 if any pair fails,
so a colour change can't quietly make something unreadable. tests/test_content.py runs it too.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

TOKENS = Path(__file__).resolve().parents[1] / "src" / "drill" / "content" / "tokens.css"

# (text or mark, background, minimum, what it is)
PAIRS = [
    ("fg", "bg", 4.5, "reading text on the page"),
    ("fg", "surface", 4.5, "reading text on a card"),
    ("muted", "bg", 4.5, "secondary text on the page"),
    ("muted", "surface", 4.5, "secondary text on a card"),
    ("accent", "surface", 3.0, "the accent as a link, icon or focus ring"),
    ("accent-ink", "accent", 4.5, "text on the primary button"),
    ("pass", "pass-bg", 4.5, "a passing result"),
    ("fail", "fail-bg", 4.5, "a failing result"),
    ("hint", "hint-bg", 4.5, "a hint"),
    ("syn-kw", "code-bg", 4.5, "keywords in the editor"),
    ("syn-str", "code-bg", 4.5, "strings in the editor"),
    ("syn-com", "code-bg", 4.5, "comments in the editor"),
    ("mark", "bg", 3.0, "the trust mark on the page"),
    ("mark", "surface", 3.0, "the trust mark on a card"),
]


def looks(css: str) -> dict[str, dict[str, str]]:
    """Each look's tokens: light is the base; dark and dusk override it."""
    def block(selector: str) -> dict[str, str]:
        at = css.index(selector)
        body = css[css.index("{", at) + 1: css.index("}", at)]
        return dict(re.findall(r"--([a-z0-9-]+):\s*(#[0-9a-fA-F]{6})", body))

    light = block(":root {")
    return {"light": light, "dark": {**light, **block(':root[data-theme="dark"]')},
            "dusk": {**light, **block(':root[data-theme="dusk"]')}}


def luminance(hex_colour: str) -> float:
    channels = [int(hex_colour[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def ratio(a: str, b: str) -> float:
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def check() -> list[tuple[str, str, str, float, float, str]]:
    """Every pair in every look: (look, fg, bg, ratio, minimum, what)."""
    out = []
    for look, tokens in looks(TOKENS.read_text()).items():
        for fg, bg, minimum, what in PAIRS:
            if fg in tokens and bg in tokens:
                out.append((look, fg, bg, ratio(tokens[fg], tokens[bg]), minimum, what))
    return out


def main() -> int:
    rows = check()
    bad = [r for r in rows if r[3] < r[4]]
    for look, fg, bg, r, minimum, what in rows:
        print(f"{'✓' if r >= minimum else '✗'} {look:5} {fg:>10} on {bg:<9} {r:5.2f}:1 (needs {minimum}) {what}")
    print(f"\n{len(rows) - len(bad)} of {len(rows)} pass." + (" Fix the ✗ lines in tokens.css." if bad else ""))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

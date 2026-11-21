#!/usr/bin/env python3
"""Tombola card generator for Bingo Caller.

The cards live in the CARDS90 object in index.html. That is the single source
of truth: the app checks LINE / BINGO against it and the PDF is printed from it.

Usage:
    python3 tools/tombola.py pdf            # print all cards from index.html to a PDF
    python3 tools/tombola.py add 20         # add 20 new unique cards to index.html, then print the PDF

Options:
    --out FILE      PDF path (default: tombola-karty-1-N.pdf in the repo root)
    --rules N       number of rules sheets at the end of the PDF (default: 2)
"""
import argparse
import json
import random
import re
import sys
import urllib.request
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"
FONT_DIR = Path(__file__).resolve().parent / "fonts"
FONT_URL = "https://cdn.jsdelivr.net/npm/dejavu-fonts-ttf@2.37.3/ttf/{}.ttf"

CARDS_RE = re.compile(r"(const CARDS90 = \{\n)(.*?)(\n        \};)", re.S)

# Column ranges of a 1–90 card: 1–9, 10–19, …, 70–79, 80–90.
RANGES = [(1, 9)] + [(10 * c, 10 * c + 9) for c in range(1, 8)] + [(80, 90)]


# ---------- cards in index.html ----------
def read_cards():
    m = CARDS_RE.search(INDEX.read_text(encoding="utf-8"))
    if not m:
        sys.exit("CARDS90 not found in index.html")
    body = re.sub(r"(\d+):", r'"\1":', m.group(2))  # quote keys
    body = re.sub(r",(\s*[\]}])", r"\1", body)  # drop trailing commas
    body = body.rstrip().rstrip(",")
    return {int(k): v for k, v in json.loads("{" + body + "}").items()}


def write_new_cards(new):
    text = INDEX.read_text(encoding="utf-8")
    fmt = lambda row: "[" + ", ".join("null" if n is None else str(n) for n in row) + "]"
    add = "".join(
        f"          {cid}: [\n" + "".join(f"            {fmt(r)},\n" for r in g) + "          ],\n"
        for cid, g in new.items()
    )
    text = CARDS_RE.sub(lambda m: m.group(1) + m.group(2) + "\n" + add.rstrip("\n") + m.group(3), text, count=1)
    INDEX.write_text(text, encoding="utf-8")


def numbers(card):
    return frozenset(n for row in card for n in row if n is not None)


def validate(cards):
    seen = set()
    for cid, g in cards.items():
        assert len(g) == 3 and all(len(r) == 9 for r in g), f"card {cid}: not 3×9"
        assert all(sum(n is not None for n in r) == 5 for r in g), f"card {cid}: row without 5 numbers"
        for c in range(9):
            col = [r[c] for r in g if r[c] is not None]
            lo, hi = RANGES[c]
            assert col, f"card {cid}: empty column {c + 1}"
            assert all(lo <= n <= hi for n in col), f"card {cid}: number outside column {c + 1}"
            assert col == sorted(col), f"card {cid}: column {c + 1} not ascending"
        key = numbers(g)
        assert len(key) == 15, f"card {cid}: duplicate number"
        assert key not in seen, f"card {cid}: same numbers as another card"
        seen.add(key)


def make_card(rng):
    while True:
        mask = []
        for _ in range(3):
            cols = set(rng.sample(range(9), 5))
            mask.append([c in cols for c in range(9)])
        if all(any(mask[r][c] for r in range(3)) for c in range(9)):
            break
    grid = [[None] * 9 for _ in range(3)]
    for c in range(9):
        rows = [r for r in range(3) if mask[r][c]]
        lo, hi = RANGES[c]
        for r, n in zip(rows, sorted(rng.sample(range(lo, hi + 1), len(rows)))):
            grid[r][c] = n
    return grid


# ---------- PDF ----------
def load_fonts():
    FONT_DIR.mkdir(exist_ok=True)
    for name, alias in (("DejaVuSans", "DV"), ("DejaVuSans-Bold", "DVB")):
        path = FONT_DIR / f"{name}.ttf"
        if not path.exists():
            print(f"downloading {name}.ttf …")
            urllib.request.urlretrieve(FONT_URL.format(name), path)
        pdfmetrics.registerFont(TTFont(alias, str(path)))


BLACK, GREY, WHITE = (0, 0, 0), (0.88, 0.88, 0.88), (1, 1, 1)
X0, CW, CH = 34.01575, 58.58268, 53.85827  # left edge, cell width, cell height (pt)
TOP0, STEP = 793.874, 196.5354  # top of the first card, distance between cards

RULES = [  # font, size, gap below, text
    ("DV", 14, 30, "Moderátor vyvoláva čísla 1–90. Keď máš číslo na karte, prečiarkni ho."),
    ("DVB", 17, 24, "LINE  –  celý jeden vodorovný riadok"),
    ("DV", 14, 20, "   (všetkých 5 čísel v riadku)."),
    ("DV", 14, 20, "   Kto ho má prvý, zakričí „LINE!“."),
    ("DV", 14, 34, "   Po overení karty vyhráva a hra pokračuje."),
    ("DVB", 17, 24, "BINGO  –  celá karta (všetkých 15 čísel)."),
    ("DV", 14, 20, "   Kto ju má prvý, zakričí „BINGO!“ a vyhráva hlavnú cenu."),
    ("DV", 14, 34, "   Hra končí."),
    ("DV", 14, 22, "Ozvi sa hneď – kým moderátor vytiahne ďalšie číslo."),
    ("DV", 14, 30, "Pri falošnom „LINE/BINGO“ sa pokračuje."),
    ("DV", 14, 22, "Ak sa ozve viac ľudí naraz, o výhre rozhodne moderátor."),
    ("DV", 14, 22, "Číslo karty je nad kartou."),
]


def draw_card(c, cid, grid, top):
    c.setFillColorRGB(*BLACK)
    c.setFont("DVB", 11)
    c.drawString(X0, top + 5, f"TOMBOLA  ·  Karta č. {cid}")
    c.rect(X0, top + 1, 9 * CW, 3, stroke=0, fill=1)
    c.setStrokeColorRGB(*BLACK)
    c.setLineWidth(1.2)
    for r, row in enumerate(grid):
        y = top - (r + 1) * CH
        for ci, n in enumerate(row):
            x = X0 + ci * CW
            c.setFillColorRGB(*(WHITE if n else GREY))
            c.rect(x, y, CW, CH, stroke=1, fill=1)
            if n:
                c.setFillColorRGB(*BLACK)
                c.setFont("DVB", 24)
                c.drawCentredString(x + CW / 2, y + CH / 2 - 8, str(n))


def draw_rules(c):
    top, bottom = TOP0, 360
    c.setStrokeColorRGB(*BLACK)
    c.setFillColorRGB(*BLACK)
    c.setLineWidth(1.2)
    c.roundRect(X0, bottom, 9 * CW, top - bottom, 8, stroke=1, fill=0)
    c.rect(X0, top - 6, 9 * CW, 6, stroke=0, fill=1)
    x, y = X0 + 28, top - 56
    c.setFont("DVB", 30)
    c.drawString(x, y, "TOMBOLA – PRAVIDLÁ")
    y -= 44
    for font, size, gap, text in RULES:
        c.setFont(font, size)
        c.drawString(x, y, text)
        y -= gap


def make_pdf(cards, out, rules):
    load_fonts()
    ids = sorted(cards)
    c = canvas.Canvas(str(out), pagesize=A4)
    c.setTitle(f"Tombola karty {ids[0]}-{ids[-1]}")
    for p in range(0, len(ids), 4):
        for k, cid in enumerate(ids[p : p + 4]):
            draw_card(c, cid, cards[cid], TOP0 - k * STEP)
        c.showPage()
    for _ in range(rules):
        draw_rules(c)
        c.showPage()
    c.save()
    pages = -(-len(ids) // 4) + rules
    print(f"{out.name}: {len(ids)} cards, {pages} pages")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["pdf", "add"])
    ap.add_argument("count", nargs="?", type=int, default=0, help="how many cards to add")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--rules", type=int, default=2)
    a = ap.parse_args()

    cards = read_cards()
    validate(cards)
    if a.command == "add":
        if a.count < 1:
            sys.exit("say how many cards to add, e.g.: tombola.py add 20")
        rng = random.Random()
        seen = {numbers(g) for g in cards.values()}
        new, cid = {}, max(cards) + 1
        while len(new) < a.count:
            g = make_card(rng)
            if numbers(g) not in seen:
                seen.add(numbers(g))
                new[cid] = g
                cid += 1
        write_new_cards(new)
        cards = read_cards()
        validate(cards)
        print(f"added cards {min(new)}–{max(new)} to index.html")
    make_pdf(cards, a.out or ROOT / f"tombola-karty-1-{max(cards)}.pdf", a.rules)


if __name__ == "__main__":
    main()

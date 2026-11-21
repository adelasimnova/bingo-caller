# Bingo Caller 🎱

A bingo number caller that runs in the browser. It is one HTML file with no build step and no dependencies to install.

> **Note:** This project is entirely AI-generated and was made just for fun.

## Features

- **Two game modes:** 1–75 (5×5 cards with columns B I N G O) or 1–90 (tombola, 3 rows × 9)
- **Voice calling** reads numbers aloud with the browser's speech synthesis, including classic bingo calls in the 1–90 mode (for example "Two fat ladies, eighty-eight!")
- **Background music:** five original lounge tracks generated live in the browser. Each new game plays the next track, the music gets quieter while the voice speaks, and **🎵 Music** turns it on or off
- **Auto draw** at fast, normal or slow speed, or draw numbers one at a time with **Next number**
- **Board of called numbers** with colour-coded columns, plus a list of the latest numbers
- **Card check:** use **LINE / BINGO** to verify a player's numbers when someone calls LINE or BINGO
- **TV layout:** on a wide landscape screen (a TV, or a laptop in fullscreen) the game fills the whole screen with large numbers you can read from across the room. It is laid out for 1920×1080 and scales up to 4K, and the mouse pointer hides after 3 seconds
- **Repeat** the last number, switch to **Fullscreen**, or start a **New game**
- **Resume:** the game state is saved in `localStorage`, so you can pick up an unfinished game after reloading the page

## Usage

Open `index.html` in a browser, or host it on any static hosting service such as GitHub Pages, Netlify or Cloudflare Pages.

```bash
open index.html
```

Voice calling works best in Chrome, Edge or Safari. The page uses English voices if the system has them installed.

## Printable cards

[`tombola-karty-1-80.pdf`](tombola-karty-1-80.pdf) has the 80 tombola cards (1–90 mode) that the app knows, 4 per A4 page in black and white, plus two rules sheets (in Slovak) to hand out. Use **LINE / BINGO** in the app with the number printed above each card.

### Generating cards

The cards are stored in the `CARDS90` object in `index.html`, and the PDF is printed from that same data, so the app and the printed cards always match.

```bash
python3 -m venv .venv
.venv/bin/pip install -r tools/requirements.txt

.venv/bin/python tools/tombola.py pdf       # rebuild the PDF from index.html
.venv/bin/python tools/tombola.py add 20    # add 20 new unique cards, then rebuild the PDF
```

Options: `--out FILE` sets the PDF path and `--rules N` sets how many rules sheets go at the end (default 2). On the first run the script downloads the DejaVu Sans font into `tools/fonts/`.

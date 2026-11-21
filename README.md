# Bingo Caller 🎱

A bingo number caller that runs in the browser. It is one HTML file with no build step and no dependencies to install.

> **Note:** This project is entirely AI-generated and was made just for fun.

## Features

- **Two game modes:** 1–75 (5×5 cards with columns B I N G O) or 1–90 (tombola, 3 rows × 9)
- **Voice calling** reads numbers aloud with the browser's speech synthesis, including classic bingo calls in the 1–90 mode (for example "Two fat ladies, eighty-eight!")
- **Auto draw** at fast, normal or slow speed, or draw numbers one at a time with **Next number**
- **Board of called numbers** with colour-coded columns, plus a list of the latest numbers
- **Card check:** use **Check card** to verify a player's numbers when someone calls LINE or BINGO
- **Repeat** the last number, switch to **Fullscreen**, or start a **New game**
- **Resume:** the game state is saved in `localStorage`, so you can pick up an unfinished game after reloading the page

## Usage

Open `index.html` in a browser, or host it on any static hosting service such as GitHub Pages, Netlify or Cloudflare Pages.

```bash
open index.html
```

Voice calling works best in Chrome, Edge or Safari. The page uses English voices if the system has them installed.

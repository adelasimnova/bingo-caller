#!/usr/bin/env python3
"""Record the caller's voice lines as MP3 files in audio/ (macOS only).

Browsers on smart TVs usually have no built-in speech voice, so the game plays
these recordings instead of using the browser's speech synthesis.

The lines are read from index.html (numbers 1–90, SPECIAL calls, the animal
calls of the 1–75 mode and the RECORDED list), so re-run this script after
changing any of them:

    python3 tools/make_voice.py

Needs the macOS `say` command with the "Daniel" (en-GB) voice and ffmpeg.
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "audio"
VOICE, RATE = "Daniel", "170"


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def block(src, start, end):
    i = src.index(start)
    return src[i : src.index(end, i)]


def phrases():
    src = (ROOT / "index.html").read_text(encoding="utf-8")
    lines = [str(n) for n in range(1, 91)]
    lines += re.findall(r'"(.+?)"', block(src, "const SPECIAL = {", "};"))
    lines += re.findall(r'"(.+?)"', block(src, "const RECORDED = [", "];"))
    letter = None
    for row in block(src, "const ANIMALS = {", "\n        };").splitlines():
        m = re.match(r"\s*([BINGO]): \[$", row)
        if m:
            letter = m.group(1)
        m = re.match(r'\s*\["(.+?)",', row)
        if m and letter:
            lines.append(f"{letter} for {m.group(1)}")
    return list(dict.fromkeys(lines))


def main():
    OUT.mkdir(exist_ok=True)
    keys = []
    with tempfile.TemporaryDirectory() as tmp:
        for text in phrases():
            key = slug(text)
            aiff = Path(tmp) / f"{key}.aiff"
            subprocess.run(["say", "-v", VOICE, "-r", RATE, "-o", str(aiff), text], check=True)
            subprocess.run(
                ["ffmpeg", "-loglevel", "error", "-y", "-i", str(aiff),
                 "-ac", "1", "-ar", "22050", "-b:a", "48k", str(OUT / f"{key}.mp3")],
                check=True,
            )
            keys.append(key)
    (OUT / "manifest.json").write_text(json.dumps(keys, indent=0) + "\n")
    size = sum(f.stat().st_size for f in OUT.glob("*.mp3"))
    print(f"{len(keys)} clips, {size / 1024:.0f} KB in {OUT.relative_to(ROOT)}/")


if __name__ == "__main__":
    sys.exit(main())

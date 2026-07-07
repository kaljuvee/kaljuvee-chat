"""Compose the Talk to Julian demo screenshots into an animated GIF.

    python scripts/make_gif.py

Screenshots live in screenshots/; the GIF is written to screenshots/kaljuvee-chat-demo.gif.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "screenshots"
OUT = SHOTS / "kaljuvee-chat-demo.gif"

TARGET_W, TARGET_H = 1280, 820
BG = (255, 255, 255)

# (filename, hold duration in ms)
FRAMES = [
    ("01-welcome.png", 2200),
    ("09-voice-listening.png", 3200),
    ("02-skills-radar.png", 3200),
    ("03-cv-download.png", 3000),
    ("04-evolution-sankey.png", 3200),
    ("05-visuals-all.png", 3000),
    ("06-visuals-skills.png", 3000),
    ("07-visuals-career.png", 3000),
    ("08-visuals-stack.png", 3000),
]


def load_frame(path: Path) -> Image.Image:
    img = Image.open(path).convert("RGB")
    ratio = TARGET_W / img.width
    img = img.resize((TARGET_W, int(img.height * ratio)), Image.LANCZOS)
    if img.height >= TARGET_H:
        img = img.crop((0, 0, TARGET_W, TARGET_H))
    else:
        canvas = Image.new("RGB", (TARGET_W, TARGET_H), BG)
        canvas.paste(img, (0, 0))
        img = canvas
    return img


def main() -> None:
    frames, durations = [], []
    for fname, dur in FRAMES:
        p = SHOTS / fname
        if not p.exists():
            print(f"  skip (missing): {fname}")
            continue
        frames.append(load_frame(p))
        durations.append(dur)
        print(f"  + {fname} ({dur} ms)")
    if not frames:
        print("no frames found")
        return
    frames[0].save(OUT, save_all=True, append_images=frames[1:], optimize=True,
                   duration=durations, loop=0, disposal=2)
    print(f"\nWrote {OUT}  ({OUT.stat().st_size/1024:.0f} KB, {len(frames)} frames)")


if __name__ == "__main__":
    main()

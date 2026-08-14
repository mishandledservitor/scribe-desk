#!/usr/bin/env python3
"""Generate Scribe Desk.app's icon.

Geometry follows Apple's icon grid (see the macos-app-icon skill): a 1024 canvas
with an 824 artwork square, a superellipse — not a rounded rect — a vertical
navy gradient with a faint top sheen, and a drop shadow living in the ~100pt
margin. The glyph is taken from `icon-mark.png`, whose cream and teal pixels are
recoloured onto the field, so the mark stays editable as flat artwork.

The committed icon.icns is the source of truth; rerunning this only reproduces
it. Needs Pillow:

    /opt/homebrew/bin/python3 make_icon.py
"""

from __future__ import annotations

import math
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

PROJECT_ROOT = Path(__file__).resolve().parent
BUNDLE_RESOURCES = PROJECT_ROOT / "Scribe Desk.app" / "Contents" / "Resources"
MARK = PROJECT_ROOT / "icon-mark.png"

CANVAS = 1024
ART = 824  # Apple's artwork square inside the 1024 canvas
SS = 4  # supersample factor; polygon edges alias badly at 1x

BG_TOP = (58, 65, 118)
BG_BOTTOM = (38, 42, 74)
CREAM = (235, 238, 250)
TEAL = (94, 214, 197)
MARK_SCALE = 0.62  # mark's longest side as a fraction of the artwork square
SHEEN = 20  # subtle = depth; strong = haze


def superellipse_mask(size: int, n: float = 5.0) -> Image.Image:
    """Apple-style squircle: |x|^n + |y|^n = 1. A rounded rect is NOT this."""
    mask = Image.new("L", (size, size), 0)
    a = size / 2
    pts = []
    for i in range(2048):
        t = 2 * math.pi * i / 2048
        ct, st = math.cos(t), math.sin(t)
        x = a * (abs(ct) ** (2 / n)) * (1 if ct >= 0 else -1)
        y = a * (abs(st) ** (2 / n)) * (1 if st >= 0 else -1)
        pts.append((a + x, a + y))
    ImageDraw.Draw(mask).polygon(pts, fill=255)
    return mask


def vertical_gradient(size: int, top: tuple, bottom: tuple) -> Image.Image:
    grad = Image.new("RGB", (1, size))
    for y in range(size):
        f = y / (size - 1)
        grad.putpixel((0, y), tuple(round(top[i] + (bottom[i] - top[i]) * f) for i in range(3)))
    return grad.resize((size, size), Image.BILINEAR)


def mark_masks() -> tuple[Image.Image, Image.Image]:
    """Cream and teal alpha masks from icon-mark.png, on a shared canvas so the
    two layers stay in register once scaled."""
    im = Image.open(MARK).convert("RGBA")
    px = im.load()
    w, h = im.size
    cream, teal = Image.new("L", (w, h), 0), Image.new("L", (w, h), 0)
    cp, tp = cream.load(), teal.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:  # alpha FIRST: PNGs keep colour under transparent pixels
                continue
            is_teal = all(abs(v - t) < 60 for v, t in zip((r, g, b), TEAL))
            (tp if is_teal else cp)[x, y] = a
    return cream, teal


def render() -> Image.Image:
    art, big = ART * SS, CANVAS * SS

    shape = superellipse_mask(art)
    body = vertical_gradient(art, BG_TOP, BG_BOTTOM).convert("RGBA")
    body.putalpha(shape)

    sheen = Image.new("L", (art, art), 0)
    ImageDraw.Draw(sheen).ellipse((-art * 0.35, -art * 0.90, art * 1.35, art * 0.30), fill=SHEEN)
    sheen = sheen.filter(ImageFilter.GaussianBlur(art * 0.05))
    sheen = Image.composite(sheen, Image.new("L", (art, art), 0), shape)
    white = Image.new("L", (art, art), 255)
    body.alpha_composite(Image.merge("RGBA", (white, white, white, sheen)))

    cream, teal = mark_masks()
    # Fit the LONGEST side: scaling by height alone runs a wide mark off the edges.
    scale = (art * MARK_SCALE) / max(cream.size)
    size = tuple(max(1, round(v * scale)) for v in cream.size)
    pos = ((art - size[0]) // 2, (art - size[1]) // 2)
    layer = Image.new("RGBA", (art, art), (0, 0, 0, 0))
    for mask, colour in ((cream, CREAM), (teal, TEAL)):
        tint = Image.new("RGBA", size, colour + (0,))
        tint.putalpha(mask.resize(size, Image.LANCZOS))
        layer.alpha_composite(tint, pos)
    body.alpha_composite(layer)

    # Shadow lives in the 100pt margin — that margin is why it exists.
    canvas = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    shadow = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    sh = Image.new("RGBA", (art, art), (0, 0, 0, 0))
    sh.putalpha(shape.point(lambda v: int(v * 0.28)))
    off = (big - art) // 2
    shadow.alpha_composite(sh, (off, off + int(art * 0.022)))
    shadow = shadow.filter(ImageFilter.GaussianBlur(art * 0.022))
    canvas.alpha_composite(shadow)
    canvas.alpha_composite(body, (off, off))
    return canvas.resize((CANVAS, CANVAS), Image.LANCZOS)


def build() -> Path:
    icon = render()
    with tempfile.TemporaryDirectory() as workspace:
        iconset = Path(workspace) / "icon.iconset"
        iconset.mkdir()
        # Exact filenames — iconutil rejects anything else.
        for s in (16, 32, 128, 256, 512):
            icon.resize((s, s), Image.LANCZOS).save(iconset / f"icon_{s}x{s}.png")
            icon.resize((s * 2, s * 2), Image.LANCZOS).save(iconset / f"icon_{s}x{s}@2x.png")
        BUNDLE_RESOURCES.mkdir(parents=True, exist_ok=True)
        destination = BUNDLE_RESOURCES / "icon.icns"
        subprocess.run(
            ["iconutil", "-c", "icns", str(iconset), "-o", str(destination)],
            check=True, capture_output=True, text=True,
        )
        icon.resize((512, 512), Image.LANCZOS).save(PROJECT_ROOT / "icon-preview.png")
    app = BUNDLE_RESOURCES.parent.parent
    subprocess.run(["codesign", "--force", "--sign", "-", str(app)], check=True)  # copy invalidates it
    subprocess.run(["touch", str(app)], check=True)  # nudge Finder's icon cache
    return destination


if __name__ == "__main__":
    if shutil.which("iconutil") is None:
        raise SystemExit("iconutil not found — this script needs macOS")
    print(f"Icon: {build()}")

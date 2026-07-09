#!/usr/bin/env python3
"""Draw ICT annotations on a screenshot.

Usage: annotate.py INPUT.png SPEC.json OUTPUT.png

SPEC.json:
{
  "marks": [
    {"type": "box",  "color": "fvg",     "xy": [x1, y1, x2, y2], "label": "FVG"},
    {"type": "zone", "color": "killzone","xy": [x1, y1, x2, y2], "label": "NY AM KZ"},
    {"type": "line", "color": "mss",     "xy": [x1, y1, x2, y2], "label": "MSS"},
    {"type": "dashed-line", "color": "sl", "xy": [x1, y1, x2, y2], "label": "SL"},
    {"type": "arrow", "color": "sweep",  "xy": [x1, y1, x2, y2], "label": "SSL sweep"},
    {"type": "label", "color": "entry",  "xy": [x, y], "label": "Entry 2318.50"}
  ]
}

Colors follow references/annotation-legend.md:
  fvg=blue box, ob-bear=red box, ob-bull=green box, sweep=yellow arrow,
  mss=orange line, killzone=purple zone, entry=white line,
  sl=red dashed line, tp=green dashed line, premium/discount=grey zone.
Any Pillow color string (e.g. "#ff00ff") is also accepted.

Requires: pip install Pillow
"""

import json
import math
import sys

from PIL import Image, ImageDraw, ImageFont

COLORS = {
    "fvg": (40, 110, 255),
    "ob-bear": (225, 45, 45),
    "ob-bull": (40, 175, 80),
    "sweep": (250, 210, 40),
    "mss": (255, 140, 0),
    "killzone": (160, 80, 220),
    "entry": (255, 255, 255),
    "sl": (225, 45, 45),
    "tp": (40, 175, 80),
    "premium": (150, 150, 150),
    "discount": (150, 150, 150),
}


def resolve_color(name):
    return COLORS.get(name, name)


def load_font(size):
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_dashed(draw, xy, color, width, dash=14, gap=8):
    x1, y1, x2, y2 = xy
    length = math.hypot(x2 - x1, y2 - y1)
    if length == 0:
        return
    ux, uy = (x2 - x1) / length, (y2 - y1) / length
    pos = 0.0
    while pos < length:
        end = min(pos + dash, length)
        draw.line(
            [x1 + ux * pos, y1 + uy * pos, x1 + ux * end, y1 + uy * end],
            fill=color, width=width,
        )
        pos = end + gap


def draw_arrow(draw, xy, color, width):
    x1, y1, x2, y2 = xy
    draw.line(xy, fill=color, width=width)
    angle = math.atan2(y2 - y1, x2 - x1)
    head = max(12, width * 4)
    for offset in (math.radians(150), math.radians(-150)):
        draw.line(
            [x2, y2,
             x2 + head * math.cos(angle + offset),
             y2 + head * math.sin(angle + offset)],
            fill=color, width=width,
        )


def draw_label(draw, x, y, text, color, font):
    left, top, right, bottom = draw.textbbox((x, y), text, font=font)
    pad = 4
    draw.rectangle([left - pad, top - pad, right + pad, bottom + pad],
                   fill=(0, 0, 0, 190))
    draw.text((x, y), text, fill=color, font=font)


def main():
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    input_path, spec_path, output_path = sys.argv[1:4]

    with open(spec_path, encoding="utf-8") as fh:
        spec = json.load(fh)

    image = Image.open(input_path).convert("RGBA")
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    width = max(3, image.width // 500)
    font_size = max(16, image.width // 70)
    font = load_font(font_size)

    for mark in spec.get("marks", []):
        kind = mark["type"]
        color = resolve_color(mark.get("color", "entry"))
        xy = mark["xy"]
        label = mark.get("label")

        if kind == "box":
            draw.rectangle(xy, outline=color, width=width)
        elif kind == "zone":
            fill = tuple(color) + (55,) if isinstance(color, tuple) else color
            draw.rectangle(xy, fill=fill, outline=color, width=width)
        elif kind == "line":
            draw.line(xy, fill=color, width=width)
        elif kind == "dashed-line":
            draw_dashed(draw, xy, color, width)
        elif kind == "arrow":
            draw_arrow(draw, xy, color, width)
        elif kind == "label":
            pass  # label-only mark, drawn below
        else:
            raise SystemExit(f"unknown mark type: {kind}")

        if label:
            lx, ly = xy[0], max(0, xy[1] - font_size - 10)
            draw_label(draw, lx, ly, label, color, font)

    Image.alpha_composite(image, overlay).convert("RGB").save(output_path)
    print(output_path)


if __name__ == "__main__":
    main()

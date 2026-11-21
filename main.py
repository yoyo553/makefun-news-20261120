#!/usr/bin/env python3
"""make.fun entry: sum up 20 November 2026 world news in one image.

Python 3.13, standard library only, no network, fully deterministic.
Draws a newspaper front page (1024x1024) with a built-in bitmap font
and writes it to the output directory as entry.png:
MAKEFUN_OUTPUT_DIR if set, else /output if usable, else ./out.
Running it twice writes exactly the same bytes.
"""

import math
import os
import struct
import zlib

WIDTH = 1024
HEIGHT = 1024

PAPER = (252, 252, 250)
INK = (16, 22, 44)
ACCENT = (198, 32, 44)
GRAY = (96, 104, 128)

# ---------------------------------------------------------------------------
# 5x7 bitmap font: uppercase letters, digits and basic punctuation.
# ---------------------------------------------------------------------------

FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", ".#.#.", "..#..", "..#..", "..#..", ".#.#.", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("#####", "...#.", "..#..", "...#.", "....#", "#...#", ".###."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    "%": ("##..#", "##.#.", "....#", "...#.", "..#..", ".#.##", "#..##"),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
}

# ---------------------------------------------------------------------------
# Canvas helpers. The canvas is a list of bytearray rows, 3 bytes per pixel.
# ---------------------------------------------------------------------------


def make_canvas(width, height, color):
    row = bytearray(bytes(color) * width)
    return [bytearray(row) for _ in range(height)]


def fill_rect(canvas, x0, y0, x1, y1, color):
    height = len(canvas)
    width = len(canvas[0]) // 3
    x0 = max(0, x0)
    y0 = max(0, y0)
    x1 = min(width, x1)
    y1 = min(height, y1)
    if x1 <= x0 or y1 <= y0:
        return
    segment = bytes(color) * (x1 - x0)
    for y in range(y0, y1):
        canvas[y][x0 * 3 : x1 * 3] = segment


def plot(canvas, cx, cy, size, color):
    half = size // 2
    fill_rect(canvas, cx - half, cy - half, cx - half + size, cy - half + size, color)


def draw_line(canvas, x0, y0, x1, y1, size, color):
    steps = int(max(abs(x1 - x0), abs(y1 - y0))) or 1
    for i in range(steps + 1):
        x = x0 + (x1 - x0) * i / steps
        y = y0 + (y1 - y0) * i / steps
        plot(canvas, int(round(x)), int(round(y)), size, color)


def draw_polyline(canvas, points, size, color):
    for (ax, ay), (bx, by) in zip(points, points[1:]):
        draw_line(canvas, ax, ay, bx, by, size, color)


def draw_circle(canvas, cx, cy, radius, size, color):
    for deg in range(0, 360, 2):
        rad = math.radians(deg)
        x = cx + radius * math.cos(rad)
        y = cy + radius * math.sin(rad)
        plot(canvas, int(round(x)), int(round(y)), size, color)


def draw_text(canvas, x, y, text, scale, color):
    advance = 6 * scale
    for ch in text.upper():
        glyph = FONT.get(ch, FONT[" "])
        for row_i, row in enumerate(glyph):
            for col_i, cell in enumerate(row):
                if cell == "#":
                    fill_rect(
                        canvas,
                        x + col_i * scale,
                        y + row_i * scale,
                        x + (col_i + 1) * scale,
                        y + (row_i + 1) * scale,
                        color,
                    )
        x += advance
    return x


def text_width(text, scale):
    return len(text) * 6 * scale - scale


def draw_text_centered(canvas, y, text, scale, color):
    x = (WIDTH - text_width(text, scale)) // 2
    draw_text(canvas, x, y, text, scale, color)


def wrap_text(text, max_chars):
    lines = []
    current = ""
    for word in text.split():
        trial = word if not current else current + " " + word
        if len(trial) <= max_chars:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


# ---------------------------------------------------------------------------
# Panel icons, drawn inside an 88x88 box at (x, y).
# ---------------------------------------------------------------------------


def icon_bridge(canvas, x, y):
    draw_line(canvas, x + 4, y + 40, x + 84, y + 40, 5, INK)
    draw_line(canvas, x + 24, y + 10, x + 24, y + 58, 5, INK)
    draw_line(canvas, x + 64, y + 10, x + 64, y + 58, 5, INK)
    arc = []
    for i in range(41):
        t = i / 40
        px = x + 4 + 80 * t
        py = y + 12 + 26 * (4 * t * (1 - t)) * 0.9
        arc.append((px, py))
    draw_polyline(canvas, arc, 4, ACCENT)
    for hx in (36, 44, 52):
        top = y + 12 + 26 * (4 * ((hx - 4) / 80) * (1 - (hx - 4) / 80)) * 0.9
        draw_line(canvas, x + hx, int(top), x + hx, y + 40, 3, ACCENT)
    for wy in (64, 74, 84):
        wave = []
        for i in range(21):
            px = x + 4 + 4 * i
            py = y + wy + 3 * math.sin(i * 1.1 + wy)
            wave.append((px, py))
        draw_polyline(canvas, wave, 3, GRAY)


def icon_cyclone(canvas, x, y):
    cx, cy = x + 42, y + 40
    points = []
    theta = 0.0
    while theta < 10.6:
        r = 3 + 3.6 * theta
        points.append((cx + r * math.cos(theta), cy + r * math.sin(theta)))
        theta += 0.15
    draw_polyline(canvas, points, 5, INK)
    plot(canvas, cx, cy, 9, ACCENT)
    draw_line(canvas, x + 4, y + 84, x + 84, y + 84, 4, GRAY)


def icon_chart(canvas, x, y):
    draw_line(canvas, x + 10, y + 8, x + 10, y + 78, 4, GRAY)
    draw_line(canvas, x + 10, y + 78, x + 84, y + 78, 4, GRAY)
    points = [(x + 16, y + 24), (x + 34, y + 38), (x + 50, y + 32), (x + 66, y + 56), (x + 80, y + 66)]
    draw_polyline(canvas, points, 6, ACCENT)
    draw_line(canvas, x + 80, y + 66, x + 66, y + 64, 6, ACCENT)
    draw_line(canvas, x + 80, y + 66, x + 78, y + 52, 6, ACCENT)


def icon_flags(canvas, x, y):
    draw_line(canvas, x + 20, y + 12, x + 20, y + 78, 4, INK)
    draw_line(canvas, x + 64, y + 12, x + 64, y + 78, 4, INK)
    fill_rect(canvas, x + 20, y + 12, x + 46, y + 32, INK)
    fill_rect(canvas, x + 64, y + 12, x + 88, y + 32, ACCENT)
    draw_line(canvas, x + 12, y + 56, x + 76, y + 56, 4, GRAY)
    draw_line(canvas, x + 12, y + 56, x + 24, y + 48, 4, GRAY)
    draw_line(canvas, x + 12, y + 56, x + 24, y + 64, 4, GRAY)
    draw_line(canvas, x + 76, y + 56, x + 64, y + 48, 4, GRAY)
    draw_line(canvas, x + 76, y + 56, x + 64, y + 64, 4, GRAY)


def icon_shield(canvas, x, y):
    cx = x + 44
    outline = [
        (cx, y + 4),
        (cx + 30, y + 14),
        (cx + 30, y + 44),
        (cx, y + 84),
        (cx - 30, y + 44),
        (cx - 30, y + 14),
        (cx, y + 4),
    ]
    draw_polyline(canvas, outline, 5, INK)
    draw_polyline(canvas, [(cx - 14, y + 42), (cx - 4, y + 54), (cx + 16, y + 26)], 6, ACCENT)


def icon_card(canvas, x, y):
    draw_line(canvas, x + 8, y + 20, x + 80, y + 20, 4, INK)
    draw_line(canvas, x + 8, y + 68, x + 80, y + 68, 4, INK)
    draw_line(canvas, x + 8, y + 20, x + 8, y + 68, 4, INK)
    draw_line(canvas, x + 80, y + 20, x + 80, y + 68, 4, INK)
    fill_rect(canvas, x + 8, y + 28, x + 80, y + 38, ACCENT)
    draw_line(canvas, x + 16, y + 48, x + 30, y + 48, 3, GRAY)
    draw_line(canvas, x + 16, y + 58, x + 30, y + 58, 3, GRAY)
    draw_circle(canvas, x + 58, y + 50, 7, 4, INK)
    draw_line(canvas, x + 63, y + 55, x + 72, y + 64, 4, INK)


ICONS = {
    "bridge": icon_bridge,
    "cyclone": icon_cyclone,
    "chart": icon_chart,
    "flags": icon_flags,
    "shield": icon_shield,
    "card": icon_card,
}

# ---------------------------------------------------------------------------
# Page content: the verified news of Friday 20 November 2026.
# ---------------------------------------------------------------------------

DATE_LINE = "FRIDAY 20 NOVEMBER 2026"
SUBTITLE = "THE WORLD IN ONE PAGE"

PANELS = [
    {
        "place": "KYIV, UKRAINE",
        "headline": ["3 DNIPRO", "BRIDGES HIT"],
        "body": "RUSSIA'S OVERNIGHT STRIKE DAMAGES KYIV'S RIVER CROSSINGS",
        "icon": "bridge",
    },
    {
        "place": "ODISHA, INDIA",
        "headline": ["CYCLONE AKVAN", "LANDFALL"],
        "body": "300,000 PEOPLE EVACUATED AS THE STORM CROSSES THE EAST COAST",
        "icon": "cyclone",
    },
    {
        "place": "ASIA MARKETS",
        "headline": ["AI STOCKS", "SELL OFF"],
        "body": "NIKKEI FALLS ABOUT 5%. TAIWAN AND CHIP SHARES SLIDE FURTHER",
        "icon": "chart",
    },
    {
        "place": "UK AND EU",
        "headline": ["YOUTH MOBILITY", "DEAL"],
        "body": "UP TO 100,000 YOUNG PEOPLE A YEAR COULD LIVE AND WORK ABROAD",
        "icon": "flags",
    },
    {
        "place": "HAITI",
        "headline": ["POLICE RAID", "GANGS"],
        "body": "34 GANG SUSPECTS KILLED IN MARTISSANT RAID, POLICE SAY",
        "icon": "shield",
    },
    {
        "place": "UNITED STATES",
        "headline": ["CARD DATA", "LEAKED"],
        "body": "VISA, MASTERCARD AND JPMORGAN DATA LEAKED AFTER RANSOMWARE",
        "icon": "card",
    },
]


def draw_panel(canvas, px, py, panel):
    w, h = 480, 250
    fill_rect(canvas, px, py, px + w, py + 3, INK)
    fill_rect(canvas, px, py + h - 3, px + w, py + h, INK)
    fill_rect(canvas, px, py, px + 3, py + h, INK)
    fill_rect(canvas, px + w - 3, py, px + w, py + h, INK)
    draw_text(canvas, px + 16, py + 12, panel["place"], 4, ACCENT)
    hy = py + 48
    for line in panel["headline"]:
        draw_text(canvas, px + 16, hy, line, 5, INK)
        hy += 43
    fill_rect(canvas, px + 16, py + 134, px + w - 16, py + 136, GRAY)
    ICONS[panel["icon"]](canvas, px + 16, py + 146)
    lines = wrap_text(panel["body"], 19)
    ly = py + 142
    for line in lines[:4]:
        draw_text(canvas, px + 124, ly, line, 3, INK)
        ly += 25


def draw_page():
    canvas = make_canvas(WIDTH, HEIGHT, PAPER)
    fill_rect(canvas, 0, 0, WIDTH, 148, INK)
    draw_text_centered(canvas, 49, DATE_LINE, 7, PAPER)
    fill_rect(canvas, 0, 148, WIDTH, 160, ACCENT)
    draw_text_centered(canvas, 172, SUBTITLE, 4, INK)
    fill_rect(canvas, 24, 212, WIDTH - 24, 214, INK)
    top = 224
    for i, panel in enumerate(PANELS):
        px = 24 if i % 2 == 0 else 520
        py = top + (i // 2) * 260
        draw_panel(canvas, px, py, panel)
    return canvas


def encode_png(canvas):
    height = len(canvas)
    width = len(canvas[0]) // 3
    raw = bytearray()
    for row in canvas:
        raw.append(0)
        raw += row

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    png = bytearray(b"\x89PNG\r\n\x1a\n")
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    return bytes(png)


def main():
    data = encode_png(draw_page())
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if not out_dir:
        out_dir = "/output" if os.path.isdir("/output") and os.access("/output", os.W_OK) else "out"
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as fh:
        fh.write(data)
    print(f"wrote {path} ({len(data)} bytes)")


if __name__ == "__main__":
    main()

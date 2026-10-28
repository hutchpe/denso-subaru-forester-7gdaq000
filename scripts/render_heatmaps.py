#!/usr/bin/env python3
"""Render the fuel and ignition maps as annotated heatmaps (PNG).

RPM across the top (uniform estimate), load down the side with low load at the
bottom. Requires Pillow + numpy.

Usage:
    python render_heatmaps.py path/to/rom.bin [out_dir]
"""
import sys, os
import numpy as np
from PIL import Image, ImageDraw

FUEL = dict(addr=0x23EC, load=7,  rpm=19, preamble=10)
IGN  = dict(addr=0x210E, load=11, rpm=19, preamble=10)
RPM_FULLSCALE = 6144


def w(d, o):
    return (d[o] << 8) | d[o + 1]


def grid(d, m):
    gs = m["addr"] + 2 * m["preamble"]
    return [[w(d, gs + 2 * (r * m["load"] + c)) for r in range(m["rpm"])]
            for c in range(m["load"])]


def cmap(t):
    t = max(0.0, min(1.0, t))
    stops = [(0, (30, 50, 160)), (0.33, (0, 170, 180)),
             (0.66, (240, 200, 40)), (1, (210, 40, 40))]
    for i in range(len(stops) - 1):
        a, ca = stops[i]; b, cb = stops[i + 1]
        if t <= b:
            f = (t - a) / (b - a + 1e-9)
            return tuple(int(ca[k] + (cb[k] - ca[k]) * f) for k in range(3))
    return stops[-1][1]


def render(g_lowfirst, title, valfmt, path, cell=32):
    n_load = len(g_lowfirst); n_rpm = len(g_lowfirst[0])
    rpm = [round(i * RPM_FULLSCALE / (n_rpm - 1) / 10) * 10 for i in range(n_rpm)]
    disp = list(reversed(g_lowfirst))          # low load at bottom
    labels = list(reversed(range(n_load)))
    a = np.array(g_lowfirst, float); mn, mx = a.min(), a.max()
    mL, mT, mB, mR = 64, 70, 24, 16
    im = Image.new("RGB", (mL + n_rpm * cell + mR, mT + n_load * cell + mB),
                   (24, 24, 28))
    dr = ImageDraw.Draw(im)
    dr.text((14, 12), title, fill=(240, 240, 245))
    dr.text((14, 32), "RPM = est. uniform ~0-6150 | load low at bottom",
            fill=(150, 152, 160))
    for c in range(n_rpm):
        dr.text((mL + c * cell + 1, mT - 14), f"{rpm[c]}", fill=(170, 172, 180))
    for r in range(n_load):
        dr.text((6, mT + r * cell + cell // 2 - 5), f"L{labels[r]}",
                fill=(170, 172, 180))
        for c in range(n_rpm):
            v = disp[r][c]; t = (v - mn) / (mx - mn + 1e-9)
            x = mL + c * cell; y = mT + r * cell
            dr.rectangle([x, y, x + cell - 1, y + cell - 1], fill=cmap(t))
            dr.text((x + 1, y + cell // 2 - 5), valfmt(v),
                    fill=((0, 0, 0) if t > 0.45 else (235, 235, 240)))
    im.save(path); print("wrote", path)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    d = open(sys.argv[1], "rb").read()
    out = sys.argv[2] if len(sys.argv) > 2 else "."
    os.makedirs(out, exist_ok=True)
    render(grid(d, FUEL), "FUEL / injection @ 0x23EC (raw counts)",
           lambda v: f"{v}", os.path.join(out, "fuel_table.png"))
    ign = [[v / 128.0 for v in row] for row in grid(d, IGN)]
    render(ign, "IGNITION advance @ 0x210E (deg BTDC = raw/128)",
           lambda v: f"{v:.0f}", os.path.join(out, "ignition_degrees.png"))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Extract the fuel and ignition maps to CSV, ignition converted to degrees.

Both maps are stored big-endian, load-major (load=columns, rpm=rows), after a
10-word preamble. Output is oriented RPM across the top, load down the side with
low load at the bottom.

  Fuel     @ 0x23EC : 7 load x 19 rpm, raw injection counts
  Ignition @ 0x210E : 11 load x 19 rpm, degrees BTDC = raw / 128

The RPM axis is a UNIFORM ESTIMATE (~0-6150 rpm); the load axis is relative.
Exact breakpoints are not stored in the ROM. Cell values are exact.

Usage:
    python extract_maps.py path/to/rom.bin [out_dir]
"""
import sys, os, csv

FUEL = dict(addr=0x23EC, load=7,  rpm=19, preamble=10)
IGN  = dict(addr=0x210E, load=11, rpm=19, preamble=10)
IGN_DEG_PER_LSB = 1 / 128.0
RPM_FULLSCALE = 6144            # from the 0x6000 preamble descriptor ~= rev limit


def w(d, o):
    return (d[o] << 8) | d[o + 1]


def grid(d, m):
    """Return rows indexed [load][rpm], load L0..Ln low..high."""
    gs = m["addr"] + 2 * m["preamble"]
    return [[w(d, gs + 2 * (r * m["load"] + c)) for r in range(m["rpm"])]
            for c in range(m["load"])]


def rpm_axis(n):
    return [round(i * RPM_FULLSCALE / (n - 1) / 10) * 10 for i in range(n)]


def save(path, g, rpm, fmt):
    # write high load first so the file top matches a low-load-at-bottom image
    with open(path, "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["load\\rpm_est"] + [str(r) for r in rpm])
        for li in reversed(range(len(g))):
            wr.writerow([f"L{li}"] + [fmt(v) for v in g[li]])
    print("wrote", path)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    d = open(sys.argv[1], "rb").read()
    out = sys.argv[2] if len(sys.argv) > 2 else "."
    os.makedirs(out, exist_ok=True)
    rpm = rpm_axis(FUEL["rpm"])

    fuel = grid(d, FUEL)
    save(os.path.join(out, "fuel_table.csv"), fuel, rpm, lambda v: str(v))

    ign = [[v * IGN_DEG_PER_LSB for v in row] for row in grid(d, IGN)]
    save(os.path.join(out, "ignition_degrees.csv"), ign, rpm,
         lambda v: f"{v:.1f}")


if __name__ == "__main__":
    main()

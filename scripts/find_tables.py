#!/usr/bin/env python3
"""Find every calibration table the firmware references.

The firmware addresses tables with the idiom `FD B9 <table_base>`. Scanning the
code region for `FD B9` targets inside the calibration block (0x1800-0x36FF)
yields the authoritative list of tables actually used.

Usage:
    python find_tables.py path/to/rom.bin [out.csv]
"""
import sys, csv, collections

ROM_LO, ROM_HI = 0x1800, 0x36FF          # calibration data block
CODE_LO, CODE_HI = 0x3700, 0x10000       # program code


def w(d, o):
    return (d[o] << 8) | d[o + 1]        # 16-bit big-endian


def framed_n(d, o):
    """Return N for a self-describing header `10 00 N0 00 00 0N`, else None."""
    if (d[o] == 0x10 and d[o + 1] == 0x00 and d[o + 3] == 0x00 and
            d[o + 4] == 0x00 and (d[o + 2] >> 4) == d[o + 5] and
            1 <= d[o + 5] <= 15 and (d[o + 2] & 0x0F) == 0):
        return d[o + 5]
    return None


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    d = open(sys.argv[1], "rb").read()
    out = sys.argv[2] if len(sys.argv) > 2 else "table_catalog.csv"

    refs = collections.Counter()
    for i in range(CODE_LO, CODE_HI - 3):
        if d[i] == 0xFD and d[i + 1] == 0xB9:
            a = (d[i + 2] << 8) | d[i + 3]
            if ROM_LO <= a <= ROM_HI:
                refs[a] += 1

    starts = sorted(refs)
    rows = []
    for idx, a in enumerate(starts):
        nxt = starts[idx + 1] if idx + 1 < len(starts) else ROM_HI + 1
        N = framed_n(d, a)
        if N:                                   # self-describing 1-D table
            vals = [w(d, a + 6 + 2 * k) for k in range(N)]
            kind = "framed"
        else:                                   # bare map / curve
            vals = [w(d, a + 2 * k) for k in range((nxt - a) // 2)]
            while vals and vals[-1] in (0x8A82, 0xFFFF):
                vals.pop()
            kind = "bare"
        mn, mx = (min(vals), max(vals)) if vals else (0, 0)
        rows.append((f"0x{a:04X}", kind, refs[a], len(vals), mn, mx,
                     f"{mn/4096:.3f}", f"{mx/4096:.3f}"))

    with open(out, "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["addr", "storage", "code_refs", "n_words",
                     "min", "max", "min_Q12", "max_Q12"])
        wr.writerows(rows)
    print(f"{len(rows)} code-referenced tables -> {out}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Classify every code-referenced table by the SENSOR/STATE variable that indexes it.

Each table is used via the idiom `FD B9 <table>` (+ one or more `FD BB <var>`
index loads) + a call to an interpolation routine. The index variable(s) reveal
which input drives the table, which is the basis for assigning a role.

Interpolators:  0xDCB4 = 2-D RPM x load map ; 0xDAD2 = 1-D curve ;
                0xDBC0/0xDB1C = table helpers ; 0x9CE0/0xDC2E = other map interps.
Known indices:  0x08EE = RPM ; 0x0966 = LOAD (smoothed; physical unit undecoded).

Usage:  python analyze_roles.py path/to/rom.bin [out.csv]
"""
import sys, csv, collections

CAL_LO, CAL_HI = 0x1800, 0x36FF
CODE_LO, CODE_HI = 0x3700, 0x10000
KNOWN = {0x08EE: "RPM", 0x0966: "LOAD"}
INTERP = {0xDCB4: "MAP2D", 0xDAD2: "CURVE1D", 0xDBC0: "help_DBC0",
          0xDB1C: "help_DB1C", 0x9CE0: "MAPi_9CE0", 0xDC2E: "MAPi_DC2E",
          0x9993: "help_9993"}


def w(d, o):
    return (d[o] << 8) | d[o + 1]


def setup_block(d, pos):
    """Index vars (FD BB) in a window around FD B9 at pos, and the interp call."""
    idxs, interp = [], None
    for j in range(max(0, pos - 14), pos):              # indices loaded before base
        if d[j] == 0xFD and d[j + 1] == 0xBB:
            idxs.append(w(d, j + 2))
    k = pos + 4
    while k < min(pos + 40, CODE_HI - 3):
        if d[k] == 0xFD and d[k + 1] == 0xBB:
            idxs.append(w(d, k + 2)); k += 4; continue
        if d[k] == 0x9D and d[k + 1] in (0xBB, 0xFB):
            interp = w(d, k + 2); break
        k += 1
    return idxs, interp


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    d = open(sys.argv[1], "rb").read()
    out = sys.argv[2] if len(sys.argv) > 2 else "map_roles.csv"

    by = collections.defaultdict(lambda: ([], set()))
    i = CODE_LO
    while i < CODE_HI - 3:
        if d[i] == 0xFD and d[i + 1] == 0xB9:
            a = w(d, i + 2)
            if CAL_LO <= a <= CAL_HI:
                idxs, interp = setup_block(d, i)
                lst, iset = by[a]
                for x in idxs:
                    if x not in lst:
                        lst.append(x)
                if interp is not None:
                    iset.add(interp)
        i += 1

    rows = []
    for a in sorted(by):
        lst, iset = by[a]
        idxlabel = ", ".join(KNOWN.get(x, f"{x:04X}") for x in lst) if lst else "-"
        ilabel = "/".join(INTERP.get(x, f"{x:04X}") for x in sorted(iset)) if iset else "-"
        rows.append((f"0x{a:04X}", ilabel, idxlabel))

    with open(out, "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["addr", "interp", "index_vars"])
        wr.writerows(rows)
    print(f"{len(rows)} tables classified -> {out}")


if __name__ == "__main__":
    main()

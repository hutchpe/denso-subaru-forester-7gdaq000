# Calibration format

## Numeric conventions

- **16-bit big-endian words** are the storage unit for maps, curves and most
  constants (high byte first).
- **Q12 fixed-point** for multipliers and corrections: `0x1000 = 4096 =
  1.000×`, so a cell of `0x0CCD` (3277) is about 0.80× and `0x1333` (4915) is
  about 1.20×.
- **Ignition advance** is stored at **128 counts per degree** (`°BTDC =
  raw/128`), so `0x0800 = 16.0°` and `0x1000 = 32.0°`.

## Self-describing (framed) tables

Many 1-D tables are wrapped in a 6-byte container header:

```
10 00   N0 00   00 0N   <N data words...>
 └ tag   └ N<<12  └ N (count)
```

That is the word `0x1000`, then `N` encoded in the high nibble of the next word,
then `N` as an integer, then `N` big-endian data words. The lookup routine reads
`N` at runtime, and consecutive framed tables of the same `N` form the rows of a
2-D map.

See [`data/framed_table_index.csv`](../data/framed_table_index.csv).

## Larger maps (bare)

The main 2-D maps (fuel `0x23EC`, ignition `0x210E`, and others) begin with a
preamble of about 10 words (scaling plus a shared axis descriptor `0800 1800
0006` / `6000 000C`), followed by the grid itself, stored **load-major** (load =
inner/columns, rpm = rows).

## Table access idiom

The firmware addresses every table through a consistent pattern:

```
FD B9 <rom_table>     ; load pointer to the table base
FD BB <ram_index>     ; load the index variable (e.g. rpm 0x08EE, load 0x0966)
9D BB <interp_routine> ; call the interpolator (e.g. 0xDCB4 for 2-D maps)
```

Scanning the code region for `FD B9` targets inside `0x1800–0x36FF` yields the
authoritative list of the **69 tables the firmware actually uses**, which is how
the catalogue was built (`scripts/find_tables.py`). The maps reached by the 2-D
interpolator `0xDCB4` are the primary RPM×load maps (fuel, ignition, and two
minor maps).

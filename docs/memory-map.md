# Memory map

The image splits cleanly into low RAM/IO, a calibration-data block, and program
code, determined by control-flow-opcode density and by tracing which addresses
the code reads as table bases.

| Range | Contents |
|---|---|
| `0x0000 – ~0x17FF` | RAM, I/O registers, scratch variables. Unused ROM bytes in this span are `0x8A82` fill. Index variables live here (rpm `0x08EE`, load `0x0966`). |
| `~0x1800 – 0x36FF` | **Calibration data** — maps, 1-D curves, axes, constants. All 69 code-referenced tables are here. |
| `0x3700 – 0xEF77` | Program code — main loop, interrupt handlers, lookup routines. |
| `0xEF68` | Calibration-ID string `"7gdaq000.aus"`. |
| `0xEF78 – 0xEFF5` | Interrupt dispatch stubs, 6 bytes each (`9D BB <tgt> 9F FF`). |
| `0xF800` | Build-stamp string `"EGC02/1996/07/02"`. |
| `0xF810` | Reset / init code (target of the reset vector). |
| `0xFF00` | Reset vector (big-endian) → `0xF810`. |
| `0xFF40 – 0xFF6F` | Interrupt vector table (big-endian pointers → dispatch stubs). |

## Notes

- `0x8A82` (decimal 35458) is the dominant fill word in the unused low region;
  `0x0000` fills other gaps. A grayscale render of the data region is at
  [`images/data_region_overview.png`](../images/data_region_overview.png).
- "RAM below ~`0x1800`, ROM calibration above" was confirmed by: the code
  *writes* low addresses (index/scratch) and *reads* `0x1800–0x36FF` as table
  bases; `FD B9` loads that point below `0x1800` hit fill or scratch, those at
  `0x1800+` hit real tabular data.
- No trivial whole-image checksum is present (the image does not sum to zero or
  a complement). A validation routine over a sub-range may exist in code; locate
  it before reflashing.

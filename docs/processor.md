# Processor

## Identity

A **proprietary Denso 8-bit microcontroller**. This ECU is a Subaru unit (see
[hardware.md](hardware.md)), but the MCU belongs to the common Denso 8-bit core
family that Denso used across its engine computers of the late-1980s to
mid-1990s — the same core lineage found in Denso-built Toyota **TCCS** (Toyota
Computer-Controlled System) ECUs. (TCCS is Toyota's name for that system; this
is a Subaru application of the same silicon, not a TCCS unit.) It was
mask-produced under Denso's own part numbers (community teardowns report a main
CPU marked `D151801-xxxx`, a knock-processor `D151801-xxxx`, an ADC
`D949577-xxxx`, typically ~64-pin packages, sometimes fabricated by Toshiba).
There is **no public datasheet**; all tooling is community-built (custom
disassemblers / IDA / Ghidra processor modules).

The 64 KB program + calibration lives in an external `27C512`-class EPROM — this
image.

## Family it is based on

Best described as a **custom core in the Motorola 6800 / 6805 lineage** (8-bit,
accumulator-based, memory-mapped I/O, **big-endian**) with some 6502-like
traits. It is **not** an NEC 78K, Hitachi H8 / SuperH, Mitsubishi, Fujitsu or
Intel architecture.

> Note: this early Denso 8-bit unit predates the Hitachi SuperH `SH7055/7058`
> ECUs that later Subarus (and much of the WRX/STI tuning scene) run. Those are
> a different, newer architecture — unrelated to this chip — so SH-based tools
> and maps do not apply here.

The "6800/6805-derived" conclusion is an **inference from the instruction set**,
not a licensing fact, but it is well supported.

## Evidence (observable in this image)

| Trait | Observation | Points to |
|---|---|---|
| Endianness | Vectors store pointers high-byte-first (`EF 78` → `0xEF78`) | Motorola family (not NEC/Intel) |
| Reset | `0xFF00` → `0xF810`; init sets RAM/ports, runs DI, calls subsystems | 6800-style boot |
| Bit test + branch | `0x35` (TBBS), restricted to the **low 32 bytes of RAM** | 6805 `BRSET`/`BRCLR` |
| Immediate load | `0x33`, operands **swapped** | 6800 assembler operand order |
| Disable interrupts | `0x05` | 6800/6805 `SEI`-equivalent |
| Call / jump | `9D BB <addr16>` and `9D FB <addr16>`; interrupt stubs are `9D BB <tgt> 9F FF` | compact accumulator ISA |

## Vectors & interrupts

- **Reset vector:** `0xFF00` (big-endian) → entry at `0xF810`.
- **Interrupt vector table:** `0xFF40–0xFF6F`, big-endian pointers into 6-byte
  dispatch stubs at `0xEF78+`, each of the form `9D BB <handler> 9F FF`.

## Key routines

| Address | Role |
|---|---|
| `0xF810` | Reset / init entry |
| `0xDCB4` | 2-D/3-D map interpolation (fuel, ignition, etc.) |
| `0xDAD2` | 1-D curve interpolation (most-called subroutine) |
| `0xDBC0`, `0xDB1C` | further table/interp helpers |

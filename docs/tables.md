# Tables

All 69 code-referenced tables are catalogued in
[`data/table_catalog.csv`](../data/table_catalog.csv) and rendered in
[`images/table_catalog.png`](../images/table_catalog.png). All maps are oriented
**RPM = X (horizontal), load = Y (vertical, low load at the bottom)**.

> **Roles by driving input.** Every table is now classified by the *input
> variable that indexes it*. See [`sensors.md`](sensors.md) and
> [`data/table_roles.csv`](../data/table_roles.csv). This is a firmer basis than
> shape alone, because the code reads the index variable directly from the
> access idiom.

## The four primary maps (`0xDCB4` interpolator)

| Map | Call site | Dims (load×rpm) | Shape | Role |
|---|---|---|---|---|
| `0x23EC` | `0x7C95` | 7 × 19 | rises with load; zero overrun row | **Fuel / injection** |
| `0x210E` | `0x7401` | 11 × 19 | falls with load, rises with rpm | **Ignition advance** |
| `0x1E10` | `0x6300` | 12 × 12 | mostly 0, sparse | **Secondary load×rpm map**. Result combined with curve `0x1DF4` at `0x62F4`. Likely transient/mode-specific (revised from "cranking") |
| `0x18D2` | `0x50BB` | 10 (rpm) | small | **RPM-indexed map**. Two lookups store to `0x09D4`/`0x09D6`. Likely dwell-vs-rpm or idle/ISC target |

Each is set up with `FD B9 <map>` plus the rpm (`0x08EE`) and load (`0x0966`)
index variables, then `9D BB DCB4`. The ignition map loads its indices via the
`FD B5/FD B6` register form, so an automated index scan shows none for `0x210E`,
but it is the same rpm×load pair as fuel.

## Ignition advance — `0x210E`

- **Scale:** `°BTDC = raw / 128` (`0x0800 = 16.0°`, `0x1000 = 32.0°`).
- **Surface:** about 16° idle, up to about 36° light-load cruise, pulled to 0–4°
  at high load / low rpm, climbing back with rpm. Range 0.0–36.3° BTDC.
- Why it is the ignition map: (1) a primary `0xDCB4` map co-indexed with fuel;
  (2) its lookup routine chains ignition correction tables
  `0x20E0 / 0x20F0 / 0x20F4 / 0x20F6 / 0x20F8`; (3) its load/rpm shape is the
  physical inverse of the fuel map.
- **Output path now traced** to the igniter output-compare register (see
  [`ignition-output.md`](ignition-output.md)): the final advance lands in RAM at
  `0x0ABC`, is converted degrees-to-timer ticks, and drives output-compare
  `0x0212`.

Data: [`data/ignition_degrees.csv`](../data/ignition_degrees.csv).

## Fuel / injection — `0x23EC`

Raw injection-quantity counts, 0–1585, rising with load. The lowest-load row is
the overrun/fuel-cut line, and the high-rpm/low-load corner drops to 0 for
deceleration fuel cut. The injector output-compare channel is `0x0222`.

Data: [`data/fuel_table.csv`](../data/fuel_table.csv).

## Correction families (by driving input)

See [`data/table_roles.csv`](../data/table_roles.csv) for all 69. The largest
coherent groups:

- **Coolant temp (`0x0924`), 22 tables:** the warmup/temperature correction
  family (fuel enrichment, cold ignition/idle trims), including primary+backup
  curve pairs (`0x1D72`≈`0x1D90`). `0x2B9C` is a disabled correction (all ×1.0).
- **Load (`0x0966`), 13 tables:** fuel map, rev-limit/threshold map `0x26BC`,
  the secondary map `0x1E10`, and load-axis correction curves.
- **Throttle/accel (`0x090E`), 8 tables:** map `0x18E7` plus the
  acceleration-enrichment group `0x2790 / 0x27A2 / 0x27B4`.
- **ADC-channel sensor (`0x08DC`, raw `0x00AA`), 3 tables:** `0x297A`, the 4×19
  map `0x2A6C`, and `0x2B32`, an air-temp or baro/altitude family.

## Other notable tables

- `0x26BC`: rev-limit / RPM-threshold map (cells clamped between 500 and 6250;
  about 6250 rpm ceiling).
- `0x2B9C`: an 11-wide correction left at all `×1.0` (effectively disabled).
- `0x3028`: a rising axis/curve.
- A large set of 1-D Q12 correction curves (see `framed_table_index.csv`), many
  present as primary + duplicate pairs (a main + backup/limp-home copy).

## Axes

The breakpoint arrays are **not** stored as plain tables. The rpm/load indices
are computed by near-linear scaling of the sensors, so the axes are close to
**uniform**. Evidence:

- The rpm/load index computation (`0x08EE` near `0x3FA5`, `0x0966` near
  `0x4808`) scales the raw sensor rather than searching a breakpoint array.
- The shared map preamble axis descriptor's rpm full-scale term `0x6000` (24576)
  corresponds to about 6144 rpm, matching the about 6250 rpm rev limit.
- Load (`0x0966`) is assembled with smoothing in a dedicated routine (`~0x4808`,
  raw read via `0x662E`). The factory pinout ([pinout.md](pinout.md)) confirms
  load is manifold absolute pressure (kPa), so the ECU is speed-density. The
  "fuel map" is an injection-quantity map rather than a VE model regardless.

So the RPM axis is published here as a **uniform ~0–6150 rpm estimate** (step
about 341 rpm over 19 points), and the load axis is MAP (kPa). Its direction is
certain (low→high), but the exact kPa breakpoints are not stored in the ROM, so
anchor them with a log or the sensor transfer function
([pinout.md](pinout.md#load-axis--map)). The cell *values* are exact, and the
axis *labels* are estimates.

## Relative VE

The Denso fuel map is an **injection-quantity** map rather than a VE model, so
there is no exact conversion to volumetric efficiency.
[`data/ve_table_relative.csv`](../data/ve_table_relative.csv) is the fuel surface
normalised to 0–100% (max = 100%), a usable *starting shape* for a TunerStudio
(Speeduino / MegaSquirt) VE table rather than a calibrated VE.

Caveats:

- Set the absolute level from your engine (`reqFuel`: displacement, injector
  flow, cylinders, target AFR).
- A true VE table is flatter up the load axis (VE ≈ fuel / MAP). This one still
  rises steeply with load because it is fuel demand, and the fuel-cut cells read
  0. For a genuine VE you must divide out MAP, which needs the load axis in real
  kPa.
- A Speeduino VE table is typically 16×16 on RPM×kPa, so resample from the native
  19×7.

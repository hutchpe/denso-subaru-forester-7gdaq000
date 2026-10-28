# Sensor / state variables and table roles

This classifies every one of the 69 code-referenced tables by the **input
variable that indexes it**, which is the most reliable signal for a table's role
because the code reads it directly from the access idiom (`FD BB <var>`) rather
than guessing it from shape. Reproduce it with `scripts/analyze_roles.py`, and
the curated result with inferred roles is in `data/table_roles.csv`.

## How a table's driver is read
Every table is used as:

```
FD B9 <table>     ; table base
FD BB <var>       ; one or more index variables  <-- identifies the driving input
9D BB <interp>    ; 0xDCB4 (2-D map) or 0xDAD2 (1-D curve), etc.
```

Grouping the 69 tables by their `<var>` gives coherent subsystems.

## The input variables

Identities marked **✓ pinout** are corroborated by the factory ECM I/O pinout
([pinout.md](pinout.md)), which confirms the sensor set and signal types.

| Var | Identity | Basis | Confidence |
|---|---|---|---|
| `0x08EE` | **Engine RPM** | written by crank ISR period (`0x0938`) → `0x3FA3` | VERIFIED |
| `0x0966` | **Engine load = MAP (manifold pressure)** | load variable for fuel/ignition; pinout confirms a MAP sensor | VERIFIED + ✓ pinout |
| `0x0924` | **Coolant temp (ECT)** — dominant warmup input | indexes 22 correction curves (classic warmup shape). ECT confirmed in pinout | high + ✓ pinout |
| `0x090E` | **Throttle position (TPS)** | drives a 2-D map + accel-enrichment group `0x2790/0x27A2/0x27B4`. TPS confirmed in pinout | high + ✓ pinout |
| `0x08DC` | **Intake air temp (IAT)** via ADC ch `0x00AA` | linearized from raw ADC `0x00AA` (writer `0x46DE`). IAT is the other analog temp input in the pinout | med + ✓ pinout |
| `0x08E8` | ignition-correction state (knock/warmup) | drives ignition corrections `0x20F8`, `0x29AC`. Knock sensor confirmed in pinout | inferred (low) |
| `0x0B78`,`0x0B68`,`0x0BCE`,`0x0BD2` | auxiliary subsystem inputs (VSS / gear / purge?) | each drives a small coherent table group in the `0x2CDA–0x2E1E` block. VSS confirmed in pinout | inferred (low) |
| others (`0x092A`,`0x097C`,`0x0A32`,`0x0914`,`0x08DE`,`0x08E0`,`0x08FA`,`0x0BC4`) | aux state vars | single-table drivers | inferred (low) |

**Load is MAP.** The load variable `0x0966` is manifold absolute pressure (kPa),
confirmed by the factory pinout ([pinout.md](pinout.md)). Internally it is
assembled and smoothed in a routine near `0x4808` (raw read via `0x662E`) with
fixed scale constants, consistent with reading and linearising a MAP ADC
voltage. The earlier frequency/airflow guess was wrong, and `0x0249` turned out
to be a scale constant rather than an I/O register.

## Tables grouped by driving input

- **Coolant temp `0x0924` (22 tables):** `0x1AD6 0x1AF0 0x1B00 0x1B24 0x1B4A
  0x1B68 0x1D36 0x1D54 0x1D72 0x1D90 0x1DAE 0x1DFA 0x1F5E 0x2032 0x2064 0x22E4
  0x2370 0x2588 0x29CC 0x29DA 0x2B7E 0x2B9C`. These are the warmup/temperature
  correction family (fuel enrichment, cold ignition/idle trims, and the
  primary+backup curve pairs such as `0x1D72`≈`0x1D90`), and `0x2B9C` is left at
  all ×1.0 as a disabled correction.
- **Load `0x0966` (13 tables):** the fuel map `0x23EC`, the rev-limit/threshold
  map `0x26BC`, the special map `0x1E10`, and load-axis correction curves
  (`0x20E0` ignition-vs-load, `0x253C`, `0x2816`, and others).
- **Throttle/accel `0x090E` (8 tables):** map `0x18E7` plus the acceleration
  enrichment group `0x2790 / 0x27A2 / 0x27B4` and `0x1DE6 / 0x29BA / 0x285E /
  0x2F60`.
- **ADC-channel sensor `0x08DC` (3 tables):** `0x297A`, the 4×19 map `0x2A6C`,
  and `0x2B32`, an air-temp or baro/altitude correction family.
- **Aux subsystem `0x0B78` (3 tables):** `0x2DD0 / 0x2DF8 / 0x2E1E`, a
  self-contained map+curve group on a distinct input.

## The four `0xDCB4` (2-D map) primaries, revisited
| Map | Index vars | Role |
|---|---|---|
| `0x23EC` | LOAD + RPM | **Fuel / injection** (VERIFIED) |
| `0x210E` | RPM × load* | **Ignition advance** (VERIFIED) |
| `0x1E10` | LOAD + RPM | secondary load×rpm map. Result combined with curve `0x1DF4` at `0x62F4`. Likely a **transient / mode-specific** map, not cranking as previously guessed |
| `0x18D2` | RPM | small RPM-indexed map. Two lookups store to `0x09D4`/`0x09D6`. Likely **dwell-vs-rpm or an idle/ISC target**, not a general map |

*The ignition map's index loads use the `FD B5/FD B6` register form rather than
`FD BB`, so `analyze_roles.py` shows no captured index for `0x210E`. It is the
same rpm×load pair as fuel, established previously by the co-indexed lookup.

## Caveats
The input-to-table grouping is verified, read straight from the code. The
*physical* sensor names are assigned from curve shape, correction count, and,
for the main inputs, the **factory ECM pinout** ([pinout.md](pinout.md)), which
confirms the sensor set (MAP, TPS, ECT, IAT, O2, knock, VSS). What is still not
proven at the silicon level is the exact **ADC-channel to RAM-variable** mapping,
so the lower-confidence identities, such as which aux var is VSS vs gear, remain
hypotheses to confirm against a live sensor sweep.

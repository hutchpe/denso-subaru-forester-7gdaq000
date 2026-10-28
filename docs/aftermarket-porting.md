# Porting the factory tune to an aftermarket ECU

This is the repo's main practical use. **Reflashing the factory Denso ECU is not
a realistic option** for an enthusiast. There is no known community flash tool
for this early Denso 8-bit unit (unlike the later Hitachi-SH Subaru ECUs that
RomRaider/Tactrix support). The calibration lives in a ROM that is not
field-reprogrammable in situ, and any checksum would have to be defeated blind.
So the intended use of everything here is as a **documented factory baseline to
replicate on a standalone ECU** (Link, Haltech, MoTeC, Emtron, Speeduino,
MegaSquirt, and similar).

The factory calibration is a useful starting point, and most of it ports
cleanly.

## What ports, and how

| Factory data | Where | How it ports |
|---|---|---|
| **Load axis = MAP (kPa)** | [pinout.md](pinout.md#load-axis--map) | Build your fuel and ignition tables on an **rpm × MAP(kPa)** grid (speed-density). |
| **Ignition map** (°BTDC) | [factory-tune.md](factory-tune.md) / [`ignition_degrees.csv`](../data/ignition_degrees.csv) | **Copy almost directly.** It is already in °BTDC on rpm×load. |
| **Fuel map** (injection qty) | [`fuel_table.csv`](../data/fuel_table.csv) | Convert to **VE** (recipe below). Use [`ve_table_relative.csv`](../data/ve_table_relative.csv) as the shape. |
| **Rev limit** ~6250 rpm | ROM `0x186A` | Set your soft/hard cut around it. |
| **Sensor set and scaling** | [pinout.md](pinout.md) | Reuse or replace. Scalings below. |
| **Outputs / firing** | [pinout.md](pinout.md) | Wasted-spark 2×, grouped injection 2×, firing order 1-3-2-4. |

## Engine and load basics

- **EJ202**: 2.0 L (1994 cc) SOHC naturally-aspirated flat-four, about 498
  cc/cyl.
- **Speed-density**: the factory ECU has a **MAP sensor and no MAF**, so load is
  **manifold pressure**. Build your VE/fuel and ignition tables on an **rpm ×
  kPa** axis. A typical NA kPa axis runs about 20–105 kPa.
- The factory maps are 19 rpm columns × (7 fuel / 11 ignition) load rows, on a
  roughly uniform rpm axis of about 0–6150. Resample onto your ECU's grid
  (commonly 16×16) by interpolation. The values matter, the grid size does not.

## Ignition

The factory ignition map is already stored in **°BTDC** on rpm×load, so it drops
almost straight into an aftermarket ignition table. Full numbers:
[factory-tune.md](factory-tune.md). Raw CSV:
[`ignition_degrees.csv`](../data/ignition_degrees.csv).

- Range 0–36°. About 16° idle, about 36° light-load cruise, pulled to single
  digits at high load/low rpm.
- **Confirm the scale** (the ROM stores advance as `raw/128`) against a timing
  light at a known point before you trust absolute numbers.
- Start **conservative** (pull 2–4° against factory) on pump fuel until you have
  logged knock, then work back up. The factory has no wideband or modern knock
  control. You do, so use them.

## Fuel: converting injection-quantity to VE

The factory fuel map stores a raw **injection quantity** (0–1585 counts), not VE
and not ms. There is no exact conversion, but the **shape** is a good VE
starting point ([`ve_table_relative.csv`](../data/ve_table_relative.csv),
normalised 0–100%). To anchor the absolute level on your ECU:

1. Set your global fuel parameters from **your** hardware: displacement 1994 cc,
   4 cylinders, **your injector flow** (factory NA EJ injectors are about
   360–440 cc @ 3 bar, so measure or use your actual injectors), fuel pressure,
   and target AFR (about 14.7 cruise, about 12.5–13.0 WOT for NA).
2. Load the relative VE shape onto your rpm × kPa grid.
3. Tune closed-loop/short-term trims to flatten it, then verify WOT on a
   wideband.

Because it is an injection-quantity map (not VE ÷ MAP), it rises more steeply
with load than a true VE surface. Expect to flatten the top of the load axis as
you calibrate. See [tables.md](tables.md#relative-ve).

## Sensors: reuse or replace (scalings from the factory pinout)

From [pinout.md](pinout.md):

| Sensor | Type | Factory signal | Aftermarket note |
|---|---|---|---|
| MAP | analog 0–5 V | ~3.5 V @ atmo, ~1.5 V @ idle | reuse w/ 2-point cal, or fit a known MAP sensor and use its scaling |
| TPS | analog 0–5 V | 0.2–1.0 V closed, 4.2–4.7 V open | reuse; calibrate closed/open |
| ECT | NTC thermistor | 0.4–2.4 V warm | reuse; use a Subaru/NTC cal table |
| IAT | NTC thermistor | 1.4–2.5 V | reuse; NTC cal |
| O2 | **narrowband** (0–0.9 V) | 0–0.9 V | **add a wideband** for tuning; keep NB only for basic closed-loop |
| Crank | **VR / reluctor** | ±7 V AC | set trigger to **reluctor**; get the trigger-wheel tooth count from your engine |
| Knock | piezo, 2.5 V bias | 2.5 V | reuse into your ECU's knock input if supported |
| VSS | pulsed 0/5 V | 0 or 5 V | speed input for speed-based functions |

## Outputs, firing order and trigger

- **Firing order 1-3-2-4.**
- **Ignition:** the factory is **wasted spark, 2 channels**. Coil A fires cyl
  **1 & 2**, coil B fires **3 & 4** (pins E22-3 and E22-9). You can replicate
  wasted-spark, or upgrade to coil-on-plug **sequential**. Sequential needs a
  **cam-sync** signal, and this factory system appears to run **crank-only**
  (wasted spark + grouped injection need no cam sensor). Verify whether your
  engine has a usable camshaft position sensor before you plan full sequential.
- **Injection:** the factory is **grouped/paired**. Injectors 1&2 fire together
  (E22-7), 3&4 together (E22-6). Aftermarket can run grouped (crank-only) or full
  sequential (with cam sync).
- **Aux outputs to wire:** idle-air-control valve (PWM, E22-4), fuel-pump relay,
  radiator fan relay(s), A/C relay, EVAP purge solenoid (PWM), tacho output,
  MIL. All are low-side relay/solenoid drives. See [pinout.md](pinout.md).

## Suggested starting-point checklist

1. Wire the engine harness to your ECU using [pinout.md](pinout.md). Set crank =
   **reluctor**, firing order **1-3-2-4**.
2. Configure **speed-density**, rpm × **kPa** axes.
3. Load the **ignition** map from [`ignition_degrees.csv`](../data/ignition_degrees.csv)
   (resampled), minus a safety margin.
4. Load the **VE shape** from [`ve_table_relative.csv`](../data/ve_table_relative.csv).
   Set global fuel from your injectors/displacement/AFR.
5. Set **rev limit** about 6250 (start lower).
6. Start wasted-spark + grouped injection (crank-only). Move to sequential later
   if you add cam sync.
7. First-start, idle, then **dyno/road-tune** on a wideband, logging knock.

## Important caveats

- **Axis labels are estimates.** Cell *values* are exact, but the rpm and kPa
  breakpoints are inferred (the ECU scales sensors to index the maps, it does not
  store breakpoint arrays). Treat the maps as *shapes* and re-reference the axes
  to your own logging. See [tables.md](tables.md#axes).
- This is an NA tune. It is a **baseline**, not a finished calibration. Validate
  everything on your engine, on a dyno where possible, with a wideband and knock
  monitoring.

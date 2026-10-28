# The ECU — hardware identification

The physical unit this ROM was read from is a Denso-built engine control unit
for the **Subaru Forester SF** (2001, Australian-delivered), consistent with the
naturally-aspirated **EJ202** (2.0 L SOHC flat-four). The ROM's roughly 6250 rpm
limit, injection-quantity fuel map and non-boost load axis all fit this NA
application rather than the turbo GT, which carries the `22611AG…` part number.

![ECU label](../images/ecu-label.jpg)

## The two part numbers (which is which)

The label carries two numbers, and both are part/model numbers rather than a
per-unit serial. The closest thing to a unit-specific identifier is the
calibration ID inside the ROM (`7gdaq000.aus`).

| Marking | Who assigns it | What it is |
|---|---|---|
| **`22611AF000`** | Subaru | **Subaru's ECU part number.** Subaru's engine-control-module part numbers all begin `22611…` (for example the turbo Forester is `22611AG572`). This is the number you order from Subaru, and the `AF` suffix distinguishes this calibration/variant. The circled **"7"** to its left is the Denso maker's mark. |
| **`112500-0103`** | Denso | **Denso's own hardware/manufacturing number** (`112500-xxxx` is Denso's format), shown with `12V` and `DENSO JAPAN`. It identifies the hardware Denso built, independent of the Subaru catalogue number. |

Other stamps on the case (`F9`, and a partially legible `J8-01` / `8C9…`) are
Denso production/revision marks.

> So `22611AF000` is the Subaru model/part number, `112500-0103` is the Denso
> hardware number, and `7gdaq000.aus` is the calibration ID inside the ROM
> (`.aus` = Australian market). None of the three is a unique serial.

## The board

![ECU board](../images/ecu-board.jpg)

Observations from the board photo, with identifications best-effort from
markings and layout rather than a full BOM:

- **Main MCU**: the large fine-pitch QFP in the centre. This is the proprietary
  Denso 8-bit microcontroller the firmware runs on (6800/6805-lineage core, no
  public datasheet). See [processor.md](processor.md).
- **Support IC**: the smaller package to the right of the MCU (pink/tan) is
  likely the analog front-end / ADC or a driver IC. Community teardowns of this
  era cite a Denso ADC such as `D949577-xxxx`.
- **Power supply**: two `47 µF 35 V` electrolytic capacitors and two `226`
  (22 µF-class) moulded inductors form the switching/linear supply that feeds the
  logic, which runs at the 12 V nominal shown on the label.
- **Output drivers**: the row of small transistor/driver packages along the
  lower edge drives the injectors and ignition, where the igniter/injector
  output-compare channels `0x0212` / `0x0222` from
  [ignition-output.md](ignition-output.md) terminate.
- **Clock**: the small can near the top edge is the oscillator/resonator.
- **Connectors**: four edge headers (two top, two bottom) for the engine
  harness. The board is conformal-coated (the green tint) for underhood use.
- Silkscreen `-0024` appears top-right (board revision).

*The ROM's owner took the photos, and all EXIF/location metadata has been
stripped from the copies in this repo.*

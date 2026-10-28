# Ignition output path — from computed advance to the coil

This traces the spark path end to end, from the ignition map lookup through the
degree-to-timer conversion to the hardware output-compare register that fires
the igniter, resolving open item #4 (the final ignition output register) to the
register level. The method is static control-flow tracing of the undocumented
Denso MCU, with confidence flagged per step.

## Summary of the chain

```
ignition map 0x210E  (rpm 0x08EE x load 0x0966, interp 0xDCB4)
        |  base advance (°BTDC = raw/128)
        v
correction curves 0x20E0 / 0x20F2 / 0x20F4 / 0x20F6 / 0x20F8  (interp 0xDAD2)
        |  summed in RAM
        v
FINAL ADVANCE  ->  0x0ABC   (and dwell/charge angle -> 0x0ABA)   [VERIFIED]
        |
        v  scheduler @ 0x7480-0x74D2: advance(°) x engine-period -> timer ticks
converter 0xDDBC / 0xDE00   (16-bit multiply/scale)              [VERIFIED routine]
        |
        v
scheduled fire time -> 0x0A9C ; spark-state flag 0x1555          [VERIFIED]
        |
        v  crank input-capture ISR 0xE1A4 (vector 0xFF40, highest priority)
reads input-capture 0x0242 + free-run timer 0x0040 -> engine period 0x0938
        |
        v  output-compare programming @ ~0xE3C3 (uses converter 0xDE00)
IGNITION OUTPUT-COMPARE REGISTER  0x0212  (16-bit; bit15 = output level)  [VERIFIED path]
        |
        v
igniter pin toggles at compare match -> coil fires
```

## Step detail

### 1. Final advance is assembled at `0x0ABC` (VERIFIED)
The ignition routine (lookup call at `0x7401`) computes the base advance from map
`0x210E`, then chains the correction curves via the 1-D interpolator `0xDAD2`.
The results accumulate in RAM:

```
7429: 71 F0 0A BE     ; store base map advance        -> 0x0ABE
7467: 71 F0 0A C0     ; store summed corrections       -> 0x0AC0
7484: 11 BB 0A BE / 14 BB 0A C0 / 71 F0 0A BC  ; 0x0ABC = 0x0ABE + 0x0AC0 (store @0x748C)
```

So `0x0ABC` holds the final spark advance (base + corrections), still in the
raw/128 degree representation, and `0x0ABA` holds a companion value (dwell / coil
charge angle) computed alongside it.

### 2. Degrees to timer ticks via `0xDDBC` / `0xDE00` (VERIFIED routine)
The scheduler at `0x7480-0x74D2` feeds the advance and dwell through the 16-bit
scaling routine `0xDDBC` (and its sibling `0xDE00`):

```
74A0: FD BB 0A BC            ; advance as input
74AE: 9D BB DD BC            ; call converter
74BA: FD BB 0A BA 9D BB DD BC ; convert dwell too
74D2: 71 F5 0A 9C            ; store scheduled fire time -> 0x0A9C
```

`0xDDBC` is a multiply/divide helper (`BD B9 … D1 A7 04 B1 A7 06 … D3 79 08 00`)
that multiplies the angle by the current engine period and rescales, which is the
standard crank-degrees-to-timer-count conversion. The result (`0x0A9C`) is the
absolute timer value at which the next event must occur, gated by the spark-state
word `0x1555`.

### 3. Crank input-capture ISR `0xE1A4` (vector `0xFF40`) (VERIFIED)
This is the **highest-priority interrupt** (first entry in the vector table) and
the engine-timing heartbeat. On each crank reference pulse it:

```
E1A7: 11 BB 02 42     ; read input-capture register 0x0242 (crank timestamp)
E1BD: 71 FB 00 40 09 38 ; copy free-running timer 0x0040 -> 0x0938
E1C7: 11 BB 09 38 / 14 BB 09 48 ; maintain inter-tooth period (0x0938/0x0948)
```

The maintained period at `0x0938` is what the main loop converts to RPM
(`0x08EE`, writer at `0x3FA3`) and what the degree-to-tick converter uses, so the
same ISR both measures engine speed and anchors the spark schedule.

### 4. Ignition output-compare register `0x0212` (VERIFIED path, INFERRED pin)
The output stage programs a 16-bit output-compare register whose top bit
(0x8000) is the output level and whose low 15 bits are the compare time:

```
E3C3: 11 BB 02 12 / 15 79 7F FF / 71 F0 02 12 ; clear bit15 (output low)
E3CF: FD B9 00 00 / 9D BB DE 00               ; compute next event time (converter)
E3D8: 11 BB 02 12 / 15 B9 80 00 / 71 F0 02 12 ; set bit15 (output high)
```

Toggling bit15 around a `0xDE00` (angle-to-count) conversion is the classic
Denso igniter output-compare idiom. The timer drives the IGt pin to the
programmed level at the compare match, so the coil charges (dwell) and fires at
the computed crank angle. **`0x0212` is the ignition timing output-compare
register.**

A second 16-bit compare register, **`0x0222`**, is programmed the same way, but
it is written from many more sites and is also read by the fuel/injection code
(`0x85FC`, `0x8648`), which is consistent with it being the **injector**
output-compare channel rather than ignition.

## Confidence
- Advance assembly at `0x0ABC`, the converter routines, the scheduled-time store
  at `0x0A9C`, and the crank ISR `0xE1A4` reading input-capture `0x0242` are all
  **VERIFIED** by direct control-flow tracing.
- For `0x0212` = ignition output-compare (against `0x0222` = injection), the
  register mechanics (bit15 level + compare time, fed by the degree-to-tick
  converter) are verified, but the **physical pin assignment** (which is IGt vs
  INJ) is a strong inference from usage rather than pin-probed. Confirm it on a
  scope or timing light before you rely on it for a hardware mod.

## Registers referenced (I/O map additions)
| Addr | Role |
|---|---|
| `0x0040` | free-running timer (counter) |
| `0x0242` | crank input-capture register (timestamp of crank pulse) |
| `0x0212` | ignition output-compare (bit15 = IGt level) |
| `0x0222` | injector output-compare (second channel) |
| `0x0938` / `0x0948` | inter-tooth period accumulator (→ RPM) |
| `0x0ABC` | final computed spark advance (raw/128 °BTDC) |
| `0x0ABA` | dwell / coil-charge angle |
| `0x0A9C` | scheduled absolute fire time (timer ticks) |
| `0x1555` | spark-scheduling state flag |

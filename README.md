# Neoclo Typhoon Ambient Edition — experimental build
Typhoon hardware rev 1.0, derived from Mutable Instruments Clouds, Supercell, Microcell, Typhoon.

Based on Patrick Dowling's [SuperParasites](https://github.com/patrickdowling/superparasites), pinned to commit `2e9ed7c8c860121baa287ccecfa0de4f4000dd7d`.
Build target: `VARIANT=MICROCELL` (STM32F4).

**Status: experimental source code, NOT validated on a real Typhoon.** A passing CI build does not imply safe firmware. Do not flash before verifying bootloader, MCU type, and recovery firmware.

## 8 slots
0. Classic Clouds — native, untouched granular processing.
1. Endless — WSOLA stretching with long windows. NOT yet true multi-layer Endless Processor.
2. Tape Memory — looping delay with slower pitch flutter.
3. Spectral Drift — original spectral engine with slow autonomous movement.
4. Shimmer Cathedral — Oliverb long reverb.
5. Harmonic Drone — resonant drone engine.
6. Dissolve Delay — Kammerl slices with gentle automated captures and reverb tail.
7. Spectral Ghost — gentler spectral cloud.

7 modes are modifications of existing SuperParasites algorithms, not completely new DSP engines. The normal mode menu, CV scaling, and original bootloader remain unmodified.

## Build
GitHub Actions → **Build experimental Typhoon Microcell firmware**. A workflow also starts on pushes to `main`.
For Mac/Linux with ARM toolchain, `numpy`, git, g++, make: `bash build.sh`. Output in `dist/`.

See [CONTROLS_RU.md](CONTROLS_RU.md) for control overview.

## Flashing safety
Do not upload these experimental files to the module without a known-working factory firmware/bootloader restoration path. Do not use ST-Link until the board pinout has been independently verified. Never connect guessed PCB pads to power or SWD.

#!/usr/bin/env bash
set -euo pipefail
BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC="$BASE_DIR/.upstream/superparasites"
UPSTREAM_SHA="2e9ed7c8c860121baa287ccecfa0de4f4000dd7d"
OUT="$BASE_DIR/dist"
for program in git make python3 g++ arm-none-eabi-gcc arm-none-eabi-g++ arm-none-eabi-objcopy arm-none-eabi-size; do
  if ! command -v "$program" >/dev/null 2>&1; then
    echo "Missing: $program" >&2; exit 2
  fi
done
mkdir -p "$BASE_DIR/.upstream" "$OUT"
if [ ! -d "$SRC/.git" ]; then
  git clone --no-checkout --filter=blob:none https://github.com/patrickdowling/superparasites.git "$SRC"
fi
cd "$SRC"
git fetch --depth 1 origin "$UPSTREAM_SHA"
git checkout --detach "$UPSTREAM_SHA"
git submodule update --init --recursive
if [ -e supercell/dsp/ambient_modes.h ]; then
  echo "Already patched upstream checkout. Remove .upstream first." >&2; exit 3
fi
python3 "$BASE_DIR/install_patch.py" "$SRC"
# The legacy 2016 toolchain makefile uses an unsupported -mthumb-interwork flag.
TOOLCHAIN_DIR="$(dirname "$(command -v arm-none-eabi-gcc)")/"
ARCHFLAGS="-mcpu=cortex-m4 -mthumb -mfloat-abi=hard -mfpu=fpv4-sp-d16 -funroll-loops"
make -f supercell/makefile -j2 VARIANT=MICROCELL TOOLCHAIN_PATH="$TOOLCHAIN_DIR" ARCHFLAGS="$ARCHFLAGS" build/microcell/microcell.bin
cp build/microcell/microcell.bin "$OUT/neoclo-typhoon-microcell-EXPERIMENTAL.bin"
arm-none-eabi-size build/microcell/microcell.elf | tee "$OUT/firmware-size.txt"
python3 "$BASE_DIR/encode_wav.py" "$OUT/neoclo-typhoon-microcell-EXPERIMENTAL.bin" -o "$OUT/neoclo-typhoon-microcell-EXPERIMENTAL.wav"
cd "$OUT"
sha256sum *.bin *.wav | tee SHA256SUMS.txt
echo "Experimental compiled firmware; no hardware tests. DO NOT FLASH without an original firmware recovery plan."

#!/usr/bin/env python3
"""Patch a pinned, clean patrickdowling/superparasites checkout. Fail closed."""
import argparse
from pathlib import Path

def replace_one(source, old, new, path):
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"Expected one anchor in {path}, found {count}: {old!r}")
    return source.replace(old, new, 1)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source_dir", type=Path)
    args = parser.parse_args()
    root = args.source_dir.resolve()
    pkg = Path(__file__).resolve().parent
    hdr = root / "supercell/dsp/granular_processor.h"
    cpp = root / "supercell/dsp/granular_processor.cc"
    dest = root / "supercell/dsp/ambient_modes.h"
    if not hdr.is_file() or not cpp.is_file() or dest.exists():
        raise RuntimeError("Missing source files, or ambient header already installed.")
    h, c = hdr.read_text(), cpp.read_text()
    h = replace_one(h, '#include "supercell/dsp/granular_processor.h"',
                    '#include "supercell/dsp/granular_processor.h"\n#include "supercell/dsp/ambient_modes.h"', hdr)
    h = replace_one(h, '  Parameters parameters_;',
                    '  Parameters parameters_;\n  AmbientModes ambient_modes_;', hdr)
    c = replace_one(c, '  phase_vocoder_.Init();\n\n  ResetFilters();',
                    '  phase_vocoder_.Init();\n  ambient_modes_.Init();\n\n  ResetFilters();', cpp)
    c = replace_one(c,
                    '  // Convert input buffers to float, and mixdown for mono processing.',
                    '  // Neoclo Ambient Edition: apply parameter map.\n'
                    '  ambient_modes_.Apply(static_cast<uint8_t>(playback_mode_), &parameters_, size);\n\n'
                    '  // Convert input buffers to float, and mixdown for mono processing.', cpp)
    c = replace_one(c,
                    '      if (playback_mode_ == PLAYBACK_MODE_KAMMERL) {\n'
                    '        dry_wet = 1.0f;\n'
                    '      }',
                    '      // Neoclo slot 7: keep manual wet/dry.', cpp)
    c = replace_one(c,
                    '  if (playback_mode_ != PLAYBACK_MODE_OLIVERB &&\n'
                    '      playback_mode_ != PLAYBACK_MODE_RESONESTOR &&\n'
                    '      playback_mode_ != PLAYBACK_MODE_KAMMERL) {\n'
                    '    float reverb_amount = parameters_.reverb;',
                    '  if (playback_mode_ != PLAYBACK_MODE_OLIVERB &&\n'
                    '      playback_mode_ != PLAYBACK_MODE_RESONESTOR) {\n'
                    '    float reverb_amount = parameters_.reverb;', cpp)
    # No writes until all exact source anchors have been verified.
    dest.write_text((pkg / 'ambient_modes.h').read_text())
    hdr.write_text(h)
    cpp.write_text(c)
    print("Ambient Edition patch applied:", root)

if __name__ == "__main__":
    main()

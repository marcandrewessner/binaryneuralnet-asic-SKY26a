"""
test_rom_sky130.py — Minimal ROM test: 64-byte × 8-bit, sky130A

Usage (run from the repo root):
    cd /path/to/OpenRAM
    python3 rom_compiler.py sky130/configs/test_rom_sky130.py

Docker (iic-osic-tools_chipathon_xserver):
    export PATH=/foss/tools/bin:$PATH
    cd /foss/designs/OpenRAM
    python3 rom_compiler.py sky130/configs/test_rom_sky130.py

Data file: sky130/configs/test_rom.hex — 64 bytes (0x00..0x3F)
Array organization auto-computed: 16 rows × 4 words/row × 8 bits = 32 cols
"""
import os
import sys

# ── ROM DATA ──────────────────────────────────────────────────────────────────
word_size  = 1        # bytes per word
data_type  = "hex"
rom_data   = "sky130/configs/test_rom.hex"   # relative to repo root

output_name = "rom_64x8_sky130"
output_path = "temp/"

# ── TECHNOLOGY ────────────────────────────────────────────────────────────────
tech_name           = "sky130"
nominal_corner_only = True
route_supplies      = "ring"

_openram_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_tech_path = os.path.join(_openram_root, "technology")
if _tech_path not in sys.path:
    sys.path.insert(0, _tech_path)

# ── VALIDATION ────────────────────────────────────────────────────────────────
check_lvsdrc  = True
inline_lvsdrc = False

# ── COMPILATION FLAGS ─────────────────────────────────────────────────────────
netlist_only  = False
verbose_level = 0

# ── DOCKER / ENVIRONMENT WORKAROUNDS ──────────────────────────────────────────
os.environ.setdefault("OPENRAM_MAGIC_NO_USER_RC", "1")
os.environ.setdefault("OPENRAM_SKIP_CONDA", "1")
use_conda = False

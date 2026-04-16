"""
sram_8x8_sky130.py — Reference configuration: 8-word × 8-bit, sky130A, 1 RW port

Usage (run from the repo root, not from this directory):
    cd /path/to/OpenRAM            # wherever you cloned the repo
    python3 sram_compiler.py sky130/configs/sram_8x8_sky130.py

Docker (iic-osic-tools_chipathon_xserver):
    export PATH=/foss/tools/bin:$PATH
    cd /foss/designs/OpenRAM
    python3 sram_compiler.py sky130/configs/sram_8x8_sky130.py

IMPORTANT: always use sram_compiler.py — never run this file directly with python3.
sram_compiler.py sets OPENRAM_HOME to the local compiler/ directory, which loads
the patched code instead of any system-installed openram package.
"""
import os
import sys

# ── MEMORY DIMENSIONS ────────────────────────────────────────────────────────
word_size     = 8
num_words     = 8
words_per_row = 1   # explicit — prevents OpenRAM from auto-calculating fewer rows
num_banks     = 1
num_spare_cols = 1
num_spare_rows = 1

num_rw_ports = 1
num_r_ports  = 0
num_w_ports  = 0

output_name  = "sram_8x8_sky130"
output_path  = "temp/"          # relative to where you run sram_compiler.py
                                # (repo root) — created automatically, gitignored

# ── TECHNOLOGY ───────────────────────────────────────────────────────────────
tech_name        = "sky130"
bitcell          = "sky130_fd_bd_sram__openram_sp_cell"
replica_bitcell  = "sky130_fd_bd_sram__openram_sp_cell_replica"
dummy_bitcell    = "sky130_fd_bd_sram__openram_sp_cell_dummy"
sp_factory_name  = "sky130"
nominal_corner_only = True
use_max_current  = False

process_corners  = ["TT"]
supply_voltages  = [1.8]
temperatures     = [25]

# Derive the repo root from this file's location — works wherever the repo is cloned.
# Layout: <repo>/sky130/configs/sram_8x8_sky130.py  →  3 levels up = repo root
_openram_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_tech_path = os.path.join(_openram_root, "technology")
if _tech_path not in sys.path:
    sys.path.insert(0, _tech_path)

# ── VALIDATION ───────────────────────────────────────────────────────────────
drc_name      = "magic"
lvs_name      = "netgen"
check_lvsdrc  = True
inline_lvsdrc = False

# ── XSCHEM SYMBOL ─────────────────────────────────────────────────────────────
# True = generate a .sym file in output_path after compilation
# The symbol can be placed directly in xschem to integrate the SRAM into a larger design.
generate_sym  = True

# ── COMPILATION FLAGS ────────────────────────────────────────────────────────
netlist_only     = False
analytical_delay = True
characterize     = False
trim_spice       = False
verbose_level    = 0

# ── DOCKER / ENVIRONMENT WORKAROUNDS ─────────────────────────────────────────
os.environ.setdefault("OPENRAM_MAGIC_NO_USER_RC", "1")
os.environ.setdefault("OPENRAM_SKIP_CONDA", "1")
use_conda = False

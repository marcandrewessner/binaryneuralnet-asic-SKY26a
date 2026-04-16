"""
test_sky130.py — Quick-test configuration: 16-word × 8-bit, sky130A, 1 RW port

Usage (run from the repo root):
    cd /path/to/OpenRAM
    python3 sram_compiler.py test_sky130.py

Docker (iic-osic-tools_chipathon_xserver):
    export PATH=/foss/tools/bin:$PATH
    cd /foss/designs/OpenRAM
    python3 sram_compiler.py test_sky130.py

IMPORTANT: always use sram_compiler.py — never run this file directly with python3.
"""
import os
import sys

# ── MEMORY DIMENSIONS ────────────────────────────────────────────────────────
word_size     = 8
num_words     = 16
words_per_row = 1   # explicit — prevents OpenRAM from auto-calculating fewer rows
num_banks     = 1
num_spare_cols = 1
num_spare_rows = 1

num_rw_ports = 1
num_r_ports  = 0
num_w_ports  = 0

output_name  = "sram_16x8_sky130"
output_path  = "temp/"

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

_openram_root = os.path.dirname(os.path.abspath(__file__))
_tech_path = os.path.join(_openram_root, "technology")
if _tech_path not in sys.path:
    sys.path.insert(0, _tech_path)
os.environ.setdefault("OPENRAM_TECH", os.path.join(_tech_path, "sky130") + os.sep)

# ── VALIDATION ───────────────────────────────────────────────────────────────
drc_name      = "magic"
lvs_name      = "netgen"
check_lvsdrc  = True
inline_lvsdrc = False

# ── XSCHEM SYMBOL ─────────────────────────────────────────────────────────────
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

# Configuration Guide — OpenRAM sky130

This repo supports two compilers: **SRAM** (read/write) and **ROM** (read-only,
data programmed at compile time). Each has its own config file format and entry point.

| Memory type | Compiler | Reference config |
|-------------|----------|-----------------|
| SRAM | `sram_compiler.py` | [sram_8x8_sky130.py](sram_8x8_sky130.py) |
| ROM | `rom_compiler.py` | [test_rom_sky130.py](test_rom_sky130.py) |

A configuration file is a plain Python script that sets variables consumed by OpenRAM.

> **Always run from the repo root** using the compiler script — never run the config
> file directly with `python3`. The compiler sets `OPENRAM_HOME` to the local
> `compiler/` directory, which loads the patched code instead of any system-installed
> `openram` package.

```bash
# Generic (any machine, any clone location)
cd /path/to/OpenRAM        # wherever you cloned the repo
python3 sram_compiler.py sky130/configs/my_sram.py

# Docker (iic-osic-tools_chipathon_xserver)
export PATH=/foss/tools/bin:$PATH
cd /foss/designs/OpenRAM
python3 sram_compiler.py sky130/configs/my_sram.py
```

---

## Minimal template

```python
import os, sys

# ── 1. MEMORY DIMENSIONS ────────────────────────────────────────────────────
# These are the only values you need to change between designs.

word_size     = 8      # bits per word  (multiples of 8 recommended)
num_words     = 8      # number of words (powers of 2 recommended)
words_per_row = 1      # always set explicitly — auto-calculation can reduce row count below sky130 minimum
num_banks     = 1      # 1 or 2

# sky130 arrays require even column/row counts.
# Add 1 spare col/row when word_size or num_words would otherwise be odd.
num_spare_cols = 1
num_spare_rows = 1

# Port configuration — choose exactly one mode:
num_rw_ports = 1   # single-port read/write (most common)
num_r_ports  = 0   # read-only port
num_w_ports  = 0   # write-only port

output_name  = "sram_{}x{}_sky130".format(num_words, word_size)
output_path  = "temp/"   # relative to the repo root — auto-created, gitignored

# ── 2. TECHNOLOGY ────────────────────────────────────────────────────────────
# Do not modify for sky130.

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

# Path-relative: works wherever the repo is cloned.
# Layout: <repo>/sky130/configs/<file>.py  →  3 dirname() calls = repo root
_openram_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_tech_path = os.path.join(_openram_root, "technology")
if _tech_path not in sys.path:
    sys.path.insert(0, _tech_path)

# ── 3. VALIDATION ────────────────────────────────────────────────────────────
# Runs Magic DRC + KLayout DRC + Netgen LVS automatically after GDS generation.
# Do not modify.

drc_name      = "magic"
lvs_name      = "netgen"
check_lvsdrc  = True    # True = run DRC+LVS; False = skip (faster iteration)
inline_lvsdrc = False   # top-level only — avoids false errors inside sub-cells

# ── 4. XSCHEM SYMBOL ─────────────────────────────────────────────────────────
# Set True to auto-generate a .sym file in output_path after compilation.
# The symbol can be placed in xschem to integrate the SRAM into a larger design.

generate_sym = False   # change to True when you need the xschem symbol

# ── 5. COMPILATION FLAGS ─────────────────────────────────────────────────────

netlist_only     = False   # False = generate GDS; True = netlist only (faster)
analytical_delay = True    # True = math model; False = Xyce simulation (slow)
characterize     = False   # True = full electrical characterisation (very slow)
trim_spice       = False   # True = strip unused sub-cells from the SPICE output

# Verbosity: 0 = errors+warnings only; 1 = milestones+DRC detail; 2 = full debug
verbose_level    = 0

# ── 6. DOCKER / ENVIRONMENT WORKAROUNDS ──────────────────────────────────────
# Do not modify.
# OPENRAM_MAGIC_NO_USER_RC: prevents Magic from loading ~/.magicrc, which can
#   interfere with PDK rules.
# OPENRAM_SKIP_CONDA / use_conda: disables Conda integration — not present in
#   the Docker container and causes crashes if left enabled.

os.environ.setdefault("OPENRAM_MAGIC_NO_USER_RC", "1")
os.environ.setdefault("OPENRAM_SKIP_CONDA", "1")
use_conda = False
```

---

## Key options explained

### Memory dimensions

| Option | Values | Effect |
|--------|--------|--------|
| `word_size` | integer | Bits per word. Use multiples of 8. |
| `num_words` | integer | Number of addressable words. Use powers of 2. |
| `words_per_row` | 1 | Always set explicitly. Without it, OpenRAM may auto-calculate a value that reduces the physical row count below sky130's minimum of 16. |
| `num_banks` | 1 or 2 | Physical banks. Use 1 for most designs. |
| `num_spare_cols` | 0 or 1 | Extra column so the array has an even column count — required by sky130. |
| `num_spare_rows` | 0 or 1 | Extra row so the array has an even row count — required by sky130. |
| `num_rw_ports` | 1 | Single read/write port (most common). |
| `num_r_ports` | 0 or 1 | Add a dedicated read-only port (dual-port mode). |
| `num_w_ports` | 0 or 1 | Add a dedicated write-only port (dual-port mode). |

### Technology

| Option | Values | Effect |
|--------|--------|--------|
| `tech_name` | `"sky130"` | PDK target. Loads `technology/sky130/`. Do not change. |
| `bitcell` | PDK cell name | Standard 6T SRAM cell that stores one bit. Do not change for sky130. |
| `replica_bitcell` | PDK cell name | Copy of the bitcell used to generate internal timing signals. Do not change. |
| `dummy_bitcell` | PDK cell name | Border cell that electrically isolates the array edges. Do not change. |
| `sp_factory_name` | `"sky130"` | Selects the SPICE transistor models used during characterisation. |
| `nominal_corner_only` | `True` / `False` | `True` = characterise only at TT/1.8V/25°C. `False` = all corners (slower). |
| `use_max_current` | `True` / `False` | `True` = use worst-case current for timing (conservative). Normally `False`. |
| `process_corners` | `["TT"]`, `["FF","SS","TT"]` | Corners to characterise. More corners = slower compilation. |
| `supply_voltages` | `[1.8]` | Nominal sky130 supply. Can add `[1.6, 1.8, 2.0]` for corner sweep. |
| `temperatures` | `[25]` | Temperature in °C. Can add `[0, 25, 85]` for corner sweep. |

### Validation

| Option | Values | Effect |
|--------|--------|--------|
| `check_lvsdrc` | `True` / `False` | `False` skips DRC+LVS — useful for fast iteration. |
| `inline_lvsdrc` | `False` | Always `False` — `True` runs DRC on each sub-cell and produces false errors. |

### Xschem symbol

| Option | Values | Effect |
|--------|--------|--------|
| `generate_sym` | `True` / `False` | `True` generates `<output_name>.sym` in `output_path` after compilation, ready to place in xschem. |

### Compilation flags

| Option | Values | Effect |
|--------|--------|--------|
| `netlist_only` | `True` / `False` | `True` skips GDS generation — outputs only SPICE/Verilog/Liberty (much faster). |
| `analytical_delay` | `True` / `False` | `True` = fast math model for timing. `False` = Xyce circuit simulation (very slow, more accurate). |
| `characterize` | `True` / `False` | `True` = full electrical characterisation with SPICE simulation (very slow). |
| `trim_spice` | `True` / `False` | `True` removes unused sub-cells from the SPICE output to reduce file size. |
| `verbose_level` | 0, 1, 2 | `1` shows Magic DRC breakdown, routing offsets, run stats. `2` is full debug. |

---

## Sizing constraints for sky130

### Minimum number of words — `num_words >= 16`

OpenRAM uses a **replica bitcell column** to generate the internal timing signal
that controls when the sense amplifier activates. This replica must represent the
RC delay of the real bitlines — if the array has too few rows, the replica delay
is too small and the sense amplifier fires too early, reading wrong data.

sky130 enforces a minimum of **16 physical rows** in the array. With
`words_per_row = 1`, this means `num_words >= 16`. This applies even for test
or debug compilations — there is no way to bypass it.

```
ERROR: Minimum number of rows is 16, but given X
```

This error means `num_words` is too small. Set `num_words = 16` as the minimum.

### Even column count — `word_size + num_rw_ports + num_spare_cols` must be even

sky130 requires the total column count to be even. The formula OpenRAM checks is:

```
word_size + num_rw_ports + num_spare_cols  must be even
```

Each RW port adds one **replica bitline (RBL)** column. For the common case of
`num_rw_ports = 1`:

| `word_size` | `num_rw_ports` | `num_spare_cols` | Total | Valid |
|-------------|----------------|-----------------|-------|-------|
| 8 | 1 | 0 | 9 — odd | ✗ |
| 8 | 1 | 1 | 10 — even | ✓ |
| 16 | 1 | 0 | 17 — odd | ✗ |
| 16 | 1 | 1 | 18 — even | ✓ |
| 4 | 1 | 1 | 6 — even | ✓ |

**Rule for single-port designs (`num_rw_ports = 1`):** `word_size + num_spare_cols`
must be odd (so that adding the 1 RBL makes the total even).
With even `word_size` (8, 16, 32…), always use `num_spare_cols = 1`.

### Always set `words_per_row = 1` explicitly

Without this, OpenRAM auto-calculates `words_per_row` in a way that can reduce
the physical row count below 16, triggering the error above even when
`num_words = 16`.

### Area estimation

```
area ≈ (word_size + num_spare_cols) × (num_words + num_spare_rows) × bitcell_area
```

Bitcell area for sky130: ~0.4 µm². Compilation time scales roughly linearly with area.

---

## PDK location

OpenRAM needs the sky130A PDK at compile time. The `technology/sky130/` directory
inside this repo contains Python tech files and DRC scripts, but **not** the full
foundry PDK (GDS/SPICE/LVS cells). The PDK cells come from one of these sources:

| Scenario | What to do |
|----------|-----------|
| **Docker `iic-osic-tools_chipathon_xserver`** | PDK is pre-installed at `/foss/pdk`. Nothing to do. |
| **Volare (recommended outside Docker)** | `pip install volare && volare enable --pdk sky130 e8294524` |
| **Manual / already installed** | Set `PDK_ROOT=/path/to/pdks` before running. |
| **Bundled `ciel/` inside this repo** | The `ciel/` directory ships the exact PDK version (e8294524) used during development. OpenRAM will find it automatically if `PDK_ROOT` is not set and the standard paths are absent. |

The `ciel/sky130/versions/e8294524.../sky130A/` tree also contains `sky130A.lydrc`,
the KLayout DRC script. OpenRAM searches for it automatically — you do not need to
set any extra variable.

---

## Common errors and fixes

### `ModuleNotFoundError: No module named 'sky130'`

OpenRAM cannot find the `technology/sky130/` directory.

- Make sure you are running **from the repo root**, not from `sky130/configs/`.
- Check that `_tech_path` resolves correctly:
  ```bash
  python3 -c "import os; f=os.path.abspath('sky130/configs/sram_8x8_sky130.py'); \
  print(os.path.dirname(os.path.dirname(os.path.dirname(f))))"
  # should print the repo root
  ```

### `ModuleNotFoundError: No module named 'openram'` or wrong version loaded

You ran the config file directly instead of via `sram_compiler.py`.

```bash
# Wrong:
python3 sky130/configs/my_sram.py

# Correct:
python3 sram_compiler.py sky130/configs/my_sram.py
```

### `klayout: command not found` or `magic: command not found`

The EDA tools are not in your `PATH`.

- **Docker**: `export PATH=/foss/tools/bin:$PATH`
- **Manual install**: add the install prefix to `PATH`, or set `check_lvsdrc = False`
  to skip DRC/LVS for now.

### `KeyError` on startup (Docker with anonymous UID)

Fixed in `globals.py` (Fix 5 in [../docs/drc_fixes.md](../docs/drc_fixes.md)).
If you still see it, you are running against the upstream package — use
`sram_compiler.py` so the local patched code is loaded.

### `FileNotFoundError: sky130A.lydrc` (KLayout DRC script not found)

Set `PDK_ROOT` to point to your sky130A installation:
```bash
export PDK_ROOT=/path/to/pdks
python3 sram_compiler.py sky130/configs/my_sram.py
```
Or use the bundled `ciel/` PDK by leaving `PDK_ROOT` unset when the repo is the
working directory.

### DRC fails with `m1.2` / `m3.2` violations

You are running against upstream OpenRAM, not this patched version.
Confirm the fixes are active:
```bash
grep "top_inst.by()" compiler/modules/bank.py
# should print the clamp line — if empty, the patch was not applied
```

---

# ROM Configuration Guide — sky130

## Running a ROM compilation

```bash
cd /path/to/OpenRAM
python3 rom_compiler.py sky130/configs/my_rom.py

# Docker:
export PATH=/foss/tools/bin:$PATH
cd /foss/designs/OpenRAM
python3 rom_compiler.py sky130/configs/my_rom.py
```

## Minimal template

```python
import os, sys

# ── ROM DATA ──────────────────────────────────────────────────────────────────
word_size  = 1                          # bytes per word (not bits)
data_type  = "hex"                      # "hex" or "bin"
rom_data   = "sky130/configs/my_rom.hex"  # path relative to repo root

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
```

## Key options explained

| Option | Values | Effect |
|--------|--------|--------|
| `word_size` | integer | **Bytes** per word (not bits — ROM uses bytes). A 1-byte word = 8 bits per column group. |
| `data_type` | `"hex"` / `"bin"` | Format of the data file. `"hex"` is a plain hex string (e.g. `deadbeef…`). `"bin"` is a raw binary file. |
| `rom_data` | file path | Path to the data file, **relative to the repo root** (where you run `rom_compiler.py`). |
| `words_per_row` | integer / omit | How many words share a wordline. If omitted, auto-computed to make the array roughly square. |
| `route_supplies` | `"ring"` | Power distribution style. `"ring"` surrounds the block with a power ring. |
| `check_lvsdrc` | `True` / `False` | Run Magic DRC + KLayout DRC + Netgen LVS after layout. |

## Array sizing

The ROM has no `num_words` parameter — it is derived from the data file:

```
num_words = file_size_in_bytes / word_size
```

Array dimensions are then auto-computed:

```
words_per_row ≈ ceil(sqrt(num_words) / (2 × word_size))
rows          = num_words / words_per_row
cols          = words_per_row × word_size × 8
```

**Minimum data file size:** there is no hard row minimum like the SRAM's 16-row
constraint. In practice, use at least 64 bytes (`word_size=1`) to get a reasonable
array shape (16 rows × 4 words/row × 8 cols = 32 cols).

## Preparing a data file

```bash
# 64 bytes, values 0x00–0x3F (hex format)
python3 -c "open('my_rom.hex','w').write(bytes(range(64)).hex())"

# 256 bytes of zeros (binary format)
python3 -c "open('my_rom.bin','wb').write(bytes(256))"

# From a compiled firmware binary (binary format)
cp firmware.bin sky130/configs/my_rom.bin
# → set data_type = "bin" and word_size to match your bus width
```

## ROM vs SRAM differences

| | SRAM | ROM |
|--|------|-----|
| Compiler | `sram_compiler.py` | `rom_compiler.py` |
| `word_size` unit | bits | **bytes** |
| `num_words` | set explicitly | auto from file size |
| Data | written at runtime | fixed at compile time |
| Output files | sp, v, lef, gds, lib, lvs, sym | sp, v, lef, gds |
| Timing model | ✓ `.lib` | ✗ (TODO) |
| xschem symbol | ✓ `generate_sym = True` | ✗ |
| Power distribution | internal stripes | `route_supplies = "ring"` |

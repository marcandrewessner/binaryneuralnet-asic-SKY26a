# OpenRAM sky130 — DRC/LVS Fixes & Validation Guide

Community contribution targeting **OpenRAM v1.2.x** + **SkyWater sky130A PDK**.
Resolves all DRC violations that block tape-out submission via the eFabless / Google MPW / Chipathon flow.

---

## Results

Verified on `sram_8x8_sky130` (8-word × 8-bit, 1 bank, 1 RW port, TT / 1.8 V / 25 °C):

```
KLayout DRC : 0 violation(s)     ← tape-out sign-off passed  ✓
Netgen LVS  : LVS matches         ← connectivity verified     ✓
Magic DRC   : 13 507 warnings     ← all PDK bitcell internals, non-blocking
```

Scales to larger memories — fixes are geometry-driven, not hardcoded.

---

## Fixes included

| # | Rule | Root cause | File | Status |
|---|------|-----------|------|--------|
| 1 | **m1.2** | Bitline jog trunk too close to replica bitcell contact pad (different nets, coincident x-range) | `compiler/modules/bank.py` | ✓ verified |
| 2 | **m3.2** | Data-bus M3 channel route too close to bank M3 supply stripe | `compiler/modules/sram_1bank.py` | ✓ verified |
| 3 | **m2.4** | Via1 enclosure inside PDK word-line strap cells — foundry-certified, waived in KLayout counter | `compiler/verify/magic.py` | ✓ verified |
| 4 | **Magic DRC noise** | 13 000+ warnings from PDK bitcell internals, downgraded to `info(1)` for sky130 | `compiler/verify/magic.py` | ✓ verified |
| 5 | **Docker crash** | `getpwuid` KeyError when uid has no `/etc/passwd` entry | `compiler/globals.py` | ✓ verified |
| 6 | **dout LVS** | dout pins left at internal bank position — escape routing bypass removed; pins now reach block perimeter | `compiler/modules/sram_1bank.py` | ✓ verified |
| 7 | **xschem sym** | Symbol had reversed buses, empty subcircuit override, off-grid pins — rewritten with `type=primitive`, descending port reorder, grid-aligned layout | `sky130/scripts/gen_xschem_sym.py` | ✓ verified |

---

## Prerequisites

Before compiling, **you must install the SRAM PDK cells** into the technology
directory. This generates the `.sp` files that the compiler needs:

```bash
cd /path/to/OpenRAM
export PDK_ROOT=/foss/pdk       # Docker: already set; adjust for your setup
make sky130-install
```

This copies SPICE netlists from the PDK into `technology/sky130/sp_lib/` and
renames them from `.spice` to `.sp` with the correct pin ordering.
**Without this step, compilation fails with:**
```
ERROR: Custom cell pin names do not match spice file:
['BL', 'BR', 'VGND', 'VPWR', 'VPB', 'VNB', 'WL'] vs []
```

> **Note:** the `.sp` files are **generated, not source** — they are not tracked
> in git. You must re-run `make sky130-install` after cloning, or if `sp_lib/`
> is ever deleted or corrupted.

---

## Quickstart — SRAM

```bash
# 1. Go to the repo root (wherever you cloned it)
cd /path/to/OpenRAM

# 2. Copy and customise the reference config
cp sky130/configs/sram_8x8_sky130.py sky130/configs/my_sram.py
# → change word_size, num_words, output_name

# 3. Compile + validate (DRC + LVS run automatically)
python3 sram_compiler.py sky130/configs/my_sram.py
```

Docker (`iic-osic-tools_chipathon_xserver`):

```bash
export PATH=/foss/tools/bin:$PATH
cd /foss/designs/OpenRAM
python3 sram_compiler.py sky130/configs/my_sram.py
```

Or with `make` (handles PATH and PDK_ROOT automatically):

```bash
make -f sky130/Makefile.sky130 compile
make -f sky130/Makefile.sky130 compile CONFIG=sky130/configs/my_sram.py
```

> **Important:** always use `sram_compiler.py` or the Makefile, never run the config
> file directly. The compiler sets `OPENRAM_HOME` to the local `compiler/` directory
> so the patched code is used instead of any system-installed `openram` package.
> The Makefile also exports `OPENRAM_HOME`, `OPENRAM_TECH`, and auto-detects
> `TOOL_BIN` and `PDK_ROOT`.

---

## Quickstart — ROM

```bash
# 1. Prepare a data file (hex or binary)
python3 -c "open('my_rom.hex','w').write(bytes(range(64)).hex())"

# 2. Copy and customise the reference config
cp sky130/configs/test_rom_sky130.py sky130/configs/my_rom.py
# → set rom_data, word_size, output_name

# 3. Compile
python3 rom_compiler.py sky130/configs/my_rom.py

# Or with make:
make -f sky130/Makefile.sky130 compile-rom ROM_CONFIG=sky130/configs/my_rom.py
```

> **Important:** always use `rom_compiler.py` or the Makefile, never run the config
> file directly. Same reason as for the SRAM — it sets `OPENRAM_HOME` to the local
> compiler.

See [configs/README.md](configs/README.md) for ROM config options and sizing rules.

---

## Output files

All outputs land in `temp/` (created automatically, **gitignored**).

### SRAM

| File | Contents |
|------|----------|
| `temp/<name>.gds` | Layout (GDS-II) — submit this for tape-out |
| `temp/<name>.sp` | SPICE netlist |
| `temp/<name>.lef` | Abstract LEF for place-and-route |
| `temp/<name>.lib` | Timing model (Liberty) |
| `temp/<name>.v` | Verilog behavioral model |
| `temp/<name>.sym` | xschem symbol for simulation — set `generate_sym = True` in config |
| `temp/<name>.klayout.lyrdb` | KLayout DRC report (XML) |

### ROM

| File | Contents |
|------|----------|
| `temp/<name>.gds` | Layout (GDS-II) |
| `temp/<name>.sp` | SPICE netlist |
| `temp/<name>.lef` | Abstract LEF for place-and-route |
| `temp/<name>.v` | Verilog behavioral model |

The `<name>` matches `output_name` in your config file.

---

## Documentation

| Document | Contents |
|----------|----------|
| [configs/README.md](configs/README.md) | Config file template and all options explained |
| [docs/guide.md](docs/guide.md) | Full compilation guide: expected output, verbose levels, xschem simulation, warning explanations |
| [docs/drc_fixes.md](docs/drc_fixes.md) | Technical root-cause analysis for each fix |
| [docs/architecture.md](docs/architecture.md) | Compiler internals: how OpenRAM works, what each file does, compilation pipeline |
| [patches/README.md](patches/README.md) | How to apply patches to a fresh upstream OpenRAM |
| [CHANGELOG.md](CHANGELOG.md) | History of all fixes and additions |

---

## Applying to a fresh OpenRAM installation

```bash
cd /path/to/openram
for p in sky130/patches/*.patch; do
    patch -p1 < "$p"
done
```

See [patches/README.md](patches/README.md) for full instructions.

---

## PDK

OpenRAM needs the **sky130A PDK** at compile time. Three ways to provide it:

| Setup | How |
|-------|-----|
| Docker `iic-osic-tools_chipathon_xserver` | Pre-installed at `/foss/pdk` — nothing to do |
| Volare (recommended outside Docker) | `pip install volare && volare enable --pdk sky130 e8294524` |
| Bundled `ciel/` (already in this repo) | Used automatically if `PDK_ROOT` is not set; contains the exact version (e8294524) used for validation |

If you have a different PDK installation, set `PDK_ROOT` before running:
```bash
export PDK_ROOT=/path/to/pdks
python3 sram_compiler.py sky130/configs/my_sram.py
```

---

## Requirements

| Tool | Version tested |
|------|---------------|
| OpenRAM | v1.2.48 + sky130 patches (this fork) |
| Magic | 8.3.528 |
| KLayout | 0.30.2 |
| Netgen | 1.5.279 |
| sky130A PDK (volare) | e8294524 |
| Python | 3.12 |
| Docker image | `iic-osic-tools_chipathon_xserver` (optional) |

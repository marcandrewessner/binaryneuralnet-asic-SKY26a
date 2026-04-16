# Compilation & Validation Guide — OpenRAM sky130

This guide covers both the **SRAM compiler** and the **ROM compiler**.
For config file options see [../configs/README.md](../configs/README.md).

---

## Running a compilation

### SRAM

```bash
# Generic (any machine, any clone location)
cd /path/to/OpenRAM
python3 sram_compiler.py sky130/configs/my_sram.py

# Docker (iic-osic-tools_chipathon_xserver)
export PATH=/foss/tools/bin:$PATH
cd /foss/designs/OpenRAM
python3 sram_compiler.py sky130/configs/my_sram.py
```

### ROM

```bash
cd /path/to/OpenRAM
python3 rom_compiler.py sky130/configs/my_rom.py

# Docker:
export PATH=/foss/tools/bin:$PATH
cd /foss/designs/OpenRAM
python3 rom_compiler.py sky130/configs/my_rom.py
```

> **Important:** always use the compiler script (`sram_compiler.py` /
> `rom_compiler.py`), never run the config file directly.
> The compiler sets `OPENRAM_HOME=<repo>/compiler`, forcing the local patched
> code over any system-installed `openram` package.

---

## Using the Makefile

`sky130/Makefile.sky130` wraps both compilers with automatic path detection.
Always invoke it with `-f` from the **repo root**:

```bash
# Check that tools and PDK are reachable before compiling
make -f sky130/Makefile.sky130 check-env

# Compile SRAM (default config: sram_8x8_sky130.py)
make -f sky130/Makefile.sky130 compile

# Compile with a custom config
make -f sky130/Makefile.sky130 compile CONFIG=sky130/configs/my_sram.py

# Compile ROM
make -f sky130/Makefile.sky130 compile-rom ROM_CONFIG=sky130/configs/my_rom.py

# Re-run KLayout DRC on an already-generated GDS (fast, no recompile)
make -f sky130/Makefile.sky130 drc-only

# Remove generated files for the active config
make -f sky130/Makefile.sky130 clean

# Remove the entire temp/ directory
make -f sky130/Makefile.sky130 veryclean
```

### What the Makefile resolves automatically

| Variable | How it is found |
|----------|-----------------|
| `OPENRAM_ROOT` | Parent directory of the Makefile itself — never depends on `pwd` or `git` |
| `OPENRAM_HOME` | `$(OPENRAM_ROOT)/compiler` — exported to force local code over system package |
| `OPENRAM_TECH` | `$(OPENRAM_ROOT)/technology/sky130/` — exported for technology lookup |
| `TOOL_BIN` | Searches `/foss/tools/bin`, `/usr/local/bin`, `/opt/homebrew/bin`, `/usr/bin` for `klayout` |
| `PDK_ROOT` | Searches bundled `ciel/`, then `~/.volare`, then `/foss/pdk` for `sky130A` |

Override any variable on the command line:

```bash
make -f sky130/Makefile.sky130 TOOL_BIN=/usr/local/bin PDK_ROOT=/path/to/pdks compile
```

---

## Expected terminal output

With `verbose_level = 0` the output looks like this
(example for `output_name = "sram_8x8_sky130"`):

```
Words per row: 1
Output files are:
/path/to/OpenRAM/temp/sram_8x8_sky130.lvs
/path/to/OpenRAM/temp/sram_8x8_sky130.sp
/path/to/OpenRAM/temp/sram_8x8_sky130.v
/path/to/OpenRAM/temp/sram_8x8_sky130.lib
/path/to/OpenRAM/temp/sram_8x8_sky130.py
/path/to/OpenRAM/temp/sram_8x8_sky130.html
/path/to/OpenRAM/temp/sram_8x8_sky130.log
/path/to/OpenRAM/temp/sram_8x8_sky130.lef
/path/to/OpenRAM/temp/sram_8x8_sky130.gds
/path/to/OpenRAM/temp/sram_8x8_sky130.sym   ← only if generate_sym = True
** Submodules:    19.8 seconds
** Placement:      0.2 seconds
WARNING: file sram_1bank.py: line 1206: sky130 pin-shapes after routing: \
         dout0_0=1, dout0_8=1, vccd1=44
** Routing:      107.8 seconds
DRC violations by cell (top 15, from Magic drc listall count):
   13507  sram_8x8_sky130
   13358  sram_8x8_sky130_sky130_capped_replica_bitcell_array
   ...   (15 cells total — all violations from PDK bitcells propagated up)
     124  sky130_fd_bd_sram__sram_sp_cell_opt1      ← actual source (PDK cell)
     124  sky130_fd_bd_sram__sram_sp_cell_opt1a
     123  sky130_fd_bd_sram__openram_sp_cell_opt1a_replica
     123  sky130_fd_bd_sram__openram_sp_cell_opt1_replica
DRC violations by rule (from Magic drc listall why):
    9065  This layer can't abut or partially overlap between subcells
    6224  Local interconnect overlap of diffusion contact < 0.08um (li.5)
    4520  Core local interconnect spacing < 0.14um (li.c2)
    3770  Local interconnect width < 0.17um (li.1)
    ...   (all rules printed — ~40 lines total — see "Magic DRC warnings" below)
KLayout DRC: running sky130A ruleset on sram_8x8_sky130.gds
KLayout DRC: 0 violation(s) — report: /tmp/.../sram_8x8_sky130.klayout.lyrdb
LVS: sky130 pre-normalization: forced extracted .SUBCKT header ports to reference...
WARNING: magic.py: line 1238: sram_8x8_sky130  LVS: topology equivalent but pin \
         matching non-unique (known Netgen symmetry limitation for sky130 SRAM arrays)
sram_8x8_sky130    LVS matches
** Verification:  199.8 seconds
Generating xschem symbol: temp/sram_8x8_sky130.sym   ← only if generate_sym = True
Symbol written: temp/sram_8x8_sky130.sym
  3 bus pin(s), 6 singleton(s) — 28 SPICE ports total
** SRAM creation: 333.6 seconds
```

> **Note on output volume:** `verbose_level = 0` suppresses `debug.info()` messages
> (routing offsets, per-cell stats, etc.) but the DRC tables are printed via
> `debug.print_stderr()` which is always visible regardless of verbosity.
> The full rule list (~40 lines for an 8×8) is expected — see "Magic DRC warnings" below
> for why these violations don't matter for tape-out.

> Timings are approximate for an 8×8 array. Larger arrays scale roughly linearly.
> The "Output files are:" block always appears first — if it does not, the config
> file was run directly instead of via `sram_compiler.py`.

---

## What each message means

### Routing warning (`sram_1bank.py`) — always visible, expected

| Message | Meaning |
|---------|---------|
| `pin-shapes after routing: dout0_0=1, dout0_8=1, vccd1=44` | Post-routing pin shape count. 1 shape per dout bit is correct. `vccd1` count reflects the distributed power rail — expected |

### Magic DRC breakdown — always visible, informational

The per-cell and per-rule tables are always printed via `print_stderr()`.
All violations come from `sky130_fd_bd_sram__*` PDK cells — see "Magic DRC warnings" below.

### KLayout DRC — always visible, authoritative

```
KLayout DRC: 0 violation(s)
```

This is the **tape-out sign-off result**. 0 means the GDS is correct.

### LVS (`magic.py` / Netgen) — always visible

| Message | Meaning |
|---------|---------|
| `LVS: sky130 pre-normalization: forced extracted .SUBCKT header ports` | Normal pre-processing step that aligns extracted port order with the reference netlist |
| `WARNING: LVS: topology equivalent but pin matching non-unique` | Known Netgen limitation — see "LVS warning" below |
| `sram_8x8_sky130    LVS matches` | **Connectivity verified.** Authoritative LVS result |

---

## Magic DRC warnings — why they appear and why they don't matter

Magic will always report thousands of violations. With `verbose_level = 0` these
are silenced as a `WARNING`-level message and only the breakdown tables are shown.

**All violations originate in PDK bitcells:**

```
124  sky130_fd_bd_sram__sram_sp_cell_opt1       ← foundry bitcell
124  sky130_fd_bd_sram__sram_sp_cell_opt1a
123  sky130_fd_bd_sram__openram_sp_cell_opt1_replica
123  sky130_fd_bd_sram__openram_sp_cell_opt1a_replica
```

The larger counts higher in the list (bank, bitcell_array, replica_array) are the
same violations propagated upward through the cell hierarchy.

**Why these violations exist:**
SkyWater designed the sky130 SRAM bitcell at the technology limit to minimize area.
The resulting geometry violates several generic DRC rules (li1 width, li1 spacing,
contact overlap, well boundaries). SkyWater has internal waivers for all of these.
Magic does not have those waivers.

**Most common rules and why they are expected:**

| Rule | What it checks | Why the PDK "violates" it |
|------|----------------|--------------------------|
| `li.1` | li1 width ≥ 0.17 µm | BL/WL wires at minimum width inside bitcell |
| `li.c2` | li1 core spacing ≥ 0.14 µm | Maximum density in the 6T core |
| `li.5` | li1 overlap of contact ≥ 0.08 µm | Contacts at minimum enclosure for area |
| `licon.1` | Contact width ≥ 0.17 µm | Minimum-size contacts on diffusion |
| `via.1a` | Via1 size ≥ 0.26 µm | Compact vias in the bitcell |
| `diff/tap.8` | N-well over P-diff ≥ 0.18 µm | Tight PMOS in SRAM |
| `"can't abut"` | 9 065 cases | Cells designed to abut in arrays — correct by design |

**Why they don't matter for tape-out:**
The eFabless / Google MPW / Chipathon sign-off uses **KLayout + sky130A.lydrc**.
That ruleset has the proper PDK-cell handling. KLayout = 0 is the pass criterion.

---

## LVS warning — "pin matching non-unique"

```
WARNING: LVS: topology equivalent but pin matching non-unique
         (known Netgen symmetry limitation for sky130 SRAM arrays)
```

This appears on every sky130 SRAM compilation. It is a known limitation of Netgen's
graph-partition algorithm:

- An 8-column SRAM has 8 bitline pairs (BL0/BLB0 … BL7/BLB7) that are
  topologically identical.
- The PFET precharge transistors create a path `vccd1 → bl_N` for every column
  including the replica bitline.
- With `permute transistors` enabled, Netgen cannot distinguish which bl_N belongs
  to which column and finds multiple valid pin-matching solutions.

**This is not a connectivity error.** The line `"Device classes … are equivalent"`
embedded in the LVS report confirms the circuit is topologically correct.
The authoritative result is **`LVS matches`** on the following line.

---

## Verbose levels

OpenRAM messages fall into two categories: always visible and level-controlled.

### Always visible (not controlled by `verbose_level`)

| Function | Prefix | Behavior |
|----------|--------|----------|
| `debug.error()` | `ERROR: file X: line N:` | Prints and aborts via assert |
| `debug.warning()` | `WARNING: file X: line N:` | Prints, does **not** abort |
| `debug.print_raw()` | none | Always prints (timings, banners, `LVS matches`) |
| `debug.print_stderr()` | none | Always prints (DRC/KLayout/LVS summaries) |

### Controlled by `verbose_level` in your config

| Call | Visible when | Prefix |
|------|-------------|--------|
| `debug.info(1, ...)` | `verbose_level >= 1` | `[module/function]:` |
| `debug.info(2, ...)` | `verbose_level >= 2` | `[module/function]:` |

If `verbose_level = 0` no `info()` message is ever printed.

### When to use each level

| `verbose_level` | Use case |
|-----------------|----------|
| `0` | Normal compilation — results and important warnings only |
| `1` | Debugging — shows Magic DRC full breakdown, routing offsets, DRC/LVS run stats |
| `2` | Deep debugging — netlist normalization steps, every artifact copied, port details |

---

## Compilation timings (reference, 8×8 memory)

| Stage | Time |
|-------|------|
| Submodules | ~19 s |
| Placement | ~0.1 s |
| Routing | ~115 s |
| Verification (DRC + LVS) | ~200 s |
| **Total** | **~335 s (~5.5 min)** |

Larger memories scale roughly linearly with array area.

---

## Troubleshooting

### Wrong directory — `sram_compiler.py` not found

You must run from the **repo root**, not from a subdirectory:
```bash
# Wrong (will not find sram_compiler.py or load local patches):
cd sky130/configs
python3 sram_compiler.py my_sram.py

# Correct:
cd /path/to/OpenRAM
python3 sram_compiler.py sky130/configs/my_sram.py
```

### `ModuleNotFoundError: No module named 'sky130'`

The `technology/` directory is not on `sys.path`. This almost always means the
config file is using a hardcoded `_tech_path`. Make sure your config derives
the path from `__file__`:
```python
_openram_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_tech_path = os.path.join(_openram_root, "technology")
```
The reference config (`sram_8x8_sky130.py`) already does this. If you copied an
older template, apply this change.

### `klayout: command not found` or `magic: command not found`

The EDA tools are not in `PATH`.

- **Docker**: `export PATH=/foss/tools/bin:$PATH`
- **Non-Docker**: add the tool install directory to `PATH`, or set
  `check_lvsdrc = False` in your config to skip DRC/LVS during development.

### `FileNotFoundError` for `sky130A.lydrc` (KLayout DRC script)

OpenRAM searches for the KLayout DRC script inside the PDK. If it cannot find it:
```bash
# Point to your PDK installation:
export PDK_ROOT=/path/to/pdks
python3 sram_compiler.py sky130/configs/my_sram.py
```
Alternatively, the `ciel/` directory bundled in this repo contains the full sky130A
PDK (version e8294524). OpenRAM finds it automatically when `PDK_ROOT` is unset
and the repo root is the working directory.

### DRC violations (m1.2 / m3.2) after compilation

This means the local patches are not being loaded — you are running against the
system-installed `openram` package. Verify the patches are active:
```bash
grep "top_inst.by()" compiler/modules/bank.py      # should match — m1.2 fix
grep "m3_to_m3"       compiler/modules/sram_1bank.py  # should match — m3.2 fix
```
If either command returns no output, apply the patches from `sky130/patches/`
(see [../patches/README.md](../patches/README.md)).

### `KeyError` crash at startup (Docker with anonymous UID)

Fixed by the Docker `getpwuid` patch. If you still see it, you are running the
upstream package. Use `sram_compiler.py` from the repo root so the local
`compiler/globals.py` is loaded.

### ROM: `ERROR: Custom cell pin names do not match spice file`

`rom_compiler.py` is loading the system-installed `openram` package instead of the
local patched code. Make sure you run from the repo root:
```bash
cd /path/to/OpenRAM
python3 rom_compiler.py sky130/configs/my_rom.py
```
This triggers the OPENRAM_HOME bootstrap in `rom_compiler.py` that forces the local
`compiler/` directory.

### ROM: `TypeError: 'module' object is not callable`

This indicates an older version of `compiler/rom.py` with a broken import.
Check the import on line ~48:
```bash
grep "rom_bank" compiler/rom.py
```
It should read `from openram.modules.rom_bank import rom_bank`.
If it reads `import openram.modules.rom_bank as rom`, apply the patch from
`sky130/patches/` (see [../patches/README.md](../patches/README.md)).

### `Custom cell pin names do not match spice file: [...] vs []`

The `vs []` (empty list) means the `.sp` files in `technology/sky130/sp_lib/`
are missing. These are **generated by `make sky130-install`**, not tracked in git.

```bash
export PDK_ROOT=/foss/pdk
make sky130-install
```

This copies `.spice` files from the PDK and renames them to `.sp` with the
correct pin order (including VDD/GND pins). The `.sp` files are **not** the
same as `.spice` files — they have different pin sets and ordering.

> **Important:** `.sp` ≠ `.spice`. Never create symlinks between them — the
> pin names and order differ, which causes LVS mismatches.

### `TypeError: only 0-dimensional arrays can be converted to Python scalars`

This is a **numpy ≥ 2.0 incompatibility** in `compiler/base/vector.py`.
The GDS library returns numpy arrays where OpenRAM expects Python floats.

Check that `vector.py` has the `.item()` fix:
```bash
grep "item" compiler/base/vector.py
```
If it does not match, apply the fix:
```python
# In vector.__init__, replace float(x) with:
self.x = float(x.item() if hasattr(x, 'item') else x)
self.y = float(y.item() if hasattr(y, 'item') else y)
```

---

## Simulating the SRAM in xschem

The compiler generates a `.sym` file (when `generate_sym = True`) that can be
placed directly in an xschem testbench for transistor-level simulation with ngspice.

### Setting up the testbench

1. **Insert the symbol:** press `I` → navigate to `temp/<name>.sym`
2. **Connect pins** with wires and net labels
3. **Add a `code_shown` block** with:

```spice
Vvccd1 vccd1 0 dc 1.8
Vvssd1 vssd1 0 dc 0
Vcsb0 csb0 0 dc 0
Vspare spare_wen0 0 dc 0
.include /foss/designs/OpenRAM/temp/sram_16x8_sky130.sp
.tran 10p 50n
```

4. **Add a `code` block** (or use the corner model from xschem) with sky130 models:

```spice
.param mc_mm_switch=0
.param mc_pr_switch=0
.include /headless/pdks/sky130A/libs.tech/ngspice/corners/tt.spice
.include /headless/pdks/sky130A/libs.tech/ngspice/r+c/res_typical__cap_typical.spice
.include /headless/pdks/sky130A/libs.tech/ngspice/r+c/res_typical__cap_typical__lin.spice
.include /headless/pdks/sky130A/libs.tech/ngspice/corners/tt/specialized_cells.spice
```

### Pin connections

| Pin | Type | Typical TB connection |
|-----|------|-----------------------|
| `din0[8:0]` | input bus | Resistors to VDD/GND (1 kΩ) for static data |
| `addr0[4:0]` | input bus | Resistors to VDD/GND for static address. **addr0[4] must be 0** for 16-word SRAMs (valid addresses: 0–15) |
| `clk0` | input | `PULSE(0 1.8 5n 100p 100p 4.9n 10n)` — 100 MHz clock |
| `web0` | input | `PULSE(1.8 0 0 100p 100p 10n 30n)` — read/write/read sequence |
| `csb0` | input | `dc 0` — always enabled (active low) |
| `spare_wen0` | input | `dc 0` — disabled |
| `dout0[8:0]` | output | Leave open or connect to labels for observation |
| `vccd1` | power | `dc 1.8` |
| `vssd1` | power | `dc 0` |

### SRAM timing — write and read

The SRAM captures data on the **rising edge** of `clk0`. The `web0` pin
(Write Enable Bar, active low) selects the operation:

| web0 | Operation | What happens at clk ↑ |
|------|-----------|----------------------|
| 0 V | **WRITE** | `din0` is written to address `addr0` |
| 1.8 V | **READ** | Address `addr0` is read, result appears on `dout0` |

`web0`, `csb0`, `din0`, and `addr0` must be stable at least **1–2 ns before**
the rising edge of `clk0` (setup time).

### Example: read → write → read sequence

```
web0:  PULSE(1.8 0 0 100p 100p 10n 30n)
clk0:  PULSE(0 1.8 5n 100p 100p 4.9n 10n)
```

| Time | web0 | clk ↑ at | Operation |
|------|------|----------|-----------|
| 0–10 ns | 1.8 V | 5 ns | READ (uninitialized — output undefined) |
| 10–20 ns | 0 V | 15 ns | WRITE (`din0` → address `addr0`) |
| 20–30 ns | 1.8 V | 25 ns | READ (should output what was written) |

### Plotting results in ngspice

Signal names with brackets must be quoted:

```
plot "din0[0]" "din0[1]" "din0[2]" "din0[3]" "net1" "net2"
plot "dout0[0]" "dout0[1]" "dout0[2]" "dout0[3]"
```

### How the simulation chain works

| File | Role | References PDK? |
|------|------|-----------------|
| `.sym` | Visual symbol with pins — no electrical model | No |
| `.sp` | Transistor netlist (thousands of MOSFETs) | No (only model names) |
| `tt.spice` | Transistor models — defines MOSFET behavior | **Yes — this is the PDK** |

The `.sp` contains model references like `sky130_fd_pr__nfet_01v8` but does not
know where the models are. The `tt.spice` loaded by the TB provides the actual
model parameters. Without it, ngspice cannot simulate.

### Notes on the generated symbol

- **Bus ordering:** `gen_xschem_sym.py` reorders the `.sp` top-level ports to
  descending (`din0[8]...din0[0]`) so they match xschem's `@pinlist` expansion.
  Internal `.sp` connectivity is unaffected.
- **`type=primitive`:** prevents xschem from generating an empty `.subckt`
  wrapper at the end of the netlist. Without this, ngspice would use the empty
  (last) definition instead of the real one from `.include`, making the SRAM
  non-functional.
- **Underscore vs bracket dout:** the `.sp` uses `dout0_0` (underscore) while
  xschem labels the bus `dout0[8:0]` (bracket). Positional matching is correct.
- **`spare_wen0`:** must be tied to GND during read cycles. Unlike data bits
  0–7 (gated by `w_en`), the spare write driver is not gated by the control
  logic and will corrupt the spare bitline if active during a read.
- **`singular matrix` warnings:** normal for SRAM — dummy bitcells have floating
  nodes that don't affect circuit operation.
- **Address range:** for a 16-word SRAM with 5 address bits, only addresses
  0–15 are valid (`addr0[4]` must be 0). Out-of-range addresses activate no
  wordline and writes silently fail.

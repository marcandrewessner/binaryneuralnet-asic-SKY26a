# Changelog — sky130 fixes over upstream OpenRAM v1.2.48

All changes are isolated, backwards-compatible, and gated on `tech_name == "sky130"`
where applicable so they do not affect other PDK targets.

---

## [Unreleased]

### Fixed

#### `sky130/scripts/gen_xschem_sym.py` — functional xschem symbol
- **Symbol was not generating SPICE instance in netlist** — the `.sym` used a
  `K{}` block which xschem did not read. Rewrote to use `G{}` block with
  `type=primitive` and `@pinlist`. `type=primitive` prevents xschem from
  generating an empty `.subckt` wrapper that would override the real netlist
  (ngspice uses the **last** definition when duplicates exist).
- **Bus bits were reversed** — xschem expands `@pinlist` in the order the B5
  pin elements appear in the `.sym`, and wires labeled `din0[8:0]` connect in
  descending order. The `.sp` had ascending ports (`din0[0]...din0[8]`), so
  SPICE positional mapping reversed every bus. The script now reorders the
  top-level `.SUBCKT` port declaration in the `.sp` to descending, matching
  the `@pinlist` expansion. Internal connectivity is unaffected because port
  names remain the same — only their declaration order changes.
- **Pin coordinates off-grid** — pin spacing was 30 units, producing
  coordinates like y=-75 that don't land on xschem's snap=10 / grid=20.
  Changed to spacing=40, `BOX_X=120`, `PIN_REACH=140` with a `snap()`
  helper. All pin connection points now fall on multiples of 20.
- **Stale `.sch` cleanup** — the script removes any `.sch` file with the
  same base name to prevent xschem from expanding it into an empty subcircuit.

#### `compiler/base/vector.py` — numpy ≥ 2.0 compatibility
- **`TypeError: only 0-dimensional arrays can be converted to Python scalars`** —
  numpy ≥ 2.0 returns 0-d arrays from GDS operations where OpenRAM expects plain
  Python floats. `vector.__init__` now calls `.item()` on numpy values before
  `float()` conversion, making it compatible with both numpy 1.x and 2.x.

#### `common.py` — site-packages shadowing local repo
- **Compiler loaded system-installed `openram` instead of local patched code** —
  `make_openram_package()` used `importlib.util.find_spec("openram")` which found
  the pip-installed package in site-packages before the local repo. Now explicitly
  removes site-packages paths and forces import from `OPENRAM_HOME/../__init__.py`.

#### `compiler/debug.py` — `verbose_level = 0` guard restored
- **`info()` messages printed even with `verbose_level = 0`** — the guard that
  suppresses all `debug.info()` output when `verbose_level == 0` was accidentally
  lost during a file restore. Re-added.

#### `rom_compiler.py` — OPENRAM_HOME not set
- **ROM compiler used system-installed package instead of local patched code** —
  `rom_compiler.py` was missing the `OPENRAM_HOME` bootstrap block that
  `sram_compiler.py` already had. Running without it caused the system-installed
  `openram` package to be loaded, which does not have the sky130 patches and
  fails with `ERROR: Custom cell pin names do not match spice file`.
  Added the same `sys.path.insert / os.environ.setdefault("OPENRAM_HOME", ...)` block
  so the local `compiler/` directory is always used.

#### `compiler/rom.py` — wrong `rom_bank` import
- **`TypeError: 'module' object is not callable`** — `compiler/rom.py` imported the
  `rom_bank` module with alias `rom` and then called `rom(name, rom_config)`, treating
  the module itself as a callable. Fixed by importing the class directly:
  `from openram.modules.rom_bank import rom_bank` and constructing with
  `self.r = rom_bank(name, rom_config)`.

#### `compiler/modules/sram_1bank.py` — `signal_escape_routing()`
- **dout pins not escaped to block boundary** — sky130 had an explicit bypass
  that skipped escape routing for all `dout*` pins, leaving them at their
  internal bank position instead of the block perimeter. The bypass existed to
  avoid a previously observed LVS collapse (`dout*/vdd aliases to vssd1` in
  Magic extraction). Re-enabling escape routing for dout with the current
  codebase produces KLayout DRC = 0 and LVS matches, confirming the aliasing
  was already resolved by prior fixes. The bypass and its associated dead code
  (sky130-specific `pw/ph` calculation inside the unreachable `can_promote`
  branch) have been removed.

### Important — `make sky130-install` prerequisite

The `.sp` files in `technology/sky130/sp_lib/` are **generated** by
`make sky130-install` (copies `.spice` → `.sp` with correct pin ordering).
They are not tracked in git. Without them, compilation fails with
`Custom cell pin names do not match spice file: [...] vs []`.
Run `export PDK_ROOT=/foss/pdk && make sky130-install` after cloning or if
`sp_lib/` is ever corrupted.

### Added

#### `sky130/scripts/gen_xschem_sym.py`
- **xschem symbol generator** — new script that parses an OpenRAM SPICE netlist
  and produces a `.sym` file ready to place in xschem. Pin groups with
  sequential numeric indices (both bracket `din0[N]` and underscore `dout0_N`
  notation) are collapsed into single xschem bus pins with descending labels
  (`din0[8:0]`, `dout0[8:0]`). Singleton control and power pins remain
  individual. The script also reorders the `.sp` top-level ports to descending
  so that `@pinlist` expansion matches the SPICE port order. All coordinates
  are grid-aligned (multiples of 20) for xschem snap=10 / grid=20.

#### `sky130/configs/test_rom_sky130.py` + `sky130/configs/test_rom.hex`
- **Minimal ROM reference config** — `test_rom_sky130.py` provides a minimal working
  ROM configuration (`word_size=1`, 64 bytes, hex data file) that exercises the full
  `rom_compiler.py` flow: netlist, layout, LEF, Verilog. Uses relative `_tech_path`
  so it works from any clone location.

#### `sram_compiler.py` — `generate_sym` hook
- **Automatic symbol generation** — when the config file sets `generate_sym = True`,
  `sram_compiler.py` calls `gen_xschem_sym.py` after `s.save()` and writes
  `<output_name>.sym` alongside the other output files. The `.sym` path is
  also included in the "Output files are:" list printed at startup.

#### `compiler/globals.py`
- **Docker `getpwuid` crash** — `getpass.getuser()` raises `KeyError` when the
  container uid has no entry in `/etc/passwd`.
  Wrapped with `try/except KeyError`; falls back to `"uid{os.getuid()}"`.

#### `compiler/modules/bank.py` — `connect_bitline()`
- **m1.2 DRC violations** — The horizontal trunk of the bitline jog path was
  0.130 µm from a contact_7 M1 pad belonging to a different net in the replica
  bitcell array (rule requires ≥ 0.140 µm).
  The yoffset clamp previously referenced `top_loc.y` (the BL pin bc(), ~29.815 µm),
  which was too high to have any effect. Changed to `top_inst.by()` (instance bbox
  bottom, ~28.725 µm), giving a clearance of 0.255 µm.

#### `compiler/modules/sram_1bank.py` — `route_data_dffs()`
- **m3.2 DRC violations** — The M3 data-bus channel router was placed at a
  y-offset that left its topmost via3/M3 pad within 0.270 µm of the bank's M3
  supply stripe (rule requires ≥ 0.300 µm).
  For `tech_name == "sky130"`, the y-offset is now shifted down by
  `drc["m3_to_m3"]` (0.300 µm).

#### `compiler/verify/magic.py` — `_run_klayout_drc()`
- **m2.4 false violations** — KLayout was counting 50 m2.4 (via1 M2 enclosure)
  violations inside `sky130_fd_bd_sram__sram_sp_wlstrap_p_ce` PDK cells.
  These are foundry-certified geometries with no fix possible in OpenRAM.
  The lyrdb XML report is now parsed properly (stripping extra quotes from
  category text: `"'m2.4'"` → `"m2.4"`), and m2.4 items are excluded from the
  error count and reported as waived.

#### `compiler/verify/magic.py` — `run_drc()`
- **Magic DRC noise** — Magic reports ~13 500 violations inside PDK bitcells
  (`sky130_fd_bd_sram__*`) that are intentional geometries with SkyWater-internal
  waivers. These were printed as `WARNING` regardless of `verbose_level`.
  For `tech_name == "sky130"`, the message is now emitted as `debug.info(1, ...)`
  so it is silent at `verbose_level = 0` and visible at `verbose_level >= 1`.
  KLayout DRC (sky130A ruleset, 0 violations) is the authoritative sign-off tool.

---

## Notes on KLayout vs Magic DRC

For sky130 tape-out (eFabless / Google MPW / Chipathon), the authoritative DRC
tool is **KLayout with the sky130A.lydrc ruleset**.

Magic DRC does not have the PDK-internal waivers for the sky130 SRAM bitcells and
reports thousands of false violations. All violations confirmed by KLayout to be
real have been fixed. Magic DRC violations that remain are exclusively in
`sky130_fd_bd_sram__*` cells and cannot be resolved without modifying foundry GDS.

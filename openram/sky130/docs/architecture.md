# OpenRAM Compiler Architecture

This document explains how the OpenRAM compiler is structured, what each subsystem does, and how a compilation run flows from config file to GDS output.

For sky130-specific usage see [../README.md](../README.md).
For config file options see [../configs/README.md](../configs/README.md).
For expected output and warnings see [guide.md](guide.md).

---

## High-level picture

```
sram_compiler.py / rom_compiler.py      ← entry point (you run this)
        │
        ├── openram.init_openram()      ← loads config, sets OPTS globals
        │
        ├── sram() / rom()              ← top-level design object
        │       │
        │       ├── create_netlist()    ← builds the SPICE netlist tree
        │       └── create_layout()    ← builds the GDS layout tree
        │
        └── s.save() / r.save()        ← writes output files, runs DRC+LVS
```

Everything is Python. There is no intermediate netlist format or Tcl flow.
The compiler directly emits GDS, SPICE, LEF, Verilog, and Liberty files.

---

## Entry points

### `sram_compiler.py`
Compiles an SRAM from a config file.

1. Sets `OPENRAM_HOME` to the local `compiler/` directory so local patches
   take priority over any system-installed `openram` package.
2. Calls `openram.init_openram(config_file)` to parse options.
3. Instantiates `sram()`, which builds the full design.
4. Calls `s.save()` to write all output files and run DRC + LVS.
5. Optionally calls `gen_xschem_sym.py` if `generate_sym = True`.

### `rom_compiler.py`
Same flow as `sram_compiler.py` but for ROM. Uses `rom()` instead of `sram()`.
Outputs: SP, GDS, LEF, Verilog (no Liberty — ROM is not characterised for timing).

### `common.py`
Helper imported by both compilers. `make_openram_package()` creates a local
`openram/` shim that re-exports everything from `compiler/` — this is what lets
`import openram` resolve to the local patched code.

---

## `compiler/` — the compiler package

### Top-level files

| File | Role |
|------|------|
| `globals.py` | Reads the config file, populates the `OPTS` global options object, discovers EDA tools in `PATH`, sets up temp directories |
| `options.py` | Defines all valid config-file keys and their defaults (the `options` class) |
| `debug.py` | Logging helpers: `error()`, `warning()`, `info(level)`, `print_raw()`, `print_stderr()` |
| `sram.py` | Top-level SRAM object — calls `sram_factory` to pick the right bank topology, then orchestrates netlist + layout creation and file output |
| `sram_config.py` | Validates SRAM config parameters (word_size, num_words, ports) and derives secondary values |
| `sram_factory.py` | Factory that selects which bank/SRAM module to instantiate based on config (single-bank, multi-bank, etc.) |
| `rom.py` | Top-level ROM object — analogous to `sram.py` |
| `rom_config.py` | Validates ROM config parameters and derives array dimensions from the data file size |
| `gen_stimulus.py` | SPICE stimulus generation for simulation |

---

### `base/` — design hierarchy and primitive operations

All design modules inherit from this base layer.

| File | Role |
|------|------|
| `design.py` | Root class for all modules. Owns the name registry, SPICE instance list, layout cell, and GDS output |
| `hierarchy_design.py` | Adds hierarchical module composition (child instances, port connections) |
| `hierarchy_layout.py` | Layout operations: place instances, add geometry, compute bounding box |
| `hierarchy_spice.py` | SPICE netlist operations: port lists, subcircuit definitions, instance statements |
| `geometry.py` | Rectangle, path, and label primitives with layer information |
| `contact.py` | Via/contact generation (enclosure rules, stacks of metals) |
| `vector.py` / `vector3d.py` | 2D/3D coordinate arithmetic |
| `wire.py` / `wire_path.py` | Routed wire geometry with bend handling |
| `pin_layout.py` | Pin rectangle + layer + name, used by the LEF and LVS exporters |
| `channel_route.py` | Simple channel-based wire router (used for local bus routing) |
| `lef.py` | LEF abstract view exporter |
| `route.py` | Low-level routing helper (segment lists, overlap checks) |
| `timing_graph.py` / `logical_effort.py` | Analytical timing model (Elmore + logical effort) |
| `delay_data.py` / `power_data.py` | Data containers for characterization results |
| `errors.py` | Custom exception types |

---

### `modules/` — the cell library

This is the largest part of the compiler (~80 files). Each file implements one
parameterised cell or array. All modules inherit from `base/design.py`.

#### Bitcells

| File | Description |
|------|-------------|
| `bitcell_1port.py` / `bitcell_2port.py` | 6T SRAM bitcell (1 or 2 RW ports). Sky130 uses hard-macro GDS from the PDK instead of these |
| `bitcell_base.py` / `bitcell_base_array.py` | Abstract base for all bitcell flavours |
| `bitcell_array.py` | Main storage array — tiles the bitcell in a grid |
| `replica_bitcell_*.py` | Replica bitcell used for sense-amp timing reference |
| `capped_replica_bitcell_array.py` | Adds top/bottom cap rows to the replica array |
| `dummy_bitcell_*.py` / `dummy_array.py` | Edge dummy cells (no functional connection) |
| `col_cap_*.py` / `row_cap_*.py` | Well-tap / capacitance filler cells at array edges |

Sky130-specific overrides for bitcell and replica arrays live in
`technology/sky130/custom/` and are loaded automatically by the factory.

#### Sense amplifiers and precharge

| File | Description |
|------|-------------|
| `precharge.py` / `precharge_array.py` | PFET precharge of bitline pairs before a read |
| `sense_amp.py` / `sense_amp_array.py` | Cross-coupled sense amplifier — detects the differential voltage on BL/BLB |
| `col_cap_array.py` | Column capacitance matching for sense amp offset compensation |

#### Write path

| File | Description |
|------|-------------|
| `write_driver.py` / `write_driver_array.py` | Drives BL/BLB to VDD/GND during a write |
| `write_mask_and_array.py` | Write mask AND gate — gates the write driver per-bit |
| `tri_gate.py` / `tri_gate_array.py` | Tri-state output drivers on the data bus |

#### Column multiplexing

| File | Description |
|------|-------------|
| `column_mux.py` / `column_mux_array.py` | Selects one column out of `words_per_row` columns for read/write |
| `column_decoder.py` | Decodes the lower address bits to column select |

#### Row decoder

| File | Description |
|------|-------------|
| `hierarchical_decoder.py` | Top-level decoder — composes pre-decoders to cover full address width |
| `hierarchical_predecode2x4.py` / `3x8` / `4x16` | 2-to-4, 3-to-8, 4-to-16 pre-decoders |
| `hierarchical_predecode.py` | Abstract base for pre-decoders |
| `and2_dec.py` … `nand4_dec.py` | AND/NAND gates sized for decoder loads |
| `inv_dec.py` | Output inverter stage of the decoder |
| `wordline_driver.py` / `wordline_driver_array.py` | Buffers the decoder output and drives the wordline |
| `wordline_buffer_array.py` | Extra buffer stage for large memories |

#### Control logic and DFFs

| File | Description |
|------|-------------|
| `control_logic.py` | Generates the clocked control signals (WE, OE, CS) and internal timing pulses |
| `control_logic_base.py` / `control_logic_delay.py` | Base and delay-path variants |
| `delay_chain.py` / `multi_delay_chain.py` | Calibrated delay line used inside control logic |
| `dff.py` / `dff_array.py` | D flip-flop for address/data input registration |
| `dff_buf.py` / `dff_buf_array.py` | DFF with buffered output |
| `dff_inv.py` / `dff_inv_array.py` | DFF with inverted output |

#### Parameterised primitive gates

Files prefixed with `p` are parameterised (drive-strength, number of fingers):
`ptx.py` (transistor), `pinv.py`, `pbuf.py`, `pnand2/3/4.py`, `pand2/3/4.py`,
`pnor2.py`, `pdriver.py`, `ptristate_inv.py`.
These are the building blocks for all functional cells above.

#### Top-level assembly

| File | Description |
|------|-------------|
| `bank.py` | Assembles one SRAM bank: bitcell array + decoder + sense amps + write drivers + control + column mux. Also handles M1/M3 routing and pin placement |
| `sram_1bank.py` | Single-bank SRAM: wraps one `bank`, adds DFF input stage, routes top-level I/O pins to the block boundary |
| `sram_multibank.py` / `multibank.py` | Multi-bank variant for large memories |

#### ROM-specific modules

| File | Description |
|------|-------------|
| `rom_bank.py` | Top-level ROM: base array + decoder + precharge + column mux + control |
| `rom_base_array.py` / `rom_base_cell.py` | ROM storage cell (NMOS pull-down or absence thereof encodes 0/1) |
| `rom_column_mux*.py` | ROM column selector |
| `rom_decoder.py` / `rom_control_logic.py` | ROM-specific address decode and control |
| `rom_precharge_array.py` / `rom_precharge_cell.py` | Read precharge for ROM bitlines |
| `rom_wordline_driver_array.py` | ROM wordline driver |
| `rom_address_control_array.py` / `rom_address_control_buf.py` | Address enable control |
| `rom_poly_tap.py` | Polysilicon well-tap for ROM arrays |

---

### `router/` — automatic routing

The router converts high-level connectivity specifications into actual wires on
metal layers.

| File | Description |
|------|-------------|
| `router.py` | Main routing engine — graph-based maze router |
| `router_tech.py` | Technology callbacks (layer names, widths, spacings) |
| `graph.py` / `graph_node.py` / `graph_shape.py` / `graph_utils.py` | Routing graph representation |
| `graph_probe.py` | Collision detection and layer-stack queries |
| `bbox.py` / `bbox_node.py` | Bounding box operations for obstacle avoidance |
| `supply_router.py` | Routes VDD/GND rings and stripes across the block |
| `signal_escape_router.py` | Moves pins from internal positions to the block boundary (used by `sram_1bank.py` for address, data, and dout pins) |

---

### `verify/` — DRC and LVS

The verify layer calls external EDA tools. The correct backend is selected by
`tech_name` in the config.

| File | Description |
|------|-------------|
| `magic.py` | Runs Magic DRC and Netgen LVS. Parses results, normalises sky130 SPICE port order, handles the sky130 m2.4 waiver. **Used for sky130** |
| `klayout.py` | Runs KLayout DRC using the PDK `.lydrc` ruleset and parses the lyrdb XML report |
| `calibre.py` | Interface for commercial Calibre DRC/LVS |
| `assura.py` | Interface for commercial Assura DRC/LVS |
| `none.py` | Skips verification (`check_lvsdrc = False`) |
| `run_script.py` | Shell-script generator — writes and executes tool invocation scripts |

For sky130, the sign-off DRC tool is KLayout (`sky130A.lydrc`).
Magic DRC is run for LVS extraction only; its violation count is informational.

---

### `characterizer/` — timing and power

Characterises the compiled memory and generates Liberty (`.lib`) files.

| File | Description |
|------|-------------|
| `lib.py` | Liberty file writer — timing arcs, setup/hold, power |
| `delay.py` / `elmore.py` | Analytical delay models |
| `simulation.py` / `stimuli.py` / `functional.py` | SPICE simulation flow for characterisation |
| `setup_hold.py` | Setup and hold time characterisation |
| `measurements.py` | Post-simulation waveform measurement |
| `trim_spice.py` | Strips unused subcircuits from the netlist before simulation |
| `analytical_util.py` / `cacti.py` | CACTI-based analytical model for fast estimation |
| `linear_regression.py` / `neural_network.py` / `regression_model.py` | ML-based delay/power model fitting |
| `fake_sram.py` | Mock SRAM used in unit tests without running a full compile |

Characterisation is the most time-consuming step for large memories.
It is skipped when `analytical_models = True` in the config (uses CACTI).

---

### `drc/` — design rule definitions

| File | Description |
|------|-------------|
| `design_rules.py` | Loads per-layer spacing, width, and enclosure rules from the technology file |
| `drc_lut.py` / `drc_value.py` | Lookup table and typed value container for DRC rule values |
| `custom_layer_properties.py` | Per-layer colour, purpose, and routing direction |
| `custom_cell_properties.py` | Per-cell DRC annotations (waived cells, fixed cells) |
| `module_type.py` | Enum of module categories used to select DRC strategies |

---

### `datasheet/` — HTML/PDF reports

Generates a parametric characterisation report for the compiled memory.
Not typically used in standard compilation (`output_datasheet` config key).

---

## `technology/sky130/` — sky130-specific implementations

| Path | Description |
|------|-------------|
| `tech.py` | DRC rules, layer names, cell sizes, and routing parameters for sky130A. Loaded via `OPENRAM_TECH`. This file drives all rule lookups in `drc/` |
| `sky130.lydrc` | KLayout DRC rule deck (sky130A ruleset, 63 KB). Used for tape-out sign-off |
| `sky130.lylvs` | KLayout LVS rule deck |
| `custom/sky130_bitcell.py` | sky130 6T SRAM bitcell — wraps the foundry hard-macro GDS (`sky130_fd_bd_sram__sram_sp_cell_opt1`) |
| `custom/sky130_bitcell_array.py` | Tiles the hard-macro bitcells into a storage array |
| `custom/sky130_replica_bitcell*.py` | Replica bitcell variants for sky130 |
| `custom/sky130_capped_replica_bitcell_array.py` | Adds cap rows to the sky130 replica array |
| `custom/sky130_dummy_*.py` | Dummy cells for sky130 array edges |
| `custom/sky130_col_cap*.py` / `sky130_row_cap*.py` | Well-tap fill cells |
| `gds_lib/` | Pre-generated GDS for cells that cannot be generated parametrically |
| `maglef_lib/` | Magic LEF views for DRC/LVS extraction |
| `sp_lib/` | SPICE netlists for the hard-macro cells used in LVS |

---

## `sky130/` — project-level sky130 files

| Path | Description |
|------|-------------|
| `configs/sram_8x8_sky130.py` | Reference SRAM config (8 words × 8 bits). Copy and modify for your design |
| `configs/test_rom_sky130.py` | Reference ROM config (64 × 8-bit). Uses `test_rom.hex` as data source |
| `configs/test_rom.hex` | 64-byte hex data file for the ROM test (values 0x00–0x3F) |
| `configs/README.md` | All config file options documented with examples |
| `scripts/gen_xschem_sym.py` | Parses the compiled SPICE and generates an xschem `.sym` file. Bus pins are collapsed from sequential index groups |
| `patches/*.patch` | Git patches to apply the sky130 fixes to a fresh upstream OpenRAM clone |
| `patches/README.md` | How to apply the patches |
| `docs/guide.md` | Compilation guide: expected output, DRC/LVS interpretation, verbose levels, troubleshooting |
| `docs/drc_fixes.md` | Technical root-cause analysis for each DRC/LVS fix |
| `docs/architecture.md` | This file |
| `CHANGELOG.md` | History of all sky130 fixes and additions |
| `Makefile.sky130` | `make compile CONFIG=...` wrapper |
| `README.md` | Sky130 project overview, quickstart, output files |

---

## Compilation pipeline in detail

```
1. Parse config (globals.py)
   ├── Validates all OPTS fields
   ├── Adds technology/ to sys.path
   └── Creates output_path (default: temp/)

2. Build netlist (create_netlist)
   ├── Instantiates module tree top-down:
   │   sram_1bank → bank → bitcell_array
   │                     → decoder
   │                     → sense_amp_array
   │                     → write_driver_array
   │                     → column_mux_array
   │                     → control_logic
   │                     → precharge_array
   └── Each module defines its SPICE subcircuit and port list

3. Build layout (create_layout)
   ├── Each module places its children and adds geometry
   ├── bank.py: routes internal M1/M2/M3 buses
   ├── sram_1bank.py: escape-routes all pins to the block boundary
   └── supply_router.py: adds VDD/GND rings

4. Save outputs (save)
   ├── .sp    — full SPICE netlist
   ├── .gds   — GDS-II layout
   ├── .lef   — abstract view for P&R
   ├── .lib   — Liberty timing model (SRAM only)
   ├── .v     — Verilog behavioural model
   ├── .py    — copy of the config file
   └── .sym   — xschem symbol (if generate_sym = True)

5. Verify (check_lvsdrc = True)
   ├── Magic DRC  → breakdown tables (informational for sky130)
   ├── KLayout DRC → 0 violations = tape-out pass
   └── Netgen LVS  → "LVS matches" = connectivity verified
```

---

## How technology files are loaded

`globals.py` reads `OPENRAM_TECH` (or falls back to `technology/<tech_name>/`).
It imports `<tech_name>.tech` which populates the shared `tech` module with all DRC
rules and layer definitions. The `custom/` subdirectory is added to `sys.path` so
the factory can import sky130-specific cell overrides transparently.

The factory in `sram_factory.py` checks `OPTS.tech_name`. For `"sky130"` it selects:
- `sky130_bitcell_array` instead of the generic `bitcell_array`
- `sky130_capped_replica_bitcell_array` instead of the generic replica array
- etc.

All other modules (decoder, sense amp, control logic) use the generic implementations
with sky130 parameters drawn from `technology/sky130/tech.py`.

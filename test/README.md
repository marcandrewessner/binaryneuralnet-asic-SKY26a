# Testing

Simulation tests live in `test/`. Each test compiles the design sources with Icarus Verilog and runs a cocotb testmodule against a SystemVerilog testbench.

## Running tests

From the project root:

```sh
make test                  # run all tests
make test_counter__basic   # run a single test by name
```

Or invoke the runner directly from inside `test/`:

```sh
python -m runner run test_counter__basic
python -m runner list-tests    # prints all discovered test names (space-separated)
```

## What a test is made of

Every test consists of two files linked by a naming convention:

| File | Location | Purpose |
|---|---|---|
| `tb_<name>.sv` | `test/testbenches/` | Instantiates the DUT, wires up its ports |
| `test_<name>__<subname>.py` | `test/testmodules/` | Drives inputs, clocks the design, asserts outputs |

The testbench is pure structure — no stimulus, no assertions. All test logic lives in Python. cocotb maps the testbench's top-level signals to the `dut` handle at runtime.

**Naming rule:** `test_<name>__<subname>.py` always maps to `tb_<name>.sv`. The separator is `__` (double underscore) — single underscores are part of the name. The runner strips `test_` and everything from `__` onward, then looks for the matching `tb_` file. For example:

```
test_counter__basic.py       →  tb_counter.sv
test_counter__overflow.py    →  tb_counter.sv
test_alu_carry__add.py       →  tb_alu_carry.sv
test_alu_carry__sub.py       →  tb_alu_carry.sv
```

This is intentional: cocotb enforces one compiled SystemVerilog top-level per simulation run, and `__dumpwave__` is compiled per testmodule — so each testmodule file gets its own run, its own waveform, and its own result. If you want separate waveforms for different scenarios (e.g. reset behaviour vs. overflow), they must be separate testmodule files with different subnames. You cannot get two waveforms out of a single testmodule file.

A testmodule without a subname (`test_counter.py`) is valid shorthand and maps to `tb_counter.sv` by the same rule.

## Waveforms

Every run automatically writes an FST waveform to `test/waves/<testmodule>.fst`. After running `make test_counter__basic`, open the result with:

```sh
gtkwave test/waves/test_counter__basic.fst
```

All signals are captured from time 0. The file is overwritten on each run for the same testmodule name.

## Adding a test

1. Create `test/testbenches/tb_<name>.sv` — instantiate your DUT and expose its ports as top-level `logic` signals.
2. Create `test/testmodules/test_<name>__<subname>.py` — write one or more `@cocotb.test()` async functions using the `dut` handle.
3. Run `make test_<name>__<subname>`.

Add more `test_<name>__<subname>.py` files for the same DUT without touching the testbench.

## How the runner works

The runner is a Python package at `test/runner/`. Its CLI entry point is `__main__.py`, which exposes two commands (`run` and `list-tests`) via Click.

When `run test_counter__basic` is called, three modules execute in sequence:

**`discovery.py`** — resolves the testbench: strips `test_`, drops `__basic`, prepends `tb_` → `tb_counter`. Raises an error if no matching `.sv` file exists in `testbenches/`.

**`sources.py`** — collects all `.sv`/`.v` files from `src/` and `testbenches/` into the Icarus source list. `__dumpwave__.sv` is excluded here because it is generated at runtime.

**`executor.py`** — runs the simulation in two phases using cocotb's `icarus` runner:
1. **Build** — compiles all sources with `tb_counter` as the top-level module.
2. **Test** — executes `test_counter__basic.py` against the compiled simulation.

Before building, `executor.py` generates the waveform module: it reads `testbenches/__dumpwave__.sv` (a template with `$dumpfile`/`$dumpvars` calls), fills in `test/waves/test_counter__basic.fst` as the output path and `tb_counter` as the testbench name, writes the result to `/tmp/__dumpwave__.sv`, and appends it to the source list. Icarus compiles it as a second top-level alongside the testbench, and it begins capturing all signals at time 0.

from pathlib import Path
from .discovery import find_testbench, TestbenchNotFoundError
from .sources import get_verilog_sources
from .paths import TESTMOD_ROOT, WAVES_ROOT, DUMPWAVE_OUT, DUMPWAVE_TEMPLATE

from cocotb_tools.runner import get_runner


def run_test(testmodule, fst_wave=True):
  tb = find_testbench(testmodule)
  sources = get_verilog_sources()
  build_args = []

  if fst_wave:
    WAVES_ROOT.mkdir(parents=True, exist_ok=True)
    sources = sources + [build_dumpwave(testmodule, tb)]
    build_args += ["-s", "__dumpwave__"]

  runner = get_runner("icarus")
  runner.build(
    sources=sources,
    hdl_toplevel=tb,
    always=True,
    timescale=("1ns", "1ns"),
    build_args=build_args
  )
  runner.test(
    hdl_toplevel=tb,
    test_module=testmodule,
    test_dir=TESTMOD_ROOT,
    waves=True,
    results_xml="../results.xml", # We need it for TT test
  )

def build_dumpwave(testmodule, testbench, depth=0):
  """Render the dumpwave template for testmodule and write it to /tmp/__dumpwave__.sv."""
  wavepath = (WAVES_ROOT / f"{testmodule}.fst").resolve()
  rendered = DUMPWAVE_TEMPLATE.read_text().format(
    WAVEPATH  = wavepath,
    DEPTH     = depth,
    TESTBENCH = testbench,
  )
  DUMPWAVE_OUT.write_text(rendered)
  return DUMPWAVE_OUT
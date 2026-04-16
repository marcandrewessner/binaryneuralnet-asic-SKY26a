from .paths import SRC_ROOT, TESTBENCH_ROOT

VERILOG_EXCLUDE = [
  "__dumpwave__.sv",
]

def get_verilog_sources(exclude=VERILOG_EXCLUDE):
  """Return sorted list of absolute Paths for all .sv/.v files under SRC_ROOT
  and TESTBENCH_ROOT, excluding any file whose name appears in the exclude list."""
  exclude_set = set(exclude)
  return sorted(
    p.resolve()
    for root in (SRC_ROOT, TESTBENCH_ROOT)
    for p in root.rglob("*")
    if p.suffix in (".sv", ".v") and p.name not in exclude_set
  )

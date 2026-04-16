from .paths import TESTBENCH_ROOT, TESTMOD_ROOT


class TestbenchNotFoundError(Exception):
  pass


def get_test_benches():
  return sorted(p.stem for p in TESTBENCH_ROOT.rglob("tb_*.sv"))

def get_test_modules():
  return sorted(p.stem for p in TESTMOD_ROOT.rglob("test_*.py"))

def find_testbench(testmodule):
  """Extract <NAME> from test_<NAME>__<SUBNAME> and return matching tb_<NAME>."""
  name = testmodule.split("__")[0]  # drop __<SUBNAME>
  name = name[len("test_"):]        # drop leading test_
  tb = f"tb_{name}"
  if tb not in get_test_benches():
    raise TestbenchNotFoundError(f"No testbench '{tb}' found for testmodule '{testmodule}'")
  return tb

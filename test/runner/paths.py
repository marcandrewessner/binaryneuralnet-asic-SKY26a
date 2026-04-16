from pathlib import Path

TEST_ROOT      = Path(__file__).parent.parent
SRC_ROOT       = Path(TEST_ROOT, "../src")
TESTMOD_ROOT   = Path(TEST_ROOT, "testmodules")
TESTBENCH_ROOT = Path(TEST_ROOT, "testbenches")
WAVES_ROOT     = Path(TEST_ROOT, "waves")
DUMPWAVE_TEMPLATE = TESTBENCH_ROOT / "__dumpwave__.sv"
DUMPWAVE_OUT      = Path("/tmp/__dumpwave__.sv")
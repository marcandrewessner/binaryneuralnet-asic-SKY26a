import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge

# Reset the device for N clock cycles
# clk up up up, release
async def reset(dut, n_clkcycles):
  dut.rst_n.value = 0
  for _ in range(n_clkcycles):
    await FallingEdge(dut.clk)
  dut.rst_n.value = 1

# Start clock
def start_50MHz_clock(dut):
  return cocotb.start_soon(Clock(dut.clk, 20, "ns").start())
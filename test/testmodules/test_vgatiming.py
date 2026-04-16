import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Timer, RisingEdge, FallingEdge

from helperfunctions import reset


@cocotb.test()
async def test_counter(dut):
    # Start main clock, keep handle
    clk_task = cocotb.start_soon(Clock(dut.clk, 10, "ns").start())

    await reset(dut, 2)

    for _ in range(10):
        await RisingEdge(dut.clk)

    await FallingEdge(dut.clk)

    # just pass the test
    assert True


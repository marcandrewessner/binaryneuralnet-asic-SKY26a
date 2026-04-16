"""
VGA 640x480 @ ~59.52 Hz timing verification
Pixel clock: 25 MHz  (50 MHz system clock ÷ 2, generated inside vgatiming)
Every test resets the DUT independently.

Timing reference (25.000 MHz pixel clock, not 25.175 MHz):
  Line period  : 800 px × 40 ns =  32 000 ns   (31.250 kHz — spec 31.469 kHz)
  Frame period : 525 ln × 32 000 ns = 16 800 000 ns  (~59.52 Hz — spec 59.94 Hz)
Both are within the tolerance range of real VGA monitors.
"""

import cocotb
from cocotb.utils import get_sim_time
from cocotb.triggers import Timer, RisingEdge, FallingEdge, ClockCycles

from helperfunctions import reset, start_50MHz_clock

# ── Pixel clock and system clock ──────────────────────────────────────────────
PIX_CLK_NS = 40    # 25 MHz  (sys-clk / 2)
SYS_CLK_NS = 20    # 50 MHz

# ── Horizontal timings (pixels) ───────────────────────────────────────────────
H_ACTIVE = 640
H_FP     = 16
H_SYNC   = 96
H_BP     = 48
H_TOTAL  = 800

# ── Vertical timings (lines) ──────────────────────────────────────────────────
V_ACTIVE = 480
V_FP     = 10
V_SYNC   = 2
V_BP     = 33
V_TOTAL  = 525

# ── Derived timing in ns ──────────────────────────────────────────────────────
LINE_NS   = H_TOTAL * PIX_CLK_NS        #  32 000 ns
FRAME_NS  = V_TOTAL * LINE_NS           # 16 800 000 ns
HSYNC_W   = H_SYNC  * PIX_CLK_NS       #   3 840 ns
VSYNC_W   = V_SYNC  * LINE_NS          #  64 000 ns
H_FP_NS   = H_FP    * PIX_CLK_NS       #     640 ns
H_BP_NS   = H_BP    * PIX_CLK_NS       #   1 920 ns

# ── Tolerances ────────────────────────────────────────────────────────────────
TOL_H = 2 * PIX_CLK_NS   # ±80 ns  for horizontal measurements
TOL_V = 2 * LINE_NS       # ±64 000 ns for vertical measurements

# ── 1 pixel clock = 2 system clock cycles ────────────────────────────────────
PIX = 2   # ClockCycles(dut.clk, PIX) advances one pixel


def check(label, measured, expected, tol):
    err = abs(measured - expected)
    assert err <= tol, (
        f"{label}: measured {measured:.0f} ns, "
        f"expected {expected:.0f} ns  (error {err:.0f} ns > tol {tol:.0f} ns)"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Test 1 — HSYNC period
# Must be 800 pixels × 40 ns = 32 000 ns  →  31.25 kHz line frequency
# VGA monitors accept 31.0–31.5 kHz; 31.25 kHz is in-spec.
# ─────────────────────────────────────────────────────────────────────────────
@cocotb.test()
async def test_hsync_period(dut):
    """HSYNC period must be 32 000 ns (31.25 kHz)."""
    start_50MHz_clock(dut)
    await reset(dut, 4)

    await FallingEdge(dut.hsync)          # sync to falling edge (start of pulse)
    t0 = get_sim_time("ns")
    await FallingEdge(dut.hsync)          # next falling edge = one full line later
    t1 = get_sim_time("ns")

    check("HSYNC period", t1 - t0, LINE_NS, TOL_H)


# ─────────────────────────────────────────────────────────────────────────────
# Test 2 — HSYNC pulse width
# Must be 96 pixels × 40 ns = 3 840 ns
# ─────────────────────────────────────────────────────────────────────────────
@cocotb.test()
async def test_hsync_pulse_width(dut):
    """HSYNC active-low pulse width must be 3 840 ns."""
    start_50MHz_clock(dut)
    await reset(dut, 4)

    await FallingEdge(dut.hsync)
    t_fall = get_sim_time("ns")
    await RisingEdge(dut.hsync)
    t_rise = get_sim_time("ns")

    check("HSYNC pulse width", t_rise - t_fall, HSYNC_W, TOL_H)


# ─────────────────────────────────────────────────────────────────────────────
# Test 3 — HSYNC front porch
# Gap from end of active pixels to falling edge of HSYNC must be 640 ns (16 px)
# ─────────────────────────────────────────────────────────────────────────────
@cocotb.test()
async def test_hsync_front_porch(dut):
    """HSYNC front porch must be 16 pixels × 40 ns = 640 ns."""
    start_50MHz_clock(dut)
    await reset(dut, 4)

    # Wait until we are actively displaying, then catch the end-of-active-row transition
    await RisingEdge(dut.in_active_frame)
    await FallingEdge(dut.in_active_frame)   # end of active pixels on this row
    t_active_end = get_sim_time("ns")
    await FallingEdge(dut.hsync)              # start of HSYNC
    t_hsync_start = get_sim_time("ns")

    check("HSYNC front porch", t_hsync_start - t_active_end, H_FP_NS, TOL_H)


# ─────────────────────────────────────────────────────────────────────────────
# Test 4 — HSYNC back porch
# Gap from rising edge of HSYNC to first active pixel must be 1 920 ns (48 px)
# ─────────────────────────────────────────────────────────────────────────────
@cocotb.test()
async def test_hsync_back_porch(dut):
    """HSYNC back porch must be 48 pixels × 40 ns = 1 920 ns."""
    start_50MHz_clock(dut)
    await reset(dut, 4)

    # Use a VSYNC-aligned row to ensure we are on an active line
    await RisingEdge(dut.vsync)              # end of vsync blanking
    await Timer(V_BP * LINE_NS, "ns")        # skip vertical back porch
    await RisingEdge(dut.hsync)              # end of an HSYNC pulse
    t_hsync_end = get_sim_time("ns")
    await RisingEdge(dut.in_active_frame)    # first active pixel of new row
    t_active_start = get_sim_time("ns")

    check("HSYNC back porch", t_active_start - t_hsync_end, H_BP_NS, TOL_H)


# ─────────────────────────────────────────────────────────────────────────────
# Test 5 — VSYNC period
# Must be 525 lines × 32 000 ns = 16 800 000 ns  (~59.52 Hz)
# ─────────────────────────────────────────────────────────────────────────────
@cocotb.test()
async def test_vsync_period(dut):
    """VSYNC period must be 16 800 000 ns (~59.52 Hz)."""
    start_50MHz_clock(dut)
    await reset(dut, 4)

    await FallingEdge(dut.vsync)
    t0 = get_sim_time("ns")
    await FallingEdge(dut.vsync)
    t1 = get_sim_time("ns")

    check("VSYNC period", t1 - t0, FRAME_NS, TOL_V)


# ─────────────────────────────────────────────────────────────────────────────
# Test 6 — VSYNC pulse width
# Must be 2 lines × 32 000 ns = 64 000 ns
# ─────────────────────────────────────────────────────────────────────────────
@cocotb.test()
async def test_vsync_pulse_width(dut):
    """VSYNC active-low pulse width must be 64 000 ns (2 lines)."""
    start_50MHz_clock(dut)
    await reset(dut, 4)

    await FallingEdge(dut.vsync)
    t_fall = get_sim_time("ns")
    await RisingEdge(dut.vsync)
    t_rise = get_sim_time("ns")

    check("VSYNC pulse width", t_rise - t_fall, VSYNC_W, TOL_V)


# ─────────────────────────────────────────────────────────────────────────────
# Test 7 — Sync polarity
# Both signals must idle HIGH; they pull LOW to signal sync (VGA spec: -HSync -VSync)
# ─────────────────────────────────────────────────────────────────────────────
@cocotb.test()
async def test_sync_polarity(dut):
    """HSYNC and VSYNC must idle HIGH (active-low, VGA -HSync -VSync)."""
    start_50MHz_clock(dut)
    await reset(dut, 4)

    # Sample well inside an active row (away from blanking transitions)
    await RisingEdge(dut.in_active_frame)
    await ClockCycles(dut.clk, 20)

    assert int(dut.hsync.value) == 1, \
        f"HSYNC not idle-high during active video (got {dut.hsync.value})"
    assert int(dut.vsync.value) == 1, \
        f"VSYNC not idle-high during active video (got {dut.vsync.value})"

    # Also confirm they go low during their respective sync intervals
    await FallingEdge(dut.hsync)
    await ClockCycles(dut.clk, 4)
    assert int(dut.hsync.value) == 0, "HSYNC not low during sync pulse"

    await FallingEdge(dut.vsync)
    await ClockCycles(dut.clk, 4)
    assert int(dut.vsync.value) == 0, "VSYNC not low during sync pulse"


# ─────────────────────────────────────────────────────────────────────────────
# Test 8 — No sync assertion during active video
# A VGA monitor relies on HSYNC/VSYNC being clean outside blanking;
# spurious pulses inside active video corrupt the raster.
# ─────────────────────────────────────────────────────────────────────────────
@cocotb.test()
async def test_no_sync_during_active_video(dut):
    """HSYNC and VSYNC must never be low while in_active_frame is high."""
    start_50MHz_clock(dut)
    await reset(dut, 4)

    # Sample at start, middle, and end of an active row on three different rows
    for row_offset in [0, H_ACTIVE // 2, H_ACTIVE - 2]:
        await RisingEdge(dut.in_active_frame)
        await ClockCycles(dut.clk, PIX * row_offset)
        t = get_sim_time("ns")
        assert int(dut.in_active_frame.value) == 1, f"in_active_frame dropped at t={t}"
        assert int(dut.hsync.value) == 1, \
            f"HSYNC low during active video at x≈{row_offset}, t={t}"
        assert int(dut.vsync.value) == 1, \
            f"VSYNC low during active video at x≈{row_offset}, t={t}"
        # finish the row
        await FallingEdge(dut.in_active_frame)


# ─────────────────────────────────────────────────────────────────────────────
# Test 9 — in_active_frame suppressed during all blanking intervals
# The signal must stay 0 during H-front porch, HSYNC, H-back porch,
# V-front porch, VSYNC, and V-back porch.
# ─────────────────────────────────────────────────────────────────────────────
@cocotb.test()
async def test_inactive_during_blanking(dut):
    """in_active_frame must be 0 throughout every blanking interval."""
    start_50MHz_clock(dut)
    await reset(dut, 4)

    # H-blanking: sample inside front porch, HSYNC, and back porch
    await FallingEdge(dut.in_active_frame)   # end of active pixels
    await ClockCycles(dut.clk, PIX * (H_FP // 2))
    assert int(dut.in_active_frame.value) == 0, "in_active_frame HIGH in H front porch"

    await FallingEdge(dut.hsync)             # start of HSYNC
    await ClockCycles(dut.clk, PIX * (H_SYNC // 2))
    assert int(dut.in_active_frame.value) == 0, "in_active_frame HIGH during HSYNC"

    await RisingEdge(dut.hsync)              # end of HSYNC = start of back porch
    await ClockCycles(dut.clk, PIX * (H_BP // 2))
    assert int(dut.in_active_frame.value) == 0, "in_active_frame HIGH in H back porch"

    # V-blanking: sample inside V front porch, VSYNC, and V back porch
    await FallingEdge(dut.vsync)             # start of VSYNC (front porch already passed)
    assert int(dut.in_active_frame.value) == 0, "in_active_frame HIGH at VSYNC start"
    await RisingEdge(dut.vsync)              # end of VSYNC = start of V back porch
    assert int(dut.in_active_frame.value) == 0, "in_active_frame HIGH at VSYNC end"
    await Timer(LINE_NS * (V_BP // 2), "ns")
    assert int(dut.in_active_frame.value) == 0, "in_active_frame HIGH in V back porch"


# ─────────────────────────────────────────────────────────────────────────────
# Test 10 — Pixel coordinates
# pixel_x must count 0–639, pixel_y must count 0–479.
# Both must read 0 when in_active_frame is low (no stale coordinates).
# ─────────────────────────────────────────────────────────────────────────────
@cocotb.test()
async def test_pixel_coordinates(dut):
    """pixel_x: 0–639, pixel_y: 0–479; both 0 during blanking."""
    start_50MHz_clock(dut)
    await reset(dut, 4)

    # Align cleanly to the top-left pixel (row 0, col 0)
    await RisingEdge(dut.vsync)              # VSYNC just ended; now in V back porch
    await RisingEdge(dut.in_active_frame)    # first active pixel of frame (after back porch)

    # ── (x=0, y=0) ───────────────────────────────────────────────────────────
    assert int(dut.pixel_x.value) == 0, \
        f"Row 0, col 0: pixel_x={dut.pixel_x.value}"
    assert int(dut.pixel_y.value) == 0, \
        f"Row 0, col 0: pixel_y={dut.pixel_y.value}"

    # ── Last column of row 0: (x=639, y=0) ───────────────────────────────────
    await ClockCycles(dut.clk, PIX * (H_ACTIVE - 1) + 1)
    assert int(dut.pixel_x.value) == H_ACTIVE - 1, \
        f"Row 0, last col: pixel_x={dut.pixel_x.value} (expected {H_ACTIVE-1})"
    assert int(dut.pixel_y.value) == 0

    # ── One pixel further → blanking; coordinates must clear to 0 ────────────
    await ClockCycles(dut.clk, PIX)
    assert int(dut.in_active_frame.value) == 0, \
        "in_active_frame still HIGH one pixel past end of row 0"
    assert int(dut.pixel_x.value) == 0, \
        f"pixel_x not 0 in H blanking: {dut.pixel_x.value}"
    assert int(dut.pixel_y.value) == 0, \
        f"pixel_y not 0 in H blanking: {dut.pixel_y.value}"

    # ── First pixel of row 1: (x=0, y=1) ─────────────────────────────────────
    # From h=640 (start of H blanking), count exactly one blanking period to h=0, v=1.
    # Using ClockCycles avoids reading combinational outputs before they settle after
    # the pix_clk edge (RisingEdge(in_active_frame) fires in the same delta cycle as
    # the FF update, causing stale reads in Icarus+cocotb VPI).
    await ClockCycles(dut.clk, (H_TOTAL - H_ACTIVE) * PIX)
    assert int(dut.pixel_x.value) == 0, \
        f"Row 1, col 0: pixel_x={dut.pixel_x.value}"
    assert int(dut.pixel_y.value) == 1, \
        f"Row 1, col 0: pixel_y={dut.pixel_y.value} (expected 1)"

    # ── First pixel of last row: (x=0, y=479) ────────────────────────────────
    # From row 1 start (h=0, v=1), advance exactly (V_ACTIVE - 2) full lines to v=479.
    await ClockCycles(dut.clk, (V_ACTIVE - 2) * H_TOTAL * PIX)
    assert int(dut.pixel_y.value) == V_ACTIVE - 1, \
        f"Last row: pixel_y={dut.pixel_y.value} (expected {V_ACTIVE - 1})"
    assert int(dut.pixel_x.value) == 0, \
        f"Last row, col 0: pixel_x={dut.pixel_x.value}"


# ─────────────────────────────────────────────────────────────────────────────
# Test 11 — end_of_frame pulse
# Fires once per frame at (vertical=480, horizontal=641) — one pixel into the
# first blanking line, immediately after the last active pixel column.
# The pulse is one pixel clock wide and the interval between pulses equals FRAME_NS.
# ─────────────────────────────────────────────────────────────────────────────
@cocotb.test()
async def test_end_of_frame(dut):
    """end_of_frame pulses once per frame; interval must equal FRAME_NS."""
    start_50MHz_clock(dut)
    await reset(dut, 4)

    await RisingEdge(dut.end_of_frame)
    t0 = get_sim_time("ns")

    # Pulse width: combinational signal, holds for exactly one pixel period
    await FallingEdge(dut.end_of_frame)
    pulse_w = get_sim_time("ns") - t0
    assert pulse_w <= 2 * PIX_CLK_NS, \
        f"end_of_frame pulse too wide: {pulse_w:.0f} ns (expected ≤{2*PIX_CLK_NS} ns)"

    # Interval to next pulse = one full frame
    await RisingEdge(dut.end_of_frame)
    t1 = get_sim_time("ns")

    check("end_of_frame interval", t1 - t0, FRAME_NS, TOL_V)

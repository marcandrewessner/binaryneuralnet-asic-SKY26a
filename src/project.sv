/*
 * Copyright (c) 2024 Your Name
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_maw_game (
    input  logic [7:0] ui_in,    // Dedicated inputs
    output logic [7:0] uo_out,   // Dedicated outputs
    input  logic [7:0] uio_in,   // IOs: Input path
    output logic [7:0] uio_out,  // IOs: Output path
    output logic [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  logic       ena,      // always 1 when the design is powered, so you can ignore it
    input  logic       clk,      // clock
    input  logic       rst_n     // reset_n - low to reset
);

  // Define the screen signals
  logic hsync, vsync;
  logic [2:0] rgb;

  assign uo_out = {
    hsync, vsync,
    rgb,
    3'b000
  };

  assign uio_out = '0;
  assign uio_oe = 8'b1111_1111;

  assign _unused = {ena, ui_in, uio_in};

endmodule

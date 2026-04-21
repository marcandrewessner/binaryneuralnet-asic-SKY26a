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
  // Define the button inputs (already debounced)
  logic btn_up, btn_down, btn_left, btn_right, btn_action;

  assign btn_up = ui_in[7];
  assign btn_down = ui_in[6];
  assign btn_left = ui_in[5];
  assign btn_right = ui_in[4];
  assign btn_action = ui_in[3];

  assign uo_out = {hsync, vsync, rgb, 3'b000};

  assign uio_out = '0;
  assign uio_oe = 8'b1111_1111;

  logic _unused;
  assign _unused = &{ena, uio_in};

  maw_main i_maw_main(
    .clk_i(clk),
    .rst_ni(rst_n),
    .btn_up_i(btn_up),
    .btn_down_i(btn_down),
    .btn_right_i(btn_right),
    .btn_left_i(btn_left),
    .btn_action_i(btn_action),
    .hsync_o(hsync),
    .vsync_o(vsync),
    .rgb_o(rgb)
  );

endmodule

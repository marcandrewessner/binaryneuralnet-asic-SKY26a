`timescale 1ns/1ps
`default_nettype none

module tb_tvsimulator (
  input  logic       clk,
  input  logic       rst_n,

  output logic       hsync,
  output logic       vsync,
  output logic [2:0] rgb
);

  render_engine dut (
    .clk_i  (clk),
    .rst_ni (rst_n),
    .hsync_o(hsync),
    .vsync_o(vsync),
    .rgb_o  (rgb)
  );

endmodule

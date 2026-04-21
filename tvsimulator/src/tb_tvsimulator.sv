`default_nettype none

module tb_tvsimulator (
  input  logic       clk,
  input  logic       rst_n,

  input logic  btn_up,
  input logic btn_down,
  input logic btn_left,
  input logic btn_right,
  input logic btn_action,

  output logic       hsync,
  output logic       vsync,
  output logic [2:0] rgb
);

  // Declare the outer world of the project
  logic [7:0] ui_in;    // Dedicated inputs
  logic [7:0] uo_out;   // Dedicated outputs
  logic [7:0] uio_in;   // IOs: Input path
  logic [7:0] uio_out;  // IOs: Output path
  logic [7:0] uio_oe;

  assign uio_in = '0;

  tt_um_maw_game i_project(
    .clk(clk),
    .rst_n(rst_n),
    .ena(1),
    .ui_in(ui_in),
    .uo_out(uo_out),
    .uio_in(uio_in),
    .uio_out(uio_out),
    .uio_oe(uio_oe)
  );

  // Extract video signals from project output
  assign hsync = uo_out[7];
  assign vsync = uo_out[6];
  assign rgb   = uo_out[5:3];

  // Drive button inputs into project
  assign ui_in = {
    btn_up,
    btn_down,
    btn_left,
    btn_right,
    btn_action,
    3'(0)
  };

endmodule


/*

This is the render engine, that gets connected
to the screen via VGA

*/



import graphic_consts::*;

module tb_vgatiming (
  input logic clk,
  input logic rst_n,

  output logic hsync_o,
  output logic vsync_o,
  output logic [2:0] rgb_o
);

  logic in_active_frame, end_of_frame;
  logic [9:0] pixel_x; // 10bits => 1024
  logic [9:0] pixel_y; // 10bits => 1024

  logic [2:0] rgb;

  vgatiming vgat(
    .clk_i(clk),
    .rst_ni(rst_n),
    .in_active_frame_o(in_active_frame),
    .end_of_frame_o(end_of_frame),
    .pixel_x_o(pixel_x),
    .pixel_y_o(pixel_y),
    .hsync_o(hsync_o),
    .vsync_o(vsync_o)
  );

  // Now we build stripes
  logic r;
  logic g;

  assign r = pixel_x[3];

  assign g = ~r;
  assign rgb = {r, g, 1'b0} & {3{in_active_frame}};

endmodule
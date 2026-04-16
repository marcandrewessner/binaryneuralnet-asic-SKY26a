
/*

This is the render engine, that gets connected
to the screen via VGA

*/


`default_nettype none

import graphic_consts::*;

module render_engine (
  input logic clk_i,
  input logic rst_ni,

  output logic hsync_o,
  output logic vsync_o,
  output logic [2:0] rgb_o,
);

  logic in_active_frame, end_of_frame;
  logic [9:0] pixel_x; // 10bits => 1024
  logic [9:0] pixel_y; // 10bits => 1024

  logic [2:0] rgb;

  vgatiming vgat(
    .clk_i(clk_i),
    .rst_ni(rst_ni),
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
  assign rgb = {r, g, 0} & {3{in_active_frame}};

endmodule
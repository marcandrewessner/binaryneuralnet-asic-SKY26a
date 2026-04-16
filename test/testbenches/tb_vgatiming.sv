
import graphic_consts::*;

module tb_vgatiming;

  logic clk, rst_n;
  logic hsync, vsync;
  logic in_active_frame, end_of_frame;
  logic [9:0] pixel_x;
  logic [9:0] pixel_y;
  logic [2:0] rgb;

  vgatiming vgat(
    .clk_i(clk),
    .rst_ni(rst_n),
    .end_of_frame_o(end_of_frame),
    .in_active_frame_o(in_active_frame),
    .pixel_x_o(pixel_x),
    .pixel_y_o(pixel_y),
    .hsync_o(hsync),
    .vsync_o(vsync)
  );

  logic r, g;
  assign r = pixel_x[3];
  assign g = ~r;
  assign rgb = {r, g, 1'b0} & {3{in_active_frame}};

endmodule

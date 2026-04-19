
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
  output logic [2:0] rgb_o
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
  assign r = pixel_x==10'(position_counter_q) && (pixel_y>=10 && pixel_y<15);

  assign rgb = {r, r, r} & {3{in_active_frame}};
  assign rgb_o = rgb;

  int unsigned position_counter_d, position_counter_q;
  
  always_comb begin
    position_counter_d = position_counter_q+1;
    if(position_counter_d==SCREEN_WIDTH)
      position_counter_d = 0;
  end

  always_ff @(posedge end_of_frame or negedge rst_ni) begin
    if(!rst_ni) begin
      position_counter_q <= 0;
    end else begin
      position_counter_q <= position_counter_d;
    end
  end

endmodule
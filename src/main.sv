
module maw_main import graphics_engine_pkg::*; (
  input  logic       clk_i,
  input  logic       rst_ni,

  input logic  btn_up_i,
  input logic btn_down_i,
  input logic btn_left_i,
  input logic btn_right_i,
  input logic btn_action_i,

  output logic       hsync_o,
  output logic       vsync_o,
  output logic [2:0] rgb_o
);

  logic end_of_frame;
  pix_coord_t cross_x_d, cross_x_q;
  pix_coord_t cross_y_d, cross_y_q;
  pix_pos_t cross_pos;
  assign cross_pos.x = cross_x_q;
  assign cross_pos.y = cross_y_q;

  render_engine i_render_engine (
    .clk_i(clk_i),
    .rst_ni(rst_ni),
    .end_of_frame_o(end_of_frame),
    .hsync_o(hsync_o),
    .vsync_o(vsync_o),
    .rgb_o(rgb_o),

    .cross_pos_i(cross_pos)
  );

  localparam pix_coord_t MOVEMENT_SPEED = 3;

  // Now react
  always_comb begin
    cross_x_d = cross_x_q + (btn_right_i ? MOVEMENT_SPEED : 0) - (btn_left_i ? MOVEMENT_SPEED : 0);
    cross_y_d = cross_y_q - (btn_up_i    ? MOVEMENT_SPEED : 0) + (btn_down_i ? MOVEMENT_SPEED : 0);
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if(!rst_ni) begin
      cross_x_q <= 100;
      cross_y_q <= 100;
    end else if (end_of_frame) begin
      cross_x_q <= cross_x_d;
      cross_y_q <= cross_y_d;
    end
  end

endmodule
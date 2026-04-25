
module maw_main
  import graphics_engine_pkg::*;
  import game_logic_pkg::*;
(
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
 
  // Crosshair
  game_pos_t crosshair_pos;
  pix_pos_t crosshair_pos_pix;
  assign crosshair_pos_pix = game2pix_pos_transformation(crosshair_pos);

  // Enemy
  game_pos_t enemy_pos;
  pix_pos_t enemy_pos_pix;
  assign enemy_pos_pix = game2pix_pos_transformation(enemy_pos);

  render_engine i_render_engine (
    .clk_i(clk_i),
    .rst_ni(rst_ni),
    .end_of_frame_o(end_of_frame),
    .hsync_o(hsync_o),
    .vsync_o(vsync_o),
    .rgb_o(rgb_o),
    .cross_pos_i(crosshair_pos_pix),
    .ghost_pos_i(enemy_pos_pix)
  );

  crosshair_control i_crosshair_control (
    .clk_i(clk_i),
    .rst_ni(rst_ni),
    .clk_virt_i(end_of_frame),
    .btn_up_i(btn_up_i),
    .btn_down_i(btn_down_i),
    .btn_right_i(btn_right_i),
    .btn_left_i(btn_left_i),
    .btn_action_i(btn_action_i),
    .pos_o(crosshair_pos)
  );

  localparam game_pos_t ENEMY_RST_POS = game_pos_t'{x:200, y:300};
  enemy_movement i_enemy_movement (
    .clk_i(clk_i),
    .rst_ni(rst_ni),
    .clk_virt_i(end_of_frame),
    .rst_position_i(ENEMY_RST_POS),
    .rtl_i(1),
    .enemy_position_o(enemy_pos)
  );

endmodule
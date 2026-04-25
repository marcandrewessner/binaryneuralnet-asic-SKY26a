
`include "ff_macros.svh"

// Module to calculate the next position for the ghost
// Floating from right to left (configurable)
module enemy_movement
  import game_logic_pkg::*;
(
    input logic clk_i,
    input logic rst_ni,

    // This is used as a time signal (virtual clk)
    input logic clk_virt_i,
    input game_pos_t rst_position_i,
    input logic rtl_i,

    // Output the position of the ghost
    output game_pos_t enemy_position_o
);

  localparam game_coord_t ENEMY_Y = 220;
  localparam game_coord_t MOVEMENT_SPEED = 0;

  game_pos_t pos_d, pos_q;

  game_coord_t wave1_val;
  logic wave1_is_negative;

  always_comb begin
    // Calculate the position of the enemy
    pos_d.x = pos_q.x + MOVEMENT_SPEED;
    pos_d.y = ENEMY_Y + (!wave1_is_negative ? wave1_val : 0) - (wave1_is_negative ? wave1_val : 0);
  end
  
  `FFAR_EN(clk_i, rst_ni, rst_position_i, pos_q, pos_d, clk_virt_i);

  // Initiatae the wave form generators
  triangle_wave_gen #(
    .QUARTER_WAVE_PERIOD(100)
  ) i_triangle_wave_gen (
    .clk_i(clk_i),
    .rst_ni(rst_ni),
    .clk_virt_i(clk_virt_i),
    .wave_o(wave1_val),
    .is_negative_o(wave1_is_negative)
  );

  assign enemy_position_o = pos_q;

endmodule

module ghost_sprite
  import graphics_engine_pkg::*;
  import graphics_rom_pkg::*;
(
  input logic clk_i,
  input logic rst_ni,

  input sprite_input_t sprite_input,
  output sprite_output_t sprite_output
);

  sprite_output_t ghost_sprite_generated_out;

  ghost_sprite_generated i_ghost_sprite_generated (
    .clk_i(clk_i),
    .rst_ni(rst_ni),
    .sprite_input(sprite_input),
    .sprite_output(ghost_sprite_generated_out)
  );

  logic alpha, active;
  assign alpha = ghost_sprite_generated_out.color[3];
  assign active = ghost_sprite_generated_out.color[2];

  assign sprite_output.color = '{alpha, active, 1'(0), 1'(0)};

endmodule

module crosshair_sprite
  import graphics_engine_pkg::*;
  import graphics_rom_pkg::*;
(
  input logic clk_i,
  input logic rst_ni,

  input sprite_input_t sprite_input,
  output sprite_output_t sprite_output
);

  pix_coord_t cx, cy, vx, vy;
  assign cx = sprite_input.center_pix.x;
  assign cy = sprite_input.center_pix.y;
  assign vx = sprite_input.vga_pos.x;
  assign vy = sprite_input.vga_pos.y;

  // Make the cross moving
  logic cross_active;
  assign cross_active = (
    vx == cx-1    ||
    vx == cx      ||
    vx == cx + 1  ||
    vy == cy-1    ||
    vy == cy      ||
    vy == cy+1
  );

  // Create the outer box
  localparam pix_coord_t OUTERBOX_WIDTH = 20;
  logic outerbox_active;
  assign outerbox_active = (
    vx-OUTERBOX_WIDTH < cx && cx < vx+OUTERBOX_WIDTH &&
    vy-OUTERBOX_WIDTH < cy && cy < vy+OUTERBOX_WIDTH
  );

  // Create the inner box
  localparam pix_coord_t INNERBOX_WIDTH = OUTERBOX_WIDTH-2;
  logic innerbox_active;
  assign innerbox_active = (
    vx-INNERBOX_WIDTH < cx && cx < vx+INNERBOX_WIDTH &&
    vy-INNERBOX_WIDTH < cy && cy < vy+INNERBOX_WIDTH
  );

  logic white;
  assign white = cross_active || (outerbox_active && ~innerbox_active);

  assign sprite_output.color = '{~white, 3{white}};

endmodule
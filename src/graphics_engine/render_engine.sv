
/*

This is the render engine, that gets connected
to the screen via VGA

*/


`default_nettype none

module render_engine import graphics_engine_pkg::*; import graphics_rom_pkg::*; (
  input logic clk_i,
  input logic rst_ni,

  output logic end_of_frame_o,
  output logic hsync_o,
  output logic vsync_o,
  output rgb_t rgb_o,

  // Now we feed in the game state
  input pix_pos_t cross_pos_i
);

  pix_pos_t vga_pos;
  vgatiming i_vgat(
    .clk_i(clk_i),
    .rst_ni(rst_ni),
    .in_active_frame_o(),
    .end_of_frame_o(end_of_frame_o),
    .pixel_x_o(vga_pos.x),
    .pixel_y_o(vga_pos.y),
    .hsync_o(hsync_o),
    .vsync_o(vsync_o)
  );

  // ==== CROSSHAIR ======
  argb_t cross_color;
  
  sprite_input_t cross_input;
  assign cross_input.center_pix = cross_pos_i;
  assign cross_input.vga_pos = vga_pos;

  sprite_output_t cross_output;
  assign cross_color = cross_output.color;

  crosshair_sprite i_crosshair_sprite (
    .clk_i(clk_i),
    .rst_ni(rst_ni),
    .sprite_input(cross_input),
    .sprite_output(cross_output)
  );

  // ====== Render the Ghost ========
  argb_t ghost_color;

  sprite_input_t ghost_input;
  assign ghost_input.center_pix = {PIXEL_COORD_T_W'(200), PIXEL_COORD_T_W'(200)};
  assign ghost_input.vga_pos = vga_pos;

  sprite_output_t ghost_output;
  assign ghost_color = ghost_output.color;

  ghost_sprite i_ghost_sprite (
    .clk_i(clk_i),
    .rst_ni(rst_ni),
    .sprite_input(ghost_input),
    .sprite_output(ghost_output)
  );

  // ====== NOW RENDER LAYERED ======
  logic ghost_active_n;
  logic cross_active_n;
  assign ghost_active_n = ghost_color[3];
  assign cross_active_n = cross_color[3];

  always_comb begin
    rgb_o = 3'(0);
    if(!cross_active_n)
      rgb_o = cross_color[2:0];
    else if (!ghost_active_n)
      rgb_o = ghost_color[2:0];
  end

endmodule
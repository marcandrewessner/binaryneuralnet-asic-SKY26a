

package graphics_rom_pkg;

  import graphics_engine_pkg::argb_t;
  import graphics_engine_pkg::pix_pos_t;

  typedef struct packed {
    pix_pos_t center_pix;
    pix_pos_t vga_pos;
  } sprite_input_t;

  typedef struct packed {
    argb_t color;
  } sprite_output_t;

endpackage
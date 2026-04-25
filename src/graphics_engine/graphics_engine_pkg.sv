package graphics_engine_pkg;

  parameter int unsigned SCREEN_WIDTH = 640;
  parameter int unsigned SCREEN_HEIGHT = 480;

  parameter int PIXEL_COORD_T_W = 10;
  typedef logic [PIXEL_COORD_T_W-1:0] pix_coord_t;  // 10bits => 1024

  parameter int ARGB_T_W = 4;
  typedef logic [ARGB_T_W-1:0] argb_t;

  parameter int RGB_T_W = 3;
  typedef logic [RGB_T_W-1:0] rgb_t;

  // Define the pixel position
  typedef struct packed {
    pix_coord_t x;
    pix_coord_t y;
  } pix_pos_t;

endpackage

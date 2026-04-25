
package game_logic_pkg;

  import graphics_engine_pkg::pix_coord_t;
  import graphics_engine_pkg::pix_pos_t;

  // Create a logical position type
  // This is maybe customized further
  // if logic does not run on pixel perfect logic
  // but rather virtual pixles (for example scaled down by 2)
  typedef pix_coord_t game_coord_t;

  // Present the according function to convert the game_coord to pix_coord
  function pix_coord_t game2pix_coord_transformation(input game_coord_t game_coords);
    pix_coord_t pix_coord_output;
    pix_coord_output = game_coords; // Identity function
    return pix_coord_output;
  endfunction

  // Define the game position
  typedef struct packed {
    game_coord_t x;
    game_coord_t y;
  } game_pos_t;

  // Present the according function to convert the game position
  // to pixel position
  function pix_pos_t game2pix_pos_transformation(input game_pos_t game_position);
    pix_pos_t pix_pos_output;
    pix_pos_output.x = game2pix_coord_transformation(game_position.x);
    pix_pos_output.y = game2pix_coord_transformation(game_position.y);
    return pix_pos_output;
  endfunction

endpackage

`include "ff_macros.svh"

module triangle_wave_gen
  import game_logic_pkg::*;
#(
  parameter game_coord_t QUARTER_WAVE_PERIOD
)
(
  input logic clk_i,
  input logic rst_ni,
  input logic clk_virt_i,

  output game_coord_t wave_o,
  output logic is_negative_o
);

  // Note that we cycle through 4 quarters up down down up
  localparam game_coord_t COUNTER_TOP = QUARTER_WAVE_PERIOD;

  logic [1:0] phase_d, phase_q;
  game_coord_t wave_cnt_d, wave_cnt_q;

  always_comb begin
    wave_cnt_d = (wave_cnt_q==COUNTER_TOP) ? 0 : wave_cnt_q+1;
    phase_d = phase_q + (wave_cnt_q==COUNTER_TOP);
  end

  `FFAR_EN(clk_i, rst_ni, 0, phase_q, phase_d, clk_virt_i);
  `FFAR_EN(clk_i, rst_ni, 0, wave_cnt_q, wave_cnt_d, clk_virt_i);

  assign is_negative_o = phase_q==2 || phase_q==3;
  always_comb begin
    logic is_running_down;
    is_running_down = phase_q==1 || phase_q==3;
    
    if(is_running_down)
      wave_o = COUNTER_TOP - wave_cnt_q;
    else
      wave_o = wave_cnt_q;
  end

endmodule

/*

This describes the timing of the video format
Using a system clock of 50M Hz

Pixel Clock: 50.000 MHz
Frame: 1040 × 666

HORIZONTAL (one line, 1040 pixels)
|<------SCREEN_WIDTH------>|<-56->|<---120--->|<--64-->|
|    ACTIVE       |  FP  |  HSYNC    |   BP   |
████████████████████████████████....................
                    ____________
HSYNC: ____________|            |___________________

VERTICAL (one frame, 666 lines)
|<------SCREEN_HEIGHT------>|<-37->|<-6->|<--23-->|
|    ACTIVE       |  FP  |VSYNC|   BP   |

VSYNC: __________________________|      |___________

FLOW:
[SCREEN_HEIGHT lines ACTIVE]
→ [37 FP] → [6 VSYNC] → [23 BP] → repeat (~72 Hz)

*/

`default_nettype none

import graphic_consts::*;

module vgatiming #(
  localparam int HFP_COUNT = 56,
  localparam int HSYNC_COUNT = 120,
  localparam int HBP_COUNT = 64,

  localparam int VFP_COUNT = 37,
  localparam int VSYNC_COUNT = 6,
  localparam int VBP_COUNT = 23,

  localparam int HMAX = SCREEN_WIDTH+HFP_COUNT+HSYNC_COUNT+HBP_COUNT,
  localparam int VMAX = SCREEN_HEIGHT+VFP_COUNT+VSYNC_COUNT+VBP_COUNT,
) (
  input logic clk_i,
  input logic rst_ni,

  output logic in_active_frame_o,
  output logic end_of_frame_o,
  output logic [9:0] pixel_x_o, // 10bits => 1024
  output logic [9:0] pixel_y_o, // 10bits => 1024

  output logic hsync_o,
  output logic vsync_o,
);

  logic in_active_frame, end_of_frame;
  logic [9:0] pixel_x, pixel_y;
  logic hsync, vsync;

  logic [10:0] horizontal_counter_d, horizontal_counter_q;
  logic [9:0] vertical_counter_d, vertical_counter_q;

  assign in_active_frame_o = in_active_frame;
  assign end_of_frame_o = end_of_frame;

  assign pixel_x_o = pixel_x;
  assign pixel_y_o = pixel_y;

  assign hsync_o = hsync;
  assign vsync_o = vsync;

  always_comb begin
    // Create wrap around counters
    horizontal_counter_d = (horizontal_counter_q==HMAX) ? 0 : horizontal_counter_q + 1;
    vertical_counter_d = (vertical_counter_q==HMAX) ? 0 : vertical_counter_q + 1;
    // output the active pixel coordinates
    in_active_frame = (horizontal_counter_q < SCREEN_WIDTH) && (vertical_counter_q < SCREEN_HEIGHT);
    pixel_x = in_active_frame ? horizontal_counter_q : 0;
    pixel_y = in_active_frame ? vertical_counter_q : 0;
    // Create the HSYNC and VSYNC signals
    hsync = (horizontal_counter_q >= SCREEN_WIDTH+HFP_COUNT) && (horizontal_counter_q<SCREEN_WIDTH+HFP_COUNT+HSYNC_COUNT);
    vsync = (vertical_counter_q >= SCREEN_HEIGHT+VFP_COUNT) && (vertical_counter_q<SCREEN_HEIGHT+VFP_COUNT+VSYNC_COUNT);
    // Calcaulte the end of frame
    end_of_frame = (vertical_counter_q==SCREEN_HEIGHT) && (horizontal_counter_q==SCREEN_WIDTH+1); 
  end

  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      horizontal_counter_q <= 0;
      vertical_counter_q <= 0;
    end else begin
      horizontal_counter_q <= horizontal_counter_d;
      vertical_counter_q <= vertical_counter_d;
    end
  end

endmodule
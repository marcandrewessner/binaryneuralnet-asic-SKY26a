/*


Note: with tiny tapeout we'll just use Pixelclock of 25MHz

Name          640x480p60
Standard      Historical
VIC                    1
Short Name       DMT0659
Aspect Ratio         4:3

Pixel Clock       25.175 MHz
TMDS Clock       251.750 MHz
Pixel Time          39.7 ns ±0.5%
Horizontal Freq.  31.469 kHz
Line Time           31.8 μs
Vertical Freq.    59.940 Hz
Frame Time          16.7 ms

Horizontal Timings
Active Pixels        640
Front Porch           16
Sync Width            96
Back Porch            48
Blanking Total       160
Total Pixels         800
Sync Polarity        neg

Vertical Timings
Active Lines         480
Front Porch           10
Sync Width             2
Back Porch            33
Blanking Total        45
Total Lines          525
Sync Polarity        neg

Active Pixels    307,200
Data Rate          604.2 Mbps

Modeline "640x480_60" 25.175 640 656 752 800 480 490 492 525 -HSync -VSync

Frame Memory (Kbits)
  1-bit Colour        300
  8-bit Colour      2,400
12-bit Colour      3,600
24-bit Colour      7,200
32-bit Colour      9,600


*/

`default_nettype none

import graphic_consts::*;

module vgatiming #(
  localparam int HFP_COUNT = 16,
  localparam int HSYNC_COUNT = 96,
  localparam int HBP_COUNT = 48,

  localparam int VFP_COUNT = 10,
  localparam int VSYNC_COUNT = 2,
  localparam int VBP_COUNT = 33,

  localparam int HMAX = SCREEN_WIDTH+HFP_COUNT+HSYNC_COUNT+HBP_COUNT - 1,
  localparam int VMAX = SCREEN_HEIGHT+VFP_COUNT+VSYNC_COUNT+VBP_COUNT - 1
) (
  input logic clk_i,
  input logic rst_ni,

  output logic in_active_frame_o,
  output logic end_of_frame_o,
  output logic [9:0] pixel_x_o, // 10bits => 1024
  output logic [9:0] pixel_y_o, // 10bits => 1024

  output logic hsync_o,
  output logic vsync_o
);

  logic pix_clk;

  logic in_active_frame, end_of_frame;
  logic [9:0] pixel_x, pixel_y;
  logic hsync, vsync;

  logic [9:0] horizontal_counter_d, horizontal_counter_q;
  logic [9:0] vertical_counter_d, vertical_counter_q;

  assign pixel_x_o = pixel_x;
  assign pixel_y_o = pixel_y;
  assign end_of_frame_o = end_of_frame;
  assign in_active_frame_o = in_active_frame;

  // Active low
  assign hsync_o = ~hsync;
  assign vsync_o = ~vsync;

  always_comb begin
    horizontal_counter_d = (horizontal_counter_q==HMAX) ? 0 : horizontal_counter_q + 1;
    if (horizontal_counter_q==HMAX)
      vertical_counter_d = (vertical_counter_q==VMAX) ? 0 : vertical_counter_q + 1;
    else
      vertical_counter_d = vertical_counter_q;
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

  // Important to Note: this is running at pixelclock
  always_ff @(posedge pix_clk or negedge rst_ni) begin
    if (!rst_ni) begin
      horizontal_counter_q <= 0;
      vertical_counter_q <= 0;
    end else begin
      horizontal_counter_q <= horizontal_counter_d;
      vertical_counter_q <= vertical_counter_d;
    end
  end

  // Generate the pixelclock just divide by two 50MHz/2 = 25MHz
  always_ff @(posedge clk_i or negedge rst_ni) begin
    if(!rst_ni)
      pix_clk <= 0;
    else
      pix_clk <= ~pix_clk;
  end

endmodule
#include "Vtb_tvsimulator.h"
#include "verilated.h"

#include <chrono>
#include <cstdio>
#include <memory>
#include <SDL2/SDL.h>

#include "DisplayManager.h"

// Define the VGA timing
constexpr struct {
  int HFP = 16;
  int HSYNC = 96;
  int HBP = 48;
  int HTOTAL = 800;
  int VFP = 10;
  int VSYNC = 2;
  int VBP = 33;
  int VTOTAL = 525;
} VGATiming;

double sc_time_stamp(){ return 0; }

// Define helper functions
void advance_one_pixel(Vtb_tvsimulator* dut);
void advance_n_pixels(Vtb_tvsimulator* dut, unsigned int npixels);
void fullspeed_testing(Vtb_tvsimulator* dut);

int main(int argc, char** argv) {
  VerilatedContext* ctx = new VerilatedContext;
  ctx->commandArgs(argc, argv);
  
  Vtb_tvsimulator* dut = new Vtb_tvsimulator{ctx};
  
  // Reset the device for 4 clock cylces 
  dut->clk   = 0;
  dut->rst_n = 0;
  dut->eval();
  for (int i = 0; i < 8; i++) {
    dut->clk ^= 1;
    dut->eval();
  }
  
  printf("Current clock before display: %d", dut->clk);
  printf("Use WASD for arrow keys and space for action!");

  // Open the window
  DisplayManager display;
  auto frame = std::make_unique<uint32_t[]>(DisplayManager::SCREEN_HEIGHT*DisplayManager::SCREEN_WIDTH);

  unsigned int vga_pos_x = 0;
  unsigned int vga_pos_y = 0;

  // Capture the prev signals
  auto prev_hsync = dut->hsync;
  auto prev_vsync = dut->vsync;

  // Startup the mainloop
  dut->rst_n = 1;
  uint64_t frame_count = 0;
  uint64_t last_ticks = SDL_GetTicks64();
  while(!display.getInputEvents().quit){
    advance_one_pixel(dut);

    bool end_of_frame = false;

    // Draw pixel if in drawing area
    bool in_drawing_area = (
      vga_pos_x >= VGATiming.HBP &&
      vga_pos_x <  VGATiming.HBP + DisplayManager::SCREEN_WIDTH &&
      vga_pos_y >= VGATiming.VBP &&
      vga_pos_y <  VGATiming.VBP + DisplayManager::SCREEN_HEIGHT
    );

    // Now draw the pixels in drawing area
    if(in_drawing_area){
      auto pixel_x = vga_pos_x - VGATiming.HBP;
      auto pixel_y = vga_pos_y - VGATiming.VBP;
      
      uint8_t r = (dut->rgb >> 2) & 0b1;
      uint8_t g = (dut->rgb >> 1) & 0b1;
      uint8_t b = (dut->rgb >> 0) & 0b1;

      uint32_t color = 0xFF000000 + r*(0xFF << 2*8) + g*(0xFF << 1*8) + b*(0xFF << 0*8);
      frame[pixel_x + pixel_y*DisplayManager::SCREEN_WIDTH] = color;
    }
  
    // HSYNC RISING EDGE => HSYNC END
    if(prev_hsync==0 && dut->hsync){
      vga_pos_x=0;
      vga_pos_y++;
    } else {
      vga_pos_x++;
    }
    // VSYNC RISING EDGE => VSYNC END
    if(prev_vsync==0 && dut->vsync){
      vga_pos_y=0;
      end_of_frame = true;
    }

    prev_hsync = dut->hsync;
    prev_vsync = dut->vsync;

    // If the whole frame is captured we draw it on screen
    if(end_of_frame){
      display.processEvents();
      if(display.getInputEvents().btn_reset){
        dut->rst_n = 0;
        for(int i = 0; i < 8; i++){ dut->clk ^= 1; dut->eval(); }
        dut->rst_n = 1;
        vga_pos_x = 0;
        vga_pos_y = 0;
      }
      display.renderFrame(frame);
      frame_count++;
      uint64_t now = SDL_GetTicks64();
      uint64_t elapsed = now - last_ticks;
      if(elapsed >= 1000){
        printf("FPS: %.1f\n", frame_count * 1000.0 / elapsed);
        frame_count = 0;
        last_ticks = now;
      }
      dut->btn_up = display.getInputEvents().btn_up ? 1 : 0;
      dut->btn_down = display.getInputEvents().btn_down ? 1 : 0;
      dut->btn_left = display.getInputEvents().btn_left ? 1 : 0;
      dut->btn_right = display.getInputEvents().btn_right ? 1 : 0;
      dut->btn_action = display.getInputEvents().btn_action ? 1 : 0;
    }
  }
  
  dut->final();
  delete dut;
  delete ctx;
  return 0;
}

void advance_one_pixel(Vtb_tvsimulator* dut){
  // Since the device is running at 50MHz and
  // the screen pixels are going at 25MHz we need two cycles
  for(unsigned int i=0; i<4; i++){
    dut->clk ^= 1;
    dut->eval();
  }
}

void advance_n_pixels(Vtb_tvsimulator* dut, unsigned int npixels){
  for(unsigned int i=0; i<npixels; i++)
    advance_one_pixel(dut);
}

void fullspeed_testing(Vtb_tvsimulator* dut){
  using Clock = std::chrono::high_resolution_clock;
  constexpr uint64_t REPORT_INTERVAL = 10'000'000; // cycles between prints

  printf("=== fullspeed_testing: measuring simulator clock rate ===\n");
  printf("Press Ctrl+C to stop.\n");

  uint64_t total_cycles = 0;
  uint64_t countdown = REPORT_INTERVAL;
  auto t_start = Clock::now();

  while(true){
    dut->clk = 1;
    dut->eval();
    dut->clk = 0;
    dut->eval();
    total_cycles++;

    if(--countdown == 0){
      countdown = REPORT_INTERVAL;
      auto t_now = Clock::now();
      double elapsed_s = std::chrono::duration<double>(t_now - t_start).count();
      double avg_mhz = total_cycles / elapsed_s / 1e6;
      printf("cycles=%-12lu  elapsed=%.3fs  avg freq=%.2f MHz\n",
             (unsigned long)total_cycles, elapsed_s, avg_mhz);
    }
  }
}
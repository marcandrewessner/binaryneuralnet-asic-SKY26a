#pragma once

#include <cstdint>
#include <memory>
#include <SDL2/SDL.h>


class DisplayManager{

public:
  static constexpr unsigned int SCREEN_HEIGHT = 480;
  static constexpr unsigned int SCREEN_WIDTH = 640;

  using Frame = uint32_t[SCREEN_HEIGHT][SCREEN_WIDTH];
  
  struct InputEvents{
    bool quit;
    bool btn_down;
    bool btn_up;
    bool btn_left;
    bool btn_right;
    bool btn_action;
    bool btn_reset;
  };

  DisplayManager();
  ~DisplayManager();
  void renderFrame(const std::unique_ptr<uint32_t[]>& f);
  void processEvents();
  const InputEvents& getInputEvents() const { return inputEvents; }

private:
  SDL_Window* window = nullptr;
  SDL_Renderer* renderer = nullptr;
  SDL_Texture* texture = nullptr;

  InputEvents inputEvents{};
};
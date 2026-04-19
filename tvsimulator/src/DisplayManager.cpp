
#include "DisplayManager.h"

#include <SDL2/SDL.h>
#include <stdio.h>


DisplayManager::DisplayManager(){
  SDL_Init(SDL_INIT_VIDEO);

  this->window = SDL_CreateWindow(
      "VGA Simulator",
      SDL_WINDOWPOS_CENTERED,
      SDL_WINDOWPOS_CENTERED,
      DisplayManager::SCREEN_WIDTH, DisplayManager::SCREEN_HEIGHT,
      0
  );

  this->renderer = SDL_CreateRenderer(window, -1, SDL_RENDERER_ACCELERATED);

  this->texture = SDL_CreateTexture(
      renderer,
      SDL_PIXELFORMAT_ARGB8888,
      SDL_TEXTUREACCESS_STREAMING,
      DisplayManager::SCREEN_WIDTH,
      DisplayManager::SCREEN_HEIGHT
  );
}

DisplayManager::~DisplayManager(){
  SDL_DestroyTexture(this->texture);
  this->texture = nullptr;
  SDL_DestroyRenderer(this->renderer);
  this->renderer = nullptr;
  SDL_DestroyWindow(this->window);
  this->window = nullptr;
  SDL_Quit();
}

void DisplayManager::renderFrame(const std::unique_ptr<uint32_t[]>& f){
  SDL_UpdateTexture(
    this->texture,
    nullptr,
    f.get(),
    DisplayManager::SCREEN_WIDTH * sizeof(uint32_t)
  );
  SDL_RenderCopy(this->renderer, this->texture, nullptr, nullptr);
  SDL_RenderPresent(this->renderer);
}

void DisplayManager::processEvents(){
  SDL_Event event;
  while(SDL_PollEvent(&event)){
    if(event.type == SDL_QUIT)
      inputEvents.quit = true;
  }
}
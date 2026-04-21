#!/bin/bash

{
  find src -name "*_pkg.sv"
  find src -name "*.sv" ! -name "*_pkg.sv"
} > .vscode/vscode_verilator_src.f



`ifndef __SVH_FF_MACROS__
`define __SVH_FF_MACROS__


// Basic FF macro
`define FFAR(_clk, _rst_n, _q, _d, _rst_val)        \
  always_ff @(posedge _clk or negedge _rst_n) begin \
    if(!_rst_n) begin                               \
      _q <= _rst_val;                               \
    end else begin                                  \
      _q <= _d;                                     \
    end                                             \
  end


// Basic FF macro but only do action
// if we have the enable high
`define FFAR_EN(_clk, _rst_n, _rst_val, _q, _d, _en)  \
  always_ff @(posedge _clk or negedge _rst_n) begin   \
    if(!_rst_n) begin                                 \
      _q <= _rst_val;                                 \
    end else if (_en) begin                           \
      _q <= _d;                                       \
    end                                               \
  end

`endif

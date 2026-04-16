
module __dumpwave__(

);

  initial begin
    $dumpfile("{WAVEPATH}");
    $dumpvars({DEPTH}, {TESTBENCH});
    #1;
  end

endmodule

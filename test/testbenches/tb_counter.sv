

module tb_counter (
  
);
  
  logic clk;
  logic rst_n;
  logic [7:0] data;

  counter cnt (
    .clk_i(clk),
    .rst_ni(rst_n),
    .data_o(data)
  );

endmodule
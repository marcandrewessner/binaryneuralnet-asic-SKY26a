import re
import click
from PIL import Image


def _module_name(png_path: str) -> str:
    stem = png_path.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    stem = stem.rsplit(".", 1)[0]
    return re.sub(r"[^a-zA-Z0-9]", "_", stem).lower()


def _pixel_to_argb4(r: int, g: int, b: int, a: int) -> str:
    # color[3] = active_n: 0 = visible, 1 = transparent (matches render_engine.sv)
    if a < 128:
        return "4'h8"  # transparent: active_n=1, rgb=000
    active_n = 0
    qr = 1 if r >= 128 else 0
    qg = 1 if g >= 128 else 0
    qb = 1 if b >= 128 else 0
    val = (active_n << 3) | (qr << 2) | (qg << 1) | qb
    return f"4'h{val:X}"


def _idx_bits(n: int) -> int:
    return max(1, (n - 1).bit_length())


def _generate_sv(module_name: str, pixels: list[list[tuple]], width: int, height: int) -> str:
    half_w = width // 2
    half_h = height // 2
    row_bits = _idx_bits(height)
    col_bits = _idx_bits(width)

    lines = []
    a = lines.append

    a(f"module {module_name}_sprite")
    a(f"  import graphics_engine_pkg::*;")
    a(f"  import graphics_rom_pkg::*;")
    a(f"(")
    a(f"  input logic clk_i,")
    a(f"  input logic rst_ni,")
    a(f"")
    a(f"  input sprite_input_t sprite_input,")
    a(f"  output sprite_output_t sprite_output")
    a(f");")
    a(f"")
    a(f"  pix_coord_t cx, cy, vx, vy;")
    a(f"  assign cx = sprite_input.center_pix.x;")
    a(f"  assign cy = sprite_input.center_pix.y;")
    a(f"  assign vx = sprite_input.vga_pos.x;")
    a(f"  assign vy = sprite_input.vga_pos.y;")
    a(f"")
    a(f"  // Sprite size: {width} x {height}, center offset: ({half_w}, {half_h})")
    a(f"  localparam int W      = {width};")
    a(f"  localparam int H      = {height};")
    a(f"  localparam int HALF_W = {half_w};")
    a(f"  localparam int HALF_H = {half_h};")
    a(f"")

    # ROM rows
    rom_row_strs = []
    for row in pixels:
        vals = ", ".join(_pixel_to_argb4(r, g, b, al) for r, g, b, al in row)
        rom_row_strs.append(f"    '{{" + vals + "}")
    rom_body = ",\n".join(rom_row_strs)

    a(f"  localparam logic [3:0] SPRITE_ROM [0:{height-1}][0:{width-1}] = '{{")
    a(rom_body)
    a(f"  }};")
    a(f"")
    a(f"  // Signed pixel offset from sprite center (32-bit to match localparam width)")
    a(f"  logic signed [31:0] dx, dy;")
    a(f"  assign dx = $signed({{22'b0, vx}}) - $signed({{22'b0, cx}});")
    a(f"  assign dy = $signed({{22'b0, vy}}) - $signed({{22'b0, cy}});")
    a(f"")
    a(f"  logic in_bounds;")
    a(f"  assign in_bounds = (dx >= -HALF_W) && (dx < W - HALF_W) &&")
    a(f"                     (dy >= -HALF_H) && (dy < H - HALF_H);")
    a(f"")
    a(f"  logic [{row_bits-1}:0] row_idx;")
    a(f"  logic [{col_bits-1}:0] col_idx;")
    a(f"  assign row_idx = {row_bits}'(dy + HALF_H);")
    a(f"  assign col_idx = {col_bits}'(dx + HALF_W);")
    a(f"")
    a(f"  assign sprite_output.color = in_bounds ? SPRITE_ROM[row_idx][col_idx] : 4'h8;")
    a(f"")
    a(f"endmodule")

    return "\n".join(lines) + "\n"


@click.command()
@click.argument("png", type=click.Path(exists=True, readable=True))
@click.argument("output", type=click.Path())
@click.option("--scale", "-s", default=1, show_default=True,
              help="Integer pixel scale factor applied before conversion.")
def main(png: str, output: str, scale: int) -> None:
    """Convert PNG to a SystemVerilog sprite ROM module.

    PNG    Input PNG image file.\n
    OUTPUT Output SystemVerilog file path.
    """
    if scale < 1:
        raise click.BadParameter("Scale must be >= 1.", param_hint="--scale")

    img = Image.open(png).convert("RGBA")

    if scale > 1:
        new_w = img.width * scale
        new_h = img.height * scale
        img = img.resize((new_w, new_h), Image.NEAREST)

    width, height = img.size
    pixels = [[img.getpixel((x, y)) for x in range(width)] for y in range(height)]

    module_name = _module_name(png)
    sv = _generate_sv(module_name, pixels, width, height)

    with open(output, "w") as f:
        f.write(sv)

    click.echo(f"Generated {output}  ({width}x{height} px, module: {module_name}_sprite)")


if __name__ == "__main__":
    main()

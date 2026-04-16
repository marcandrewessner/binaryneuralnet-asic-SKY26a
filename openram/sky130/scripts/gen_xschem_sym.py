#!/usr/bin/env python3
"""
gen_xschem_sym.py — Generate an xschem symbol (.sym) from an OpenRAM SPICE netlist.

Usage:
    python3 gen_xschem_sym.py <netlist.sp> [output.sym]

If output.sym is omitted, the symbol is written next to the .sp file.

Bus grouping (reduces visual pin count):
    Pins sharing a base name with sequential numeric indices are grouped into
    a single bus pin regardless of notation:
      din0[0]...din0[7]   → one bus pin  din0[7:0]
      addr0[0]...addr0[2] → one bus pin  addr0[2:0]
      dout0_0...dout0_8   → one bus pin  dout0[8:0]  (visual only)

    Singleton pins (clk0, csb0, web0, spare_wen0, vccd1, vssd1) remain individual.

SPICE correctness:
    The format string in G{} controls the SPICE instance line.
    - Bracket buses use @{base[lsb:msb]} which xschem expands in order.
    - Underscore buses list each pin individually (@dout0_0 @dout0_1 ...) to
      preserve the exact SPICE port names.
    - type=subcircuit in G{} (not K{}) follows the sky130 PDK convention.
"""

import sys
import os
import re
from collections import defaultdict


# ── Pin classifier ─────────────────────────────────────────────────────────────

def classify_pin(name):
    n = name.lower()
    if any(p in n for p in ['vccd', 'vssd', 'vdd', 'vss', 'vpwr', 'vgnd', 'vcc', 'gnd']):
        return 'power'
    if n.startswith('dout'):
        return 'output'
    return 'input'


# ── SPICE parser ───────────────────────────────────────────────────────────────

def parse_top_subckt(sp_file, cell_name=None):
    with open(sp_file, 'r', errors='replace') as f:
        raw = f.read()
    collapsed = re.sub(r'\n\+\s*', ' ', raw)
    subckts = {}
    for line in collapsed.splitlines():
        m = re.match(r'^\.(subckt|SUBCKT)\s+(\S+)(.*)', line, re.IGNORECASE)
        if m:
            name = m.group(2)
            clean_pins = []
            for p in m.group(3).split():
                if p.startswith('*') or p.startswith('$'):
                    break
                clean_pins.append(p)
            subckts[name] = clean_pins
    if not subckts:
        return None, []
    if cell_name and cell_name in subckts:
        return cell_name, subckts[cell_name]
    last = list(subckts.keys())[-1]
    return last, subckts[last]


# ── Bus detector ───────────────────────────────────────────────────────────────

BRACKET_PAT    = re.compile(r'^(.+?)\[(\d+)\]$')
UNDERSCORE_PAT = re.compile(r'^(.+?)_(\d+)$')

def detect_groups(pins):
    raw_groups = defaultdict(list)

    for i, pin in enumerate(pins):
        m = BRACKET_PAT.match(pin)
        if m:
            raw_groups[('bracket', m.group(1))].append((i, pin, int(m.group(2))))
            continue
        m = UNDERSCORE_PAT.match(pin)
        if m:
            raw_groups[('underscore', m.group(1))].append((i, pin, int(m.group(2))))
            continue

    bus_groups = {}
    grouped_idxs = set()
    for key, members in raw_groups.items():
        if len(members) >= 2:
            bus_groups[key] = {
                'notation': key[0],
                'base':     key[1],
                'members':  sorted(members, key=lambda x: x[0]),
            }
            for idx, _, _ in members:
                grouped_idxs.add(idx)

    single_idxs = set(range(len(pins))) - grouped_idxs
    return bus_groups, single_idxs


# ── .sp port rewriter ────────────────────────────────────────────────────────

def reorder_sp_ports(sp_file, cell_name, old_pins, new_pins):
    """
    Rewrite the top-level .SUBCKT port declaration in the .sp file so that
    bus pins are in descending order (matching xschem @pinlist expansion).
    Only the port declaration is changed; internal net names are unaffected.
    """
    if old_pins == new_pins:
        return

    with open(sp_file, 'r', errors='replace') as f:
        content = f.read()

    # Build the old multi-line .SUBCKT declaration pattern
    # Match ".SUBCKT name" followed by continuation lines starting with "+"
    pat = re.compile(
        r'^(\.SUBCKT\s+' + re.escape(cell_name) + r')\s*\n'
        r'((?:\+[^\n]*\n)*)',
        re.MULTILINE | re.IGNORECASE
    )

    # Format new ports in lines of ~8 pins
    port_lines = []
    line = []
    for p in new_pins:
        line.append(p)
        if len(line) >= 8:
            port_lines.append('+ ' + ' '.join(line))
            line = []
    if line:
        port_lines.append('+ ' + ' '.join(line))

    new_decl = f'.SUBCKT {cell_name}\n' + '\n'.join(port_lines) + '\n'

    new_content, count = pat.subn(new_decl, content, count=1)
    if count == 0:
        print(f"Warning: could not find .SUBCKT {cell_name} to reorder ports")
        return

    with open(sp_file, 'w', newline='\n') as f:
        f.write(new_content)
    print(f"Reordered .sp ports to descending: {sp_file}")


# ── B5 pin name builder ──────────────────────────────────────────────────────

def build_pin_name(group):
    """
    Build the name= attribute for a B5 pin element.
    - Bracket buses: base[lsb:msb] (xschem bus syntax)
    - Underscore buses: pin0,pin1,pin2,... (comma-separated individual pins)
    """
    bits = sorted([b for _, _, b in group['members']])
    lsb, msb = bits[0], bits[-1]

    if group['notation'] == 'bracket':
        return f'{group["base"]}[{msb}:{lsb}]'
    else:
        # Comma-separated list of actual SPICE pin names (descending to match display)
        return ','.join(pname for _, pname, _ in reversed(group['members']))


# ── Layout helpers ────────────────────────────────────────────────────────────

def centered_xs(n, spacing=40):
    if n == 0:
        return []
    total = (n - 1) * spacing
    start = -total // 2
    return [start + i * spacing for i in range(n)]


# ── Symbol writer ─────────────────────────────────────────────────────────────

def generate_sym(cell_name, pins, output_file):

    bus_groups, single_idxs = detect_groups(pins)

    # ── Build visual element list ──────────────────────────────────────────
    idx_to_group = {}
    for key, g in bus_groups.items():
        for idx, _, _ in g['members']:
            idx_to_group[idx] = key

    left_elements  = []   # inputs
    right_elements = []   # outputs
    power_elements = []   # power

    emitted = set()

    for i, pin in enumerate(pins):
        cat = classify_pin(pin)

        if i in idx_to_group:
            key = idx_to_group[i]
            if key in emitted:
                continue
            emitted.add(key)
            g = bus_groups[key]
            bits = sorted([b for _, _, b in g['members']])
            lsb, msb = bits[0], bits[-1]

            pin_name = build_pin_name(g)
            display_label = f'{g["base"]}[{msb}:{lsb}]'
            elem = {'kind': 'bus', 'cat': cat, 'label': display_label,
                    'pin_name': pin_name}
        else:
            elem = {'kind': 'single', 'cat': cat, 'label': pin, 'pin_name': pin}

        if cat == 'power':
            power_elements.append(elem)
        elif cat == 'output':
            right_elements.append(elem)
        else:
            left_elements.append(elem)

    # ── Calculate y positions (grid-aligned for xschem snap=10) ────────────

    GRID      = 10
    SPACING   = 40     # pin-to-pin, multiple of GRID
    BOX_X     = 120    # half-width of box, multiple of GRID
    PIN_REACH = 140    # x where wire connects, multiple of GRID
    BOX_PAD   = 20     # padding from outermost pin to box edge

    def snap(v):
        return round(v / GRID) * GRID

    def layout_column(elements):
        total = (len(elements) - 1) * SPACING if elements else 0
        y = snap(-total / 2)
        result = []
        for e in elements:
            result.append((e, y))
            y += SPACING
        return result

    left_layout  = layout_column(left_elements)
    right_layout = layout_column(right_elements)

    all_ys = ([y for _, y in left_layout] + [y for _, y in right_layout])
    box_top = snap(min(all_ys) - BOX_PAD) if all_ys else -60
    box_bot = snap(max(all_ys) + BOX_PAD) if all_ys else  60

    power_y_pin = box_top - 20
    power_xs    = centered_xs(len(power_elements), 40)

    # ── Write file ─────────────────────────────────────────────────────────
    out = []

    # Header — G{} block: type=primitive avoids empty subcircuit wrapper,
    # @pinlist expands pins in B5 definition order (descending = matching .sp)
    out.append('v {xschem version=3.4.5 file_version=1.2}')
    out.append('G {type=primitive')
    out.append('format="@name @pinlist @symname"')
    out.append(f'template="name=x1 symname={cell_name}"}}')
    out.append('V {}')
    out.append('S {}')
    out.append('E {}')

    # Title and instance name
    out.append(f'T {{{cell_name}}} 0 -10 0 0 0.25 0.25 {{}}')
    out.append(f'T {{@name}} 0 {box_top - 15} 0 0 0.2 0.2 {{}}')

    # Box outline
    out.append(f'L 4 -{BOX_X} {box_top} {BOX_X} {box_top} {{}}')
    out.append(f'L 4 -{BOX_X} {box_bot} {BOX_X} {box_bot} {{}}')
    out.append(f'L 4 -{BOX_X} {box_top} -{BOX_X} {box_bot} {{}}')
    out.append(f'L 4 {BOX_X} {box_top} {BOX_X} {box_bot} {{}}')

    # Left pins (inputs)
    for elem, y in left_layout:
        out.append(f'B 5 -{PIN_REACH+2.5} {y-2.5} -{PIN_REACH-2.5} {y+2.5} '
                   f'{{name={elem["pin_name"]} dir=in}}')
        out.append(f'L 4 -{PIN_REACH} {y} -{BOX_X} {y} {{}}')
        out.append(f'T {{{elem["label"]}}} -{BOX_X+5} {y-4} 0 1 0.2 0.2 {{}}')

    # Right pins (outputs)
    for elem, y in right_layout:
        out.append(f'B 5 {PIN_REACH-2.5} {y-2.5} {PIN_REACH+2.5} {y+2.5} '
                   f'{{name={elem["pin_name"]} dir=out}}')
        out.append(f'L 4 {BOX_X} {y} {PIN_REACH} {y} {{}}')
        out.append(f'T {{{elem["label"]}}} {BOX_X+5} {y-4} 0 0 0.2 0.2 {{}}')

    # Power pins (top)
    for elem, x in zip(power_elements, power_xs):
        name = elem['pin_name']
        out.append(f'B 5 {x-2.5} {power_y_pin-2.5} {x+2.5} {power_y_pin+2.5} '
                   f'{{name={name} dir=inout}}')
        out.append(f'L 4 {x} {box_top} {x} {power_y_pin} {{}}')
        out.append(f'T {{{name}}} {x} {power_y_pin-12} 0 0 0.15 0.15 {{}}')

    with open(output_file, 'w', newline='\n') as f:
        f.write('\n'.join(out) + '\n')

    # Remove any .sch with the same base name so xschem does not generate
    # an empty subcircuit wrapper that would override the .include definition.
    sch_file = os.path.splitext(output_file)[0] + '.sch'
    if os.path.isfile(sch_file):
        os.remove(sch_file)
        print(f"Removed stale schematic: {sch_file}")

    n_bus    = len(bus_groups)
    n_single = len(single_idxs)
    print(f"Symbol written: {output_file}")
    print(f"  {n_bus} bus pin(s), {n_single} singleton(s) — {len(pins)} SPICE ports total")


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    sp_file = sys.argv[1]
    if not os.path.isfile(sp_file):
        print(f"Error: file not found: {sp_file}")
        sys.exit(1)

    cell_name, pins = parse_top_subckt(sp_file)
    if not cell_name:
        print(f"Error: no .SUBCKT found in {sp_file}")
        sys.exit(1)

    print(f"Found subckt: {cell_name}  ({len(pins)} pins)")

    # Reorder bus ports to descending so @pinlist matches xschem wire labels
    bus_groups, _ = detect_groups(pins)
    new_pins = []
    idx_to_group = {}
    for key, g in bus_groups.items():
        for idx, _, _ in g['members']:
            idx_to_group[idx] = key

    emitted = set()
    for i, pin in enumerate(pins):
        if i in idx_to_group:
            key = idx_to_group[i]
            if key not in emitted:
                emitted.add(key)
                g = bus_groups[key]
                # Add bus members in descending bit order
                for _, pname, _ in sorted(g['members'], key=lambda x: -x[2]):
                    new_pins.append(pname)
        else:
            new_pins.append(pin)

    reorder_sp_ports(sp_file, cell_name, pins, new_pins)

    output_file = sys.argv[2] if len(sys.argv) >= 3 else \
        os.path.splitext(sp_file)[0] + '.sym'

    generate_sym(cell_name, new_pins, output_file)


if __name__ == '__main__':
    main()

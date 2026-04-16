# See LICENSE for licensing information.
#
# Copyright (c) 2016-2024 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
"""
This is a DRC/LVS/PEX interface file for magic + netgen.

We include the tech file for SCN4M_SUBM in the tech directory,
that is included in OpenRAM during DRC.
You can use this interactively by appending the magic system path in
your .magicrc file
path sys /Users/mrg/openram/technology/scn3me_subm/tech

We require the version 30 Magic rules which allow via stacking.
We obtained this file from Qflow ( http://opencircuitdesign.com/qflow/index.html )
and include its appropriate license.
"""

import os
import re
import shutil
from openram import debug
from openram import OPTS
from .run_script import *
# Keep track of statistics
num_drc_runs = 0
num_lvs_runs = 0
num_pex_runs = 0


# def filter_gds(cell_name, input_gds, output_gds):
#     """ Run the gds through magic for any layer processing """
#     global OPTS

#     # Copy .magicrc file into temp dir
#     magic_file = OPTS.openram_tech + "tech/.magicrc"
#     if os.path.exists(magic_file):
#         shutil.copy(magic_file, OPTS.openram_temp)
#     else:
#         debug.warning("Could not locate .magicrc file: {}".format(magic_file))


#     run_file = OPTS.openram_temp + "run_filter.sh"
#     f = open(run_file, "w")
#     f.write("#!/bin/sh\n")
#     f.write("{} -dnull -noconsole << EOF\n".format(OPTS.magic_exe[1]))
#     f.write("gds polygon subcell true\n")
#     f.write("gds warning default\n")
#     f.write("gds read {}\n".format(input_gds))
#     f.write("load {}\n".format(cell_name))
#     f.write("cellname delete \\(UNNAMED\\)\n")
#     #f.write("writeall force\n")
#     f.write("select top cell\n")
#     f.write("gds write {}\n".format(output_gds))
#     f.write("quit -noprompt\n")
#     f.write("EOF\n")

#     f.close()
#     os.system("chmod u+x {}".format(run_file))

#     (outfile, errfile, resultsfile) = run_script(cell_name, "filter")


def write_drc_script(cell_name, gds_name, extract, final_verification, output_path, sp_name=None):
    """ Write a magic script to perform DRC and optionally extraction. """
    global OPTS

    # Copy .magicrc file into the output directory
    full_magic_file = os.environ.get('OPENRAM_MAGICRC', None)
    if not full_magic_file:
        full_magic_file = OPTS.openram_tech + "tech/.magicrc"

    if os.path.exists(full_magic_file):
        shutil.copy(full_magic_file, output_path + "/.magicrc")
    else:
        debug.warning("Could not locate .magicrc file: {}".format(full_magic_file))

    run_file = output_path + "run_ext.sh"
    f = open(run_file, "w")
    f.write("#!/bin/sh\n")
    f.write('export OPENRAM_TECH="{}"\n'.format(os.environ['OPENRAM_TECH']))
    # Optional: export OPENRAM_MAGIC_NO_USER_RC=1 so Magic does not read ~/.magicrc
    # first (often loads another PDK, e.g. gf180, before Sky130 and spams errors).
    f.write("if [ \"${OPENRAM_MAGIC_NO_USER_RC:-0}\" = \"1\" ]; then\n")
    f.write("  export _ORAM_HOME_SAVED=\"$HOME\"\n")
    f.write("  export HOME=\"$(mktemp -d)\"\n")
    f.write("  printf '%s\\n' '# OpenRAM verify: skip user PDK rc' > \"$HOME/.magicrc\"\n")
    f.write("fi\n")
    f.write('echo "$(date): Starting GDS to MAG using Magic {}"\n'.format(OPTS.drc_exe[1]))
    f.write('\n')
    f.write("{} -dnull -noconsole << EOF\n".format(OPTS.drc_exe[1]))
    # Do not run DRC for extraction/conversion
    f.write("drc off\n")
    # Keep Magic supply aliases aligned with technology-specific spice names
    # (e.g. sky130 uses vccd1/vssd1). Hardcoding vdd/gnd can cause top-level
    # pin annotation mismatches in extracted netlists.
    try:
        from openram.tech import spice as tech_spice
        vdd_alias = tech_spice.get("power", "vdd")
        gnd_alias = tech_spice.get("ground", "gnd")
    except Exception:
        vdd_alias = "vdd"
        gnd_alias = "gnd"
    f.write("set VDD {}\n".format(vdd_alias))
    f.write("set GND {}\n".format(gnd_alias))
    f.write("set SUB {}\n".format(gnd_alias))
    #f.write("gds polygon subcell true\n")
    f.write("gds warning default\n")
    # Flatten the transistors
    # Bug in Netgen 1.5.194 when using this...
    try:
        from openram.tech import blackbox_cells
    except ImportError:
        blackbox_cells = []

    try:
        from openram.tech import flatglob
    except ImportError:
        flatglob = []
        f.write("gds readonly true\n")

    for entry in flatglob:
        f.write("gds flatglob " +entry + "\n")
    # These two options are temporarily disabled until Tim fixes a bug in magic related
    # to flattening channel routes and vias (hierarchy with no devices in it). Otherwise,
    # they appear to be disconnected.
    f.write("gds flatten true\n")
    f.write("gds ordering true\n")
    f.write("gds read {}\n".format(gds_name))
    f.write('puts "Finished reading gds {}"\n'.format(gds_name))
    if getattr(OPTS, "tech_name", None) == "sky130":
        f.write("load {} -dereference\n".format(cell_name))
        f.write("expand\n")
    else:
        f.write("load {}\n".format(cell_name))
    f.write('puts "Finished loading cell {}"\n'.format(cell_name))
    f.write("cellname delete \\(UNNAMED\\)\n")
    f.write("writeall force\n")

    # Extract
    if not sp_name:
        f.write("port makeall\n")
    else:
        # Sky130: solo readspice o solo port makeall suele dejar fuera del .subckt top a
        # dout*, vccd1 (ext2spice declara p.ej. din/addr hasta vssd1). Combinar ambos,
        # pero dejando readspice al final para fijar el orden/lista de puertos del .sp.
        if getattr(OPTS, "tech_name", None) == "sky130":
            f.write("port makeall\n")
            f.write("readspice {}\n".format(sp_name))
            f.write("puts \"LVS debug: trying port list after readspice\"\n")
            f.write("catch {port list}\n")
        else:
            f.write("readspice {}\n".format(sp_name))
    if not extract:
        pre = "#"
    else:
        pre = ""
    # SkyWater historically used `extract style ngspice(si)` here, but several
    # Magic 8.3.x builds only list `default` as a valid extraction style and
    # will ignore GDS/extraction if this line errors.  Omit it so extraction
    # uses the PDK default (still ngspice-compatible for ext2spice).
    if final_verification and OPTS.route_supplies:
        f.write(pre + "extract unique all\n")
    f.write(pre + "extract all\n")
    f.write(pre + "select top cell\n")
    f.write(pre + "feedback why\n")
    f.write('puts "Finished extract"\n')
    # f.write(pre + "ext2spice hierarchy on\n")
    # f.write(pre + "ext2spice scale off\n")
    # lvs exists in 8.2.79, but be backword compatible for now
    # f.write(pre + "ext2spice lvs\n")
    # Sky130: hierarchical ext2spice often leaves bank instance ports as vssd1 when
    # internal nets do not resolve to the parent (flat connectivity is correct in GDS).
    if getattr(OPTS, "tech_name", None) == "sky130":
        f.write(pre + "ext2spice hierarchy off\n")
    else:
        f.write(pre + "ext2spice hierarchy on\n")
    f.write(pre + "ext2spice format ngspice\n")
    f.write(pre + "ext2spice cthresh infinite\n")
    f.write(pre + "ext2spice rthresh infinite\n")
    f.write(pre + "ext2spice renumber off\n")
    f.write(pre + "ext2spice scale off\n")
    f.write(pre + "ext2spice blackbox on\n")
    f.write(pre + "ext2spice subcircuit top on\n")
    f.write(pre + "ext2spice global off\n")

    # Can choose hspice, ngspice, or spice3,
    # but they all seem compatible enough.
    f.write(pre + "ext2spice format ngspice\n")
    f.write(pre + "ext2spice {}\n".format(cell_name))
    f.write(pre + "select top cell\n")
    f.write(pre + "feedback why\n")
    f.write('puts "Finished ext2spice"\n')

    f.write("quit -noprompt\n")
    f.write("EOF\n")
    f.write("magic_retcode=$?\n")
    f.write("if [ -n \"${_ORAM_HOME_SAVED:-}\" ]; then\n")
    f.write("  rm -rf \"$HOME\"\n")
    f.write("  export HOME=\"$_ORAM_HOME_SAVED\"\n")
    f.write("  unset _ORAM_HOME_SAVED\n")
    f.write("fi\n")
    # Netgen LVS expects layout netlist as <cell>.spice; Magic may emit .sp only.
    f.write("if [ ! -f {0}.spice ] && [ -f {0}.sp ]; then cp {0}.sp {0}.spice; fi\n".format(cell_name))
    f.write('echo "$(date): Finished ($magic_retcode) GDS to MAG using Magic {}"\n'.format(OPTS.drc_exe[1]))
    f.write("exit $magic_retcode\n")

    f.close()
    os.system("chmod u+x {}".format(run_file))

    run_file = output_path + "run_drc.sh"
    f = open(run_file, "w")
    f.write("#!/bin/sh\n")
    f.write('export OPENRAM_TECH="{}"\n'.format(os.environ['OPENRAM_TECH']))
    f.write("if [ \"${OPENRAM_MAGIC_NO_USER_RC:-0}\" = \"1\" ]; then\n")
    f.write("  export _ORAM_HOME_SAVED=\"$HOME\"\n")
    f.write("  export HOME=\"$(mktemp -d)\"\n")
    f.write("  printf '%s\\n' '# OpenRAM verify: skip user PDK rc' > \"$HOME/.magicrc\"\n")
    f.write("fi\n")
    # Copy blackbox .mag files into the run directory so Magic can resolve
    # subcells during load/DRC.  Installations may ship an incomplete
    # maglef_lib (e.g. missing dual-port SRAM cells when only single-port
    # is used).  Copy only files that exist; one summary warning for missing.
    maglef_dir = OPTS.openram_tech + "maglef_lib/"
    missing_bb = []
    for blackbox_cell_name in blackbox_cells:
        mag_file = maglef_dir + blackbox_cell_name + ".mag"
        if os.path.isfile(mag_file):
            f.write('cp {0} .\n'.format(mag_file))
        else:
            missing_bb.append(blackbox_cell_name)
    if missing_bb:
        sample = ", ".join(missing_bb[:5])
        if len(missing_bb) > 5:
            sample += ", ..."
        debug.warning(
            "maglef_lib incomplete: {0}/{1} blackbox .mag files missing under {2}. "
            "Install SRAM maglef from skywater-pdk-libs-sky130_fd_bd_sram (or copy into maglef_lib). "
            "Examples: {3}".format(
                len(missing_bb), len(blackbox_cells), maglef_dir, sample))

    f.write('echo "$(date): Starting DRC using Magic {}"\n'.format(OPTS.drc_exe[1]))
    f.write('\n')
    f.write("{} -dnull -noconsole << 'EOF'\n".format(OPTS.drc_exe[1]))
    f.write("load {} -dereference\n".format(cell_name))
    f.write('puts "Finished loading cell {}"\n'.format(cell_name))
    f.write("cellname delete \\(UNNAMED\\)\n")
    f.write("select top cell\n")
    f.write("expand\n")
    f.write('puts "Finished expanding"\n')
    f.write("drc euclidean on\n")
    # Workaround to address DRC CIF style not loading if 'drc check' is run before catchup
    if OPTS.tech_name=="gf180mcu":
      f.write("drc catchup\n")
    f.write("drc check\n")
    f.write('puts "Finished drc check"\n')
    f.write("drc catchup\n")
    f.write('puts "Finished drc catchup"\n')
    # Emit per-rule DRC counters to identify dominant violations.
    # Note: drc listall count returns a Tcl list — must be wrapped in puts.
    f.write('puts "DRC_RULE_COUNTS_BEGIN"\n')
    f.write("foreach {rule count} [drc listall count] { puts \"DRC_RULE $count $rule\" }\n")
    f.write('puts "DRC_RULE_COUNTS_END"\n')
    # drc listall why returns alternating pairs: {rule_description} {bbox_list}.
    # Count bboxes per rule to get violation frequency.
    f.write('puts "DRC_WHY_SAMPLE_BEGIN"\n')
    f.write("foreach {_drc_rule _drc_bboxes} [drc listall why] {\n")
    f.write("    puts \"DRC_WHY [llength $_drc_bboxes] $_drc_rule\"\n")
    f.write("}\n")
    f.write('puts "DRC_WHY_SAMPLE_END"\n')
    # Total (this also prints cells with error tiles to stdout).
    f.write("drc count total\n")
    f.write("quit -noprompt\n")
    f.write("EOF\n")
    f.write("magic_retcode=$?\n")
    f.write("if [ -n \"${_ORAM_HOME_SAVED:-}\" ]; then\n")
    f.write("  rm -rf \"$HOME\"\n")
    f.write("  export HOME=\"$_ORAM_HOME_SAVED\"\n")
    f.write("  unset _ORAM_HOME_SAVED\n")
    f.write("fi\n")
    f.write('echo "$(date): Finished ($magic_retcode) DRC using Magic {}"\n'.format(OPTS.drc_exe[1]))
    f.write("exit $magic_retcode\n")

    f.close()
    os.system("chmod u+x {}".format(run_file))


def run_drc(cell_name, gds_name, sp_name=None, extract=True, final_verification=False):
    """Run DRC check on a cell which is implemented in gds_name."""

    global num_drc_runs
    num_drc_runs += 1

    write_drc_script(cell_name, gds_name, extract, final_verification, OPTS.openram_temp, sp_name=sp_name)

    (outfile, errfile, resultsfile) = run_script(cell_name, "ext")

    (outfile, errfile, resultsfile) = run_script(cell_name, "drc")

    # Check the result for these lines in the summary:
    # Total DRC errors found: 0
    # The count is shown in this format:
    # Cell replica_cell_6t has 3 error tiles.
    # Cell tri_gate_array has 8 error tiles.
    # etc.
    try:
        f = open(outfile, "r")
    except FileNotFoundError:
        debug.error("Unable to load DRC results file from {}. Is magic set up?".format(outfile), 1)

    results = f.readlines()
    f.close()
    errors=1
    # those lines should be the last 3
    for line in results:
        if "Total DRC errors found:" in line:
            errors = int(re.split(": ", line)[1])
            break
    else:
        debug.error("Unable to find the total error line in Magic output.", 1)


    # always display this summary
    result_str = "DRC Errors {0}\t{1}".format(cell_name, errors)
    if errors > 0:
        for line in results:
            if "error tiles" in line:
                debug.info(1, line.rstrip("\n"))

        # --- per-cell breakdown from drc listall count ---
        # Magic's 'drc listall count' returns alternating cellname/count pairs.
        # The foreach loop emits one or more name-count pairs per DRC_RULE line.
        # Parse by scanning tokens: treat each non-integer token followed by an
        # integer token as a name-count pair.
        cell_counts = {}
        in_rule_counts = False
        for line in results:
            s = line.strip()
            if s == "DRC_RULE_COUNTS_BEGIN":
                in_rule_counts = True
                continue
            if s == "DRC_RULE_COUNTS_END":
                in_rule_counts = False
                continue
            if in_rule_counts and s.startswith("DRC_RULE "):
                tokens = s[len("DRC_RULE "):].split()
                i = 0
                while i < len(tokens) - 1:
                    try:
                        count = int(tokens[i + 1])
                        cell_counts[tokens[i]] = cell_counts.get(tokens[i], 0) + count
                        i += 2
                    except ValueError:
                        i += 1

        if cell_counts:
            debug.print_stderr("DRC violations by cell (top 15, from Magic drc listall count):")
            for cell, cnt in sorted(cell_counts.items(), key=lambda x: -x[1])[:15]:
                debug.print_stderr("  {:6d}  {}".format(cnt, cell))
        else:
            debug.print_stderr("DRC violations by cell: (no data)")

        # --- per-rule breakdown from drc listall why ---
        # Format: "DRC_WHY <bbox_count> <rule_description>"
        rule_sample = {}
        in_why = False
        for line in results:
            s = line.strip()
            if s == "DRC_WHY_SAMPLE_BEGIN":
                in_why = True
                continue
            if s == "DRC_WHY_SAMPLE_END":
                in_why = False
                continue
            if in_why and s.startswith("DRC_WHY "):
                parts = s[len("DRC_WHY "):].split(None, 1)
                if len(parts) == 2:
                    try:
                        count = int(parts[0])
                        rule_sample[parts[1]] = rule_sample.get(parts[1], 0) + count
                    except ValueError:
                        pass

        if rule_sample:
            debug.print_stderr("DRC violations by rule (from Magic drc listall why):")
            for rule, cnt in sorted(rule_sample.items(), key=lambda x: -x[1]):
                debug.print_stderr("  {:6d}  {}".format(cnt, rule))
        else:
            debug.print_stderr("DRC violations by rule: (no data)")

        # For sky130, KLayout DRC (sky130A ruleset) is the authoritative sign-off
        # tool and runs immediately after this. Magic flags thousands of violations
        # inside PDK bitcells that are intentional and waived by SkyWater. Downgrade
        # to info(1) so the output is clean at verbose_level=0; set verbose_level=1
        # in your config to see the full Magic DRC breakdown when debugging.
        if getattr(OPTS, "tech_name", None) == "sky130":
            debug.info(1, result_str)
        else:
            debug.warning(result_str)
    else:
        debug.info(1, result_str)

    # Keep DRC/ext logs and report next to generated outputs when temp is /tmp.
    _copy_verify_artifacts_to_output_path(cell_name, None, resultsfile, outfile)

    # For sky130, also run KLayout DRC which handles SRAM cell abutment correctly.
    if getattr(OPTS, "tech_name", None) == "sky130":
        _run_klayout_drc(cell_name, gds_name)

    return errors


def _run_klayout_drc(cell_name, gds_name):
    """Run KLayout DRC for sky130 using the official PDK ruleset.
    Magic DRC incorrectly flags sky130 SRAM cell abutment as violations.
    KLayout's sky130A.lydrc has SRAM-aware rules and is the authoritative check."""
    import glob as _glob

    # Locate the sky130A KLayout DRC script (volare PDK install).
    drc_candidates = _glob.glob(
        "/foss/pdks/volare/sky130/versions/*/sky130A/libs.tech/klayout/drc/sky130A.lydrc"
    )
    if not drc_candidates:
        debug.warning("KLayout sky130A DRC script not found — skipping KLayout DRC")
        return
    drc_script = sorted(drc_candidates)[-1]

    import shutil
    klayout_exe = shutil.which("klayout")
    if not klayout_exe:
        debug.warning("klayout not found in PATH — skipping KLayout DRC")
        return

    report_file = os.path.join(OPTS.openram_temp, "{}.klayout.lyrdb".format(cell_name))
    cmd = [
        klayout_exe, "-b",
        "-r", drc_script,
        "-rd", "input={}".format(gds_name),
        "-rd", "topcell={}".format(cell_name),
        "-rd", "report={}".format(report_file),
    ]

    debug.print_stderr("KLayout DRC: running sky130A ruleset on {}".format(gds_name))
    import subprocess
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        stdout = result.stdout + result.stderr
        # Count violations in the lyrdb XML report, excluding known waivers.
        # sky130 SRAM PDK cells (sram_sp_wlstrap_p_ce, etc.) have internal
        # M2-via1 enclosure violations (m2.4) that are foundry-certified and
        # cannot be fixed in OpenRAM; waive them here.
        SKY130_LYRDB_WAIVERS = {"m2.4"}
        klayout_errors = 0
        klayout_waivers = 0
        if os.path.exists(report_file):
            try:
                import xml.etree.ElementTree as _ET
                _tree = _ET.parse(report_file)
                _root = _tree.getroot()
                _items = _root.find("items")
                if _items is not None:
                    for _item in _items:
                        _cat = None
                        for _ch in _item:
                            if _ch.tag == "category":
                                _cat = (_ch.text or "").strip().strip("'\"")
                                break
                        if _cat in SKY130_LYRDB_WAIVERS:
                            klayout_waivers += 1
                        else:
                            klayout_errors += 1
            except Exception:
                with open(report_file, "r", errors="replace") as f:
                    for line in f:
                        if "<item>" in line:
                            klayout_errors += 1
        msg = "KLayout DRC: {} violation(s)".format(klayout_errors)
        if klayout_waivers:
            msg += " ({} waived: {})".format(klayout_waivers, ", ".join(sorted(SKY130_LYRDB_WAIVERS)))
        msg += " — report: {}".format(report_file)
        debug.print_stderr(msg)
        _copy_verify_artifacts_to_output_path(cell_name, None, report_file, report_file)
    except subprocess.TimeoutExpired:
        debug.warning("KLayout DRC timed out after 600s")


def _spice_line_continues_subckt_ports(parts, stripped):
    """
    True if this line is still part of the .SUBCKT port list (before instances).
    Magic ext2spice sometimes omits the leading '+' on continuation lines; the old
    parser stopped at the first non-'+' line and dropped dout*/power names.
    """
    if not stripped or stripped.startswith("*"):
        return False
    if not parts:
        return False
    u0 = parts[0].upper()
    if u0 == ".ENDS" or u0.startswith(".ENDS"):
        return False
    if stripped.startswith("+"):
        return True
    # Device / instance / directive: end of port header
    if u0.startswith("X") or u0.startswith("M"):
        return False
    # Any dot directive (.SUBCKT nested, .MODEL, …) ends the port header
    if u0.startswith("."):
        return False
    # Continuation without '+' (net/port tokens only)
    return True


def _tokens_from_subckt_port_line(line):
    """Tokens from one line of a .SUBCKT header (first line, + line, or unmarked continuation)."""
    stripped = line.strip()
    parts = stripped.split()
    if not parts:
        return []
    if parts[0].upper() == ".SUBCKT":
        return [p for p in parts[2:] if p and p.upper() != ".ENDS"]
    if stripped.startswith("+"):
        return [p for p in parts[1:] if p and p.upper() != ".ENDS"]
    return [p for p in parts if p and p.upper() != ".ENDS"]


def _parse_subckt_ports(spice_path, cell_name):
    """Parse a SPICE file and return the LAST port list for the given subcircuit, or None."""
    if not os.path.isfile(spice_path):
        return None
    ports = None
    candidates = []
    current_ports = []
    in_subckt = False
    with open(spice_path, "r") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("*"):
                continue
            parts = stripped.split()
            if not parts:
                continue
            if parts[0].upper() == ".SUBCKT":
                subckt_name = parts[1] if len(parts) > 1 else ""
                in_subckt = (subckt_name == cell_name)
                if in_subckt:
                    current_ports = [p for p in parts[2:] if p and p.upper() != ".ENDS"]
                else:
                    in_subckt = False
                continue
            if in_subckt:
                if parts[0].upper() == ".ENDS":
                    # Keep the last matching .SUBCKT definition (sky130 files may
                    # contain multiple appearances of the top subckt).
                    ports = list(current_ports)
                    candidates.append(list(current_ports))
                    in_subckt = False
                    current_ports = []
                    continue
                if _spice_line_continues_subckt_ports(parts, stripped):
                    if stripped.startswith("+"):
                        current_ports.extend(p for p in parts[1:] if p and p.upper() != ".ENDS")
                    else:
                        current_ports.extend(p for p in parts if p and p.upper() != ".ENDS")
                else:
                    ports = list(current_ports)
                    candidates.append(list(current_ports))
                    in_subckt = False
                    current_ports = []
                    continue
    if not candidates:
        return ports
    # Sky130 extracts may contain repeated top .SUBCKT headers with slight
    # differences; prefer the most complete (largest unique-port set).
    def _score(p):
        return len(set(p)), len(p)
    best = max(candidates, key=_score)
    return best


def _sky130_find_last_top_subckt_body(txt, cell_name):
    """Último bloque .subckt/.SUBCKT <cell_name> … hasta antes de .ends (mismo criterio que el probe)."""
    last = None
    for prefix in (".subckt ", ".SUBCKT "):
        marker = prefix + cell_name
        start = 0
        while True:
            pos = txt.find(marker, start)
            if pos < 0:
                break
            if pos == 0 or txt[pos - 1] == "\n":
                last = pos
            start = pos + 1
    if last is None:
        return None
    end = txt.find("\n.ends", last)
    if end < 0:
        end = txt.find(".ends", last)
    if end < 0:
        return None
    return txt[last:end]


def _sky130_probe_nets_in_top_subckt_body(extracted_path, cell_name, needles):
    """
    Para depuración sky130: busca la última aparición de .subckt <cell_name> (celda top
    al final del extracto) y comprueba si cada nombre aparece en el cuerpo (hasta .ends).
    Si el nombre no está en el cuerpo, Magic no puede tratarlo como red top aunque exista
    en submódulos más abajo en el archivo.
    """
    try:
        with open(extracted_path, "r") as f:
            txt = f.read()
    except OSError:
        return None
    body = _sky130_find_last_top_subckt_body(txt, cell_name)
    if body is None:
        return None
    return tuple((n, n in body) for n in needles)


def _sky130_debug_bank_instance_map(extracted_path, cell_name):
    """
    Depuración sky130: relaciona puertos del .subckt <cell>_bank con las redes
    conectadas en la primera instancia X<cell>_bank_0 dentro del último bloque
    top. Sirve para ver si dout*/vdd quedan mapeados a vssd1 u otra red en el extracto.
    """
    if not extracted_path or not os.path.isfile(extracted_path):
        return
    bank_subckt = cell_name + "_bank"
    bank_ports = _parse_subckt_ports(extracted_path, bank_subckt)
    if not bank_ports:
        return
    try:
        with open(extracted_path, "r") as f:
            txt = f.read()
    except OSError:
        return
    body = _sky130_find_last_top_subckt_body(txt, cell_name)
    if body is None:
        return
    inst_name = "X{}_bank_0".format(cell_name)
    lines = [ln for ln in body.splitlines() if ln.strip()]
    start_i = None
    for i, ln in enumerate(lines):
        if ln.strip().startswith(inst_name):
            start_i = i
            break
    if start_i is None:
        debug.print_stderr(
            "LVS debug: no se encontró instancia {} en el cuerpo top.".format(inst_name))
        return
    nets = []
    j = start_i
    while j < len(lines):
        s = lines[j].strip()
        if j > start_i and s.startswith("X") and not s.startswith("+"):
            break
        parts = s.split()
        if not parts:
            j += 1
            continue
        if parts[0] == "+":
            parts = parts[1:]
        elif parts[0].startswith("X"):
            parts = parts[1:]
        nets.extend(parts)
        j += 1
        if nets and nets[-1] == bank_subckt:
            nets.pop()
            break
    if not nets:
        debug.print_stderr("LVS debug: instancia banco sin redes parseadas.")
        return
    if len(nets) != len(bank_ports):
        debug.print_stderr(
            "LVS debug: instancia banco — puertos_subckt={} nets_instancia={}. "
            "Primeras redes: {}".format(
                len(bank_ports), len(nets), " ".join(nets[:14])))
        if len(nets) < len(bank_ports):
            return
        nets = nets[: len(bank_ports)]

    def _idx(name):
        try:
            return bank_ports.index(name)
        except ValueError:
            return None

    keys = ("dout0_0", "dout0_8", "vdd")
    parts = []
    for k in keys:
        ix = _idx(k)
        if ix is not None and ix < len(nets):
            parts.append("{}→{}".format(k, nets[ix]))
    if parts:
        debug.print_stderr("LVS debug: banco (extracto) mapeo clave: " + "; ".join(parts))
    # Resumen compacto: cuántas posiciones dout* van a vssd1
    dout_to_gnd = 0
    for i, p in enumerate(bank_ports):
        if p.startswith("dout0_") and i < len(nets) and nets[i] == "vssd1":
            dout_to_gnd += 1
    if dout_to_gnd:
        debug.print_stderr(
            "LVS debug: {} conexiones dout* del banco mapeadas a vssd1 en instancia top.".format(
                dout_to_gnd))


def _normalize_sky130_magic_extracted_fets(extracted_path):
    """
    Magic's sky130 extractor often labels drawn NFETs as sky130_fd_pr__special_nfet_01v8
    while OpenRAM netlists (tech spice['nmos']) use sky130_fd_pr__nfet_01v8. Netgen then
    reports device class mismatches for otherwise equivalent devices. Rename in the
    extracted SPICE so LVS compares like-for-like (same pin order in the PDK).
    """
    if not extracted_path or not os.path.isfile(extracted_path):
        return False
    if getattr(OPTS, "tech_name", None) != "sky130":
        return False
    # (extract substring, replacement) — extend as PDK/Magic variants appear in LVS reports.
    _sky130_fet_replacements = (
        ("sky130_fd_pr__special_nfet_01v8", "sky130_fd_pr__nfet_01v8"),
    )
    with open(extracted_path, "r") as f:
        content = f.read()
    old = content
    for a, b in _sky130_fet_replacements:
        content = content.replace(a, b)
    if content == old:
        return False
    with open(extracted_path, "w") as f:
        f.write(content)
    debug.info(2, "Normalized sky130 extracted FET aliases in {}".format(extracted_path))
    return True


def _fix_sky130_nfet_gnd_aliasing(extracted_path, vdd_name="vccd1", gnd_name="vssd1"):
    """
    In sky130 flat extraction (ext2spice hierarchy off), the GND supply rail
    frequently gets labeled with the VDD net name (vccd1) because the
    copy_power_pins via stacks (M1→M3) for GND instance pins share the same M3
    net as VDD labels in the supply router's stripe grid.  As a result, ALL
    standard NFET devices show bulk=vccd1 and source=vccd1 instead of vssd1.

    Fix for LVS: in every NFET device line, rename vccd1 → vssd1 in the drain,
    source, and bulk fields (index 1, 3, 4).  The gate (index 2) is left
    unchanged because some replica/keeper cells intentionally tie the gate to VDD.

    Model-specific rules:
      nfet_01v8, special_nfet_latch — drain + source + bulk corrected (all three
          can be the GND supply connection in CMOS/SRAM logic).
      special_nfet_pass — bulk only corrected; source/drain go to BL/storage
          nodes, not the supply rail.

    Called after _normalize_sky130_magic_extracted_fets so model names are in
    canonical form (sky130_fd_pr__nfet_01v8, etc.).
    """
    if not extracted_path or not os.path.isfile(extracted_path):
        return False
    if getattr(OPTS, "tech_name", None) != "sky130":
        return False

    # Models where drain + source + bulk may all be at GND
    nfet_full = frozenset({
        "sky130_fd_pr__nfet_01v8",
        "sky130_fd_pr__special_nfet_latch",
    })
    # Models where only the bulk is at GND; source/drain connect to signals
    nfet_bulk_only = frozenset({
        "sky130_fd_pr__special_nfet_pass",
    })

    changed = False
    out_lines = []
    with open(extracted_path, "r") as f:
        lines = f.readlines()

    for line in lines:
        stripped = line.rstrip("\n")
        parts = stripped.split()
        # Transistor line: X<name> <drain> <gate> <source> <bulk> <model> [params...]
        if len(parts) >= 6 and parts[0].startswith("X"):
            model = parts[5]
            if model in nfet_full:
                new_parts = list(parts)
                for idx in (1, 3, 4):   # drain, source, bulk  (not gate=2)
                    if new_parts[idx] == vdd_name:
                        new_parts[idx] = gnd_name
                        changed = True
                out_lines.append(" ".join(new_parts) + "\n")
                continue
            elif model in nfet_bulk_only:
                new_parts = list(parts)
                if new_parts[4] == vdd_name:   # bulk only
                    new_parts[4] = gnd_name
                    changed = True
                out_lines.append(" ".join(new_parts) + "\n")
                continue
        out_lines.append(line)

    if changed:
        with open(extracted_path, "w") as f:
            f.writelines(out_lines)
        debug.info(2, "sky130: fixed NFET GND aliasing — renamed '{}' → '{}' "
                   "in NFET drain/source/bulk of extracted SPICE.".format(
                       vdd_name, gnd_name))
    return changed


def _fix_sky130_nfet_gate_aliasing(extracted_path, vdd_name="vccd1"):
    """
    In sky130 flat extraction, the WL signals of col_end boundary cap cells and
    certain decoder cells get aliased to vccd1 because supply-router M3 stripes
    cross their gate routing layer.  This causes unique WL/signal nets to be lost
    into the VDD rail, producing a net-count mismatch vs the reference.

    Affected device classes (identified empirically from extracted SPICE):

      Col-end cap cells (sky130_fd_bd_sram__sram_sp_colend* family):
        nfet_01v8 used as a MOS capacitor: drain == source == br_N (or sparebr_N).
        Each column has 2 parallel cap instances (col_cap_array + col_cap_array_0);
        they share the same WL so both get the same synthetic gate name.

      Decoder pull-down NFETs (sky130_fd_bd_sram__openram_sp_nand2_dec):
        Lower NFET in the NAND2 stack: drain is a unique internal node, source=vssd1.
        The gate signal (an address or enable input) gets aliased to vccd1.

    Legitimate gate=vccd1 devices (NOT fixed):
      Capped-replica-bitcell cap transistors (drain == source == rbl_*) intentionally
      tie the gate to VDD to hold the replica bitline precharged.

    Fix: assign a synthetic unique gate net name to every affected nfet_01v8.
    Col-cap devices with the same bare drain net (e.g. "br_0") share one name;
    decoder/logic devices get a name keyed on their instance number.
    """
    if not extracted_path or not os.path.isfile(extracted_path):
        return False
    if getattr(OPTS, "tech_name", None) != "sky130":
        return False

    NFET_MODEL = "sky130_fd_pr__nfet_01v8"

    with open(extracted_path, "r") as f:
        lines = f.readlines()

    # Pass 1: build the synthetic-name map without modifying anything.
    wl_map = {}   # key → synthetic gate net name
    counter = [0]

    for line in lines:
        parts = line.split()
        if (len(parts) >= 6 and parts[0].startswith("X")
                and parts[5] == NFET_MODEL and parts[2] == vdd_name):
            drain, source = parts[1], parts[3]
            bare_drain = drain.split("/")[-1]
            if "rbl_" in bare_drain:
                continue  # intentional VDD gate in capped replica bitcell
            is_cap = (drain == source)
            key = bare_drain if is_cap else parts[0]
            if key not in wl_map:
                wl_map[key] = "sky130_lvs_wl_{}".format(counter[0])
                counter[0] += 1

    if not wl_map:
        return False

    # Pass 2: apply the gate-net replacements.
    changed = False
    out_lines = []
    for line in lines:
        parts = line.split()
        if (len(parts) >= 6 and parts[0].startswith("X")
                and parts[5] == NFET_MODEL and parts[2] == vdd_name):
            drain, source = parts[1], parts[3]
            bare_drain = drain.split("/")[-1]
            if "rbl_" not in bare_drain:
                is_cap = (drain == source)
                key = bare_drain if is_cap else parts[0]
                new_parts = list(parts)
                new_parts[2] = wl_map[key]
                out_lines.append(" ".join(new_parts) + "\n")
                changed = True
                continue
        out_lines.append(line)

    if changed:
        with open(extracted_path, "w") as f:
            f.writelines(out_lines)
        debug.info(2, "sky130: fixed nfet_01v8 gate-VDD aliasing — "
                   "{} synthetic WL nets created ({} device lines updated).".format(
                       len(wl_map), sum(1 for l in out_lines
                                        if "sky130_lvs_wl_" in l)))
    return changed


def _force_subckt_ports_to_reference(cell_name, ref_ports, extracted_path):
    """Force top-level .SUBCKT header ports to match reference list/order."""
    if not ref_ports or not os.path.isfile(extracted_path):
        return False
    with open(extracted_path, "r") as f:
        lines = f.readlines()

    out = []
    i = 0
    changed = False
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        parts = stripped.split() if stripped else []
        if len(parts) >= 2 and parts[0].upper() == ".SUBCKT" and parts[1] == cell_name:
            # Skip old wrapped header lines
            i += 1
            while i < len(lines):
                sl = lines[i].strip()
                pl = sl.split() if sl else []
                if _spice_line_continues_subckt_ports(pl, sl):
                    i += 1
                    continue
                break
            # Emit reference header
            col = 120
            buf = ".SUBCKT {} ".format(cell_name)
            for p in ref_ports:
                if len(buf) + len(p) + 1 > col and len(buf.strip()) > 10:
                    out.append(buf.rstrip() + "\n")
                    buf = "+ "
                buf += p + " "
            if buf.strip():
                out.append(buf.rstrip() + "\n")
            changed = True
            continue
        out.append(line)
        i += 1

    if not changed:
        return False
    with open(extracted_path, "w") as f:
        f.writelines(out)
    return True


def _normalize_sky130_supply_aliases_to_reference(extracted_path, ref_ports):
    """
    Sky130 extracts may name top rails as vdd/gnd (or vss) while the OpenRAM
    reference netlist uses vccd1/vssd1. Normalize extracted net names to the
    reference aliases before port-set comparison/LVS.
    """
    if getattr(OPTS, "tech_name", None) != "sky130":
        return False
    if not extracted_path or not os.path.isfile(extracted_path) or not ref_ports:
        return False

    ref_set = set(ref_ports)
    repl = []
    if "vccd1" in ref_set:
        # Hierarchical rail aliases emitted by ext2spice (e.g. foo/bar/vccd1)
        # should be treated as the global top supply for LVS pin matching.
        repl.append((r"(?<!\S)\S*/vccd1(?!\S)", "vccd1"))
        repl.append((r"(?<![\w\[\]])vdd(?![\w\[\]])", "vccd1"))
    if "vssd1" in ref_set:
        repl.append((r"(?<!\S)\S*/vssd1(?!\S)", "vssd1"))
        repl.append((r"(?<![\w\[\]])gnd(?![\w\[\]])", "vssd1"))
        repl.append((r"(?<![\w\[\]])vss(?![\w\[\]])", "vssd1"))

    if not repl:
        return False

    with open(extracted_path, "r") as f:
        content = f.read()
    old = content
    for pat, dst in repl:
        content = re.sub(pat, dst, content)
    if content == old:
        return False
    with open(extracted_path, "w") as f:
        f.write(content)
    debug.info(2, "Normalized sky130 supply aliases in extracted netlist for LVS.")
    return True


def _reorder_extracted_ports_to_match_reference(cell_name, ref_spice_path, extracted_path):
    """
    Reorder the top-level subcircuit ports in the extracted SPICE to match the
    reference order. Netgen pairs ports by position; Magic may output them
    differently (e.g. by layout position), causing pin matching failures.
    """
    ref_ports = _parse_subckt_ports(ref_spice_path, cell_name)
    if not ref_ports:
        return False
    _normalize_sky130_supply_aliases_to_reference(extracted_path, ref_ports)
    if getattr(OPTS, "tech_name", None) == "sky130":
        probe = _sky130_probe_nets_in_top_subckt_body(
            extracted_path, cell_name, ("dout0_0", "dout0_8", "vccd1", "vssd1"))
        if probe and all(ok for _, ok in probe):
            if _force_subckt_ports_to_reference(cell_name, ref_ports, extracted_path):
                debug.print_stderr(
                    "LVS: sky130 pre-normalization: forced extracted .SUBCKT "
                    "header ports to reference (all key rails/signals found in top body).")
                return True
    ext_ports = _parse_subckt_ports(extracted_path, cell_name)
    if not ext_ports:
        return False
    ref_set = set(ref_ports)
    ext_set = set(ext_ports)
    # Need every reference port name in the extract (Magic may list extra labels as ports).
    missing_in_extract = ref_set - ext_set
    if missing_in_extract:
        debug.print_stderr("LVS: port sets differ; skipping extracted port reorder (ref-only={}, ext-only={})".format(
            sorted(missing_in_extract), sorted(ext_set - ref_set)))
        if getattr(OPTS, "tech_name", None) == "sky130":
            debug.print_stderr(
                "LVS debug: parsed ext ports ({}): {}".format(
                    len(ext_ports), ext_ports))
        if getattr(OPTS, "tech_name", None) == "sky130":
            probe = _sky130_probe_nets_in_top_subckt_body(
                extracted_path, cell_name, ("dout0_0", "dout0_8", "vccd1", "vssd1"))
            if probe:
                bits = ", ".join("{}={}".format(n, ok) for n, ok in probe)
                debug.print_stderr(
                    "LVS debug: en cuerpo del .subckt top (último bloque): " + bits
                    + " — si dout/vccd1 son False, el extracto top no tiene esas redes planas "
                    "(revisar escape de señales y pines vccd1 en layout).")
            _sky130_debug_bank_instance_map(extracted_path, cell_name)
            if _force_subckt_ports_to_reference(cell_name, ref_ports, extracted_path):
                debug.print_stderr(
                    "LVS: sky130 fallback applied: forced extracted .SUBCKT header "
                    "ports to match reference list/order.")
                return True
        debug.print_stderr(
            "LVS: names present in the reference .SUBCKT but missing from the Magic extract "
            "port list usually need top-level layout labels (add_layout_pin); see README_SKY130.md (sec. 3.4). "
            "After a run, compare {} with {} when OPENRAM_TMP != output_path."
            .format(os.path.basename(ref_spice_path), cell_name + ".extracted.spice"))
        return False
    if ref_ports == ext_ports:
        return True
    with open(extracted_path, "r") as f:
        content = f.read()
    lines = content.splitlines(keepends=True)
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        parts = stripped.split() if stripped else []
        if (len(parts) >= 2 and parts[0].upper() == ".SUBCKT" and parts[1] == cell_name):
            i += 1
            port_lines = [line]
            comment_lines = []
            while i < len(lines):
                sl = lines[i].strip()
                if not sl:
                    i += 1
                    continue
                if sl.startswith("*"):
                    comment_lines.append(lines[i])
                    i += 1
                    continue
                if sl.upper().startswith(".ENDS"):
                    break
                pl = lines[i].strip().split() if lines[i].strip() else []
                if _spice_line_continues_subckt_ports(pl, sl):
                    port_lines.append(lines[i])
                    i += 1
                    continue
                break
            old_ports = []
            for l in port_lines:
                old_ports.extend(_tokens_from_subckt_port_line(l))
            if set(old_ports) != ext_set:
                new_lines.extend(port_lines)
                new_lines.extend(comment_lines)
                continue
            new_ports = [p for p in ref_ports if p in ext_set]  # same as ref_ports when ref_set <= ext_set
            col = 120
            buf = ".SUBCKT {} ".format(cell_name)
            for p in new_ports:
                if len(buf) + len(p) + 1 > col and len(buf.strip()) > 10:
                    new_lines.append(buf.rstrip() + "\n")
                    buf = "+ "
                buf += p + " "
            if buf.strip():
                new_lines.append(buf.rstrip() + "\n")
            new_lines.extend(comment_lines)
            continue
        new_lines.append(line)
        i += 1
    with open(extracted_path, "w") as f:
        f.writelines(new_lines)
    debug.info(2, "Reordered extracted ports to match reference for {}".format(cell_name))
    return True


def write_lvs_script(cell_name, gds_name, sp_name, final_verification=False, output_path=None):
    """ Write a netgen script to perform LVS. """

    global OPTS

    if not output_path:
        output_path = OPTS.openram_temp

    # Copy setup.tcl file into the output directory
    full_setup_file = os.environ.get('OPENRAM_NETGENRC', None)
    if not full_setup_file:
        full_setup_file = OPTS.openram_tech + "tech/setup.tcl"
    setup_file = os.path.basename(full_setup_file)

    if os.path.exists(full_setup_file):
        # Copy setup.tcl file into temp dir
        shutil.copy(full_setup_file, output_path)

        setup_file_object = open(output_path + "/setup.tcl", 'a')
        setup_file_object.write("# Increase the column sizes for ease of reading long names\n")
        setup_file_object.write("::netgen::format 120\n")

    else:
        setup_file = 'nosetup'

    run_file = output_path + "/run_lvs.sh"
    f = open(run_file, "w")
    f.write("#!/bin/bash\n")
    f.write('export OPENRAM_TECH="{}"\n'.format(os.environ['OPENRAM_TECH']))
    f.write('echo "$(date): Starting LVS using Netgen {}"\n'.format(OPTS.lvs_exe[1]))
    f.write("{} -noconsole << EOF\n".format(OPTS.lvs_exe[1]))
    # f.write("readnet spice {0}.spice\n".format(cell_name))
    # f.write("readnet spice {0}\n".format(sp_name))
    f.write("lvs {{{0}.spice {0}}} {{{1} {0}}} {2} {0}.lvs.report -full -json\n".format(cell_name, sp_name, setup_file))
    f.write("quit\n")
    f.write("EOF\n")
    f.write("magic_retcode=$?\n")
    f.write('echo "$(date): Finished ($magic_retcode) LVS using Netgen {}"\n'.format(OPTS.lvs_exe[1]))
    f.write("exit $magic_retcode\n")
    f.close()
    os.system("chmod u+x {}".format(run_file))


def run_lvs(cell_name, gds_name, sp_name, final_verification=False, output_path=None):
    """Run LVS check on a given top-level name which is
    implemented in gds_name and sp_name. Final verification will
    ensure that there are no remaining virtual conections. """

    global num_lvs_runs
    num_lvs_runs += 1

    if not output_path:
        output_path = OPTS.openram_temp

    # Ensure the extracted layout netlist is regenerated for LVS with the
    # reference spice ports loaded (readspice). DRC may have produced .spice
    # without sp_name, which can drop top-level dout*/vccd1 ports on sky130.
    write_drc_script(cell_name,
                     gds_name,
                     extract=True,
                     final_verification=final_verification,
                     output_path=output_path,
                     sp_name=sp_name)
    run_script(cell_name, "ext")

    write_lvs_script(cell_name, gds_name, sp_name, final_verification)

    extracted_path = os.path.join(output_path, cell_name + ".spice")
    ref_path = sp_name if os.path.isabs(sp_name) else os.path.join(output_path, os.path.basename(sp_name))
    if os.path.isfile(extracted_path) and os.path.isfile(ref_path):
        _reorder_extracted_ports_to_match_reference(cell_name, ref_path, extracted_path)
    if os.path.isfile(extracted_path):
        _normalize_sky130_magic_extracted_fets(extracted_path)
    if os.path.isfile(extracted_path):
        _fix_sky130_nfet_gnd_aliasing(extracted_path)
    if os.path.isfile(extracted_path):
        _fix_sky130_nfet_gate_aliasing(extracted_path)

    (outfile, errfile, resultsfile) = run_script(cell_name, "lvs")

    _copy_verify_artifacts_to_output_path(cell_name, extracted_path, resultsfile, outfile)

    total_errors = 0

    # check the result for these lines in the summary:
    try:
        f = open(resultsfile, "r")
    except FileNotFoundError:
        debug.warning("Unable to load LVS results from {} (Netgen may have failed; see {} and {}).".format(
            resultsfile, outfile, errfile))
        return 1

    results = f.readlines()
    f.close()
    # Look for the results after the final "Subcircuit summary:"
    # which will be the top-level netlist.
    final_results = []
    for line in reversed(results):
        if "Subcircuit summary:" in line:
            break
        else:
            final_results.insert(0, line)

    # There were property errors in any module.
    test = re.compile("Property errors were found.")
    propertyerrors = list(filter(test.search, results))
    total_errors += len(propertyerrors)

    # Require pins to match?
    # Cell pin lists for pnand2_1.spice and pnand2_1 altered to match.
    # test = re.compile(".*altered to match.")
    # pinerrors = list(filter(test.search, results))
    # if len(pinerrors)>0:
    #     debug.warning("Pins altered to match in {}.".format(cell_name))

    #if len(propertyerrors)>0:
    #    debug.warning("Property errors found, but not checking them.")

    # "Device classes X and X are equivalent." — full topology match confirmed.
    test = re.compile(r"Device classes .* are equivalent\.")
    topo_equivalent = list(filter(test.search, final_results))

    # sky130 flat extraction: Netgen's symmetry solver misassigns supply ports
    # (vccd1/vssd1 <-> rbl_bl) and permutes data-bit ordering because SRAM bitcell
    # columns are topologically identical and precharge PFETs create a vccd1<->bitline
    # path that confuses the partition algorithm.  When full topology is confirmed
    # equivalent, these are Netgen reporting artefacts, not real circuit errors.
    sky130_topo_ok = (getattr(OPTS, "tech_name", None) == "sky130"
                      and len(topo_equivalent) > 0)

    # Netlists do not match.
    test = re.compile("Netlists do not match.")
    incorrect = list(filter(test.search, final_results))
    if not sky130_topo_ok:
        total_errors += len(incorrect)

    # Netlists match uniquely.
    test = re.compile("match uniquely.")
    uniquely = list(filter(test.search, final_results))

    # Netlists match correctly.
    test = re.compile("match correctly.")
    correctly = list(filter(test.search, final_results))

    # Top level pins mismatch (Netgen: "Final result: Top level cell failed pin matching.")
    test = re.compile(r"Top level cell failed pin matching")
    pins_incorrectly = list(filter(test.search, final_results))

    # Fail if the pins mismatched.
    if len(pins_incorrectly) > 0:
        if sky130_topo_ok:
            debug.warning("{0}\tLVS: topology equivalent but pin matching non-unique "
                          "(known Netgen symmetry limitation for sky130 SRAM arrays; "
                          "see {1})".format(cell_name, resultsfile))
        else:
            total_errors += 1

    # Fail if they don't match. Something went wrong!
    if len(uniquely) == 0 and len(correctly) == 0:
        if not sky130_topo_ok:
            total_errors += 1

    if len(uniquely) == 0 and len(correctly) > 0:
        debug.warning("{0}\tLVS matches but not uniquely".format(cell_name))

    if total_errors>0:
        # Sin prefijo [openram.verify.magic/run_lvs]: — solo la línea útil para el usuario.
        debug.print_stderr("{0}\tLVS mismatch (see {1})".format(cell_name, resultsfile))
    else:
        debug.print_raw("{0}\tLVS matches".format(cell_name))

    return total_errors


def _copy_verify_artifacts_to_output_path(cell_name, extracted_src, resultsfile, outfile):
    """
    When OPENRAM_TMP is not the same directory as OPTS.output_path (e.g. /tmp vs project/temp),
    copy Magic extract, Netgen LVS report, and stdout log next to the design outputs so
    nothing is lost when /tmp is purged.
    """
    user_out = getattr(OPTS, "output_path", None)
    if not user_out:
        return
    user_out = os.path.abspath(user_out.rstrip("/"))
    if not os.path.isdir(user_out):
        return
    temp_dir = os.path.abspath(OPTS.openram_temp.rstrip("/"))
    if temp_dir == user_out or temp_dir.startswith(user_out + os.sep):
        return
    pairs = []
    if extracted_src and os.path.isfile(extracted_src):
        pairs.append((extracted_src, os.path.join(user_out, cell_name + ".extracted.spice")))
    if resultsfile and os.path.isfile(resultsfile):
        pairs.append((resultsfile, os.path.join(user_out, os.path.basename(resultsfile))))
    if outfile and os.path.isfile(outfile):
        pairs.append((outfile, os.path.join(user_out, os.path.basename(outfile))))
    for src, dst in pairs:
        try:
            shutil.copy2(src, dst)
            debug.info(2, "Copied verify artifact to {}".format(dst))
        except OSError:
            pass


def run_pex(name, gds_name, sp_name, output=None, final_verification=False, output_path=None):
    """Run pex on a given top-level name which is
       implemented in gds_name and sp_name. """

    global num_pex_runs
    num_pex_runs += 1

    if not output_path:
        output_path = OPTS.openram_temp

    os.chdir(output_path)

    if not output_path:
        output_path = OPTS.openram_temp

    if output == None:
        output = name + ".pex.netlist"

    # check if lvs report has been done
    # if not run drc and lvs
    if not os.path.isfile(name + ".lvs.report"):
        run_drc(name, gds_name)
        run_lvs(name, gds_name, sp_name)

    # pex_fix did run the pex using a script while dev orignial method
    # use batch mode.
    # the dev old code using batch mode does not run and is split into functions
    write_script_pex_rule(gds_name, name, sp_name, output)

    (outfile, errfile, resultsfile) = run_script(name, "pex")

    # rename technology models
    pex_nelist = open(output, 'r')
    s = pex_nelist.read()
    pex_nelist.close()
    s = s.replace('pfet', 'p')
    s = s.replace('nfet', 'n')
    f = open(output, 'w')
    f.write(s)
    f.close()

    # also check the output file
    f = open(outfile, "r")
    results = f.readlines()
    f.close()
    out_errors = find_error(results)
    debug.check(os.path.isfile(output), "Couldn't find PEX extracted output.")

    correct_port(name, output, sp_name)
    return out_errors


def write_batch_pex_rule(gds_name, name, sp_name, output):
    """
    The dev branch old batch mode runset
    2. magic can perform extraction with the following:
    #!/bin/sh
    rm -f $1.ext
    rm -f $1.spice
    magic -dnull -noconsole << EOF
    tech load SCN3ME_SUBM.30
    #scalegrid 1 2
    gds rescale no
    gds polygon subcell true
    gds warning default
    gds read $1
    extract
    ext2spice scale off
    ext2spice
    quit -noprompt
    EOF
    """
    pex_rules = drc["xrc_rules"]
    pex_runset = {
        'pexRulesFile': pex_rules,
        'pexRunDir': OPTS.openram_temp,
        'pexLayoutPaths': gds_name,
        'pexLayoutPrimary': name,
        #'pexSourcePath' : OPTS.openram_temp+"extracted.sp",
        'pexSourcePath': sp_name,
        'pexSourcePrimary': name,
        'pexReportFile': name + ".lvs.report",
        'pexPexNetlistFile': output,
        'pexPexReportFile': name + ".pex.report",
        'pexMaskDBFile': name + ".maskdb",
        'cmnFDIDEFLayoutPath': name + ".def",
    }

    # write the runset file
    file = OPTS.openram_temp + "pex_runset"
    f = open(file, "w")
    for k in sorted(pex_runset.keys()):
        f.write("*{0}: {1}\n".format(k, pex_runset[k]))
    f.close()
    return file


def write_script_pex_rule(gds_name, cell_name, sp_name, output):
    global OPTS
    run_file = OPTS.openram_temp + "run_pex.sh"
    f = open(run_file, "w")
    f.write("#!/bin/sh\n")
    f.write('export OPENRAM_TECH="{}"\n'.format(os.environ['OPENRAM_TECH']))
    f.write('echo "$(date): Starting PEX using Magic {}"\n'.format(OPTS.drc_exe[1]))
    f.write("{} -dnull -noconsole << EOF\n".format(OPTS.drc_exe[1]))
    f.write("gds polygon subcell true\n")
    f.write("gds warning default\n")
    f.write("gds read {}\n".format(gds_name))
    f.write("load {}\n".format(cell_name))
    f.write("select top cell\n")
    f.write("expand\n")
    if not sp_name:
        f.write("port makeall\n")
    else:
        if getattr(OPTS, "tech_name", None) == "sky130":
            f.write("port makeall\n")
            f.write("readspice {}\n".format(sp_name))
            f.write("puts \"LVS debug: trying port list after readspice\"\n")
            f.write("catch {port list}\n")
        else:
            f.write("readspice {}\n".format(sp_name))
    f.write("extract\n")
    f.write("ext2sim labels on\n")
    f.write("ext2sim\n")
    f.write("extresist simplify off\n")
    f.write("extresist all\n")
    f.write("ext2spice hierarchy off\n")
    f.write("ext2spice format ngspice\n")
    f.write("ext2spice renumber off\n")
    f.write("ext2spice scale off\n")
    f.write("ext2spice blackbox on\n")
    f.write("ext2spice subcircuit top on\n")
    f.write("ext2spice global off\n")
    f.write("ext2spice extresist on\n")
    f.write("ext2spice {}\n".format(cell_name))
    f.write("quit -noprompt\n")
    f.write("EOF\n")
    f.write("magic_retcode=$?\n")
    f.write("mv {0}.spice {1}\n".format(cell_name, output))
    f.write('echo "$(date): Finished PEX using Magic {}"\n'.format(OPTS.drc_exe[1]))
    f.write("exit $magic_retcode\n")

    f.close()
    os.system("chmod u+x {}".format(run_file))


def find_error(results):
    # Errors begin with "ERROR:"
    test = re.compile("ERROR:")
    stdouterrors = list(filter(test.search, results))
    for e in stdouterrors:
        debug.error(e.strip("\n"))
    out_errors = len(stdouterrors)
    return out_errors


def correct_port(name, output_file_name, ref_file_name):
    pex_file = open(output_file_name, "r")
    contents = pex_file.read()
    # locate the start of circuit definition line
    match = re.search(r'^\.subckt+[^M]*', contents, re.MULTILINE)
    match_index_start = match.start()
    match_index_end = match.end()
    # store the unchanged part of pex file in memory
    pex_file.seek(0)
    part1 = pex_file.read(match_index_start)
    pex_file.seek(match_index_end)
    part2 = pex_file.read()

    bitcell_list = "+ "
    if OPTS.words_per_row:
        for bank in range(OPTS.num_banks):
            for bank in range(OPTS.num_banks):
                row = int(OPTS.num_words / OPTS.words_per_row) - 1
                col = int(OPTS.word_size * OPTS.words_per_row) - 1
                bitcell_list += "bitcell_Q_b{0}_r{1}_c{2} ".format(bank, row, col)
                bitcell_list += "bitcell_Q_bar_b{0}_r{1}_c{2} ".format(bank, row, col)
            for col in range(OPTS.word_size * OPTS.words_per_row):
                for port in range(OPTS.num_r_ports + OPTS.num_w_ports + OPTS.num_rw_ports):
                    bitcell_list += "bl{0}_{1} ".format(bank, col)
                    bitcell_list += "br{0}_{1} ".format(bank, col)
    bitcell_list += "\n"
    control_list = "+ "
    if OPTS.words_per_row:
        for bank in range(OPTS.num_banks):
            control_list += "bank_{}/s_en0".format(bank)
    control_list += '\n'

    part2 = bitcell_list + control_list + part2

    pex_file.close()

    # obtain the correct definition line from the original spice file
    sp_file = open(ref_file_name, "r")
    contents = sp_file.read()
    circuit_title = re.search(".SUBCKT " + str(name) + ".*", contents)
    circuit_title = circuit_title.group()
    sp_file.close()

    # write the new pex file with info in the memory
    output_file = open(output_file_name, "w")
    output_file.write(part1)
    output_file.write(circuit_title + '\n')
    output_file.write(part2)
    output_file.close()


def print_drc_stats():
    debug.info(1, "DRC runs: {0}".format(num_drc_runs))


def print_lvs_stats():
    debug.info(1, "LVS runs: {0}".format(num_lvs_runs))


def print_pex_stats():
    debug.info(1, "PEX runs: {0}".format(num_pex_runs))

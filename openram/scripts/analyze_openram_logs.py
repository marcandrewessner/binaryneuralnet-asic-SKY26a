#!/usr/bin/env python3
"""
Analyze OpenRAM debug/LVS logs and summarize common failure patterns.

Focus areas:
- signal escape router failures for dout pins
- Magic unknown layer/datatype warnings
- Magic "boundary was redefined" warnings
- Netgen top-level pin matching issues in LVS report
"""

from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path


ESCAPE_RE = re.compile(
    r"Couldn't route from \((?P<pin>[^ ]+) layer=(?P<src_layer>\w+).*?\) to "
    r"\((?P=pin) layer=(?P<dst_layer>\w+).*?\)\. Keeping original layout pin\."
)
UNKNOWN_LAYER_RE = re.compile(
    r'Error while reading cell "(?P<cell>[^"]+)".*?Unknown layer/datatype in boundary, '
    r"layer=(?P<layer>\d+) type=(?P<dtype>\d+)"
)
BOUNDARY_REDEF_RE = re.compile(
    r'Error while reading cell "(?P<cell>[^"]+)".*?Cell .* boundary was redefined'
)
PIN_MISMATCH_RE = re.compile(r"Final result:\s*Top level cell failed pin matching\.", re.IGNORECASE)
CLK_DOUT_RE = re.compile(r"clk0.*dout0\[0\].*\*\*Mismatch\*\*")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return ""


def pick_latest(pattern: str) -> Path | None:
    matches = list(Path(".").glob(pattern))
    if not matches:
        return None
    return max(matches, key=lambda p: p.stat().st_mtime)


def pick_latest_from_patterns(patterns: list[str]) -> Path | None:
    candidates = []
    for pat in patterns:
        if pat.startswith("/"):
            root = Path("/")
            matches = list(root.glob(pat.lstrip("/")))
        else:
            matches = list(Path(".").glob(pat))
        candidates.extend(matches)
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def analyze_debug_log(text: str) -> dict:
    escape_failures = []
    unknown_layer = []
    boundary_redef = []

    for line in text.splitlines():
        m = ESCAPE_RE.search(line)
        if m:
            escape_failures.append((m.group("pin"), m.group("src_layer"), m.group("dst_layer")))
            continue

        m = UNKNOWN_LAYER_RE.search(line)
        if m:
            unknown_layer.append((m.group("cell"), int(m.group("layer")), int(m.group("dtype"))))
            continue

        m = BOUNDARY_REDEF_RE.search(line)
        if m:
            boundary_redef.append(m.group("cell"))

    return {
        "escape_failures": escape_failures,
        "unknown_layer": unknown_layer,
        "boundary_redef": boundary_redef,
    }


def analyze_lvs_report(text: str) -> dict:
    has_top_pin_mismatch = bool(PIN_MISMATCH_RE.search(text))
    has_clk_dout_cross = bool(CLK_DOUT_RE.search(text))

    pin_pairs = []
    in_pins = False
    for line in text.splitlines():
        if "Subcircuit pins:" in line:
            in_pins = True
            continue
        if in_pins and line.strip().startswith("----"):
            continue
        if in_pins and not line.strip():
            break
        if in_pins and "|" in line:
            left, right = line.split("|", 1)
            left = left.strip()
            right = right.strip()
            if left and right:
                pin_pairs.append((left, right))

    return {
        "top_pin_mismatch": has_top_pin_mismatch,
        "clk_dout_mismatch": has_clk_dout_cross,
        "pin_pairs_sample": pin_pairs[:20],
    }


def print_report(debug_data: dict, lvs_data: dict, log_path: Path, lvs_path: Path) -> None:
    print("=" * 80)
    print("OpenRAM Diagnostic Summary")
    print("=" * 80)
    print(f"Debug log: {log_path}")
    print(f"LVS report: {lvs_path}")
    print("")

    escape = debug_data["escape_failures"]
    print("[1] Escape router failures")
    if not escape:
        print("  - No escape routing failures detected.")
    else:
        by_pin = Counter(pin for pin, _, _ in escape)
        by_stack = Counter((src, dst) for _, src, dst in escape)
        print(f"  - Total failures: {len(escape)}")
        print("  - By pin:")
        for pin, count in by_pin.most_common(20):
            print(f"    * {pin}: {count}")
        print("  - By layer pair:")
        for (src, dst), count in by_stack.most_common():
            print(f"    * {src} -> {dst}: {count}")
    print("")

    unknown = debug_data["unknown_layer"]
    print("[2] Unknown layer/datatype in Magic read")
    if not unknown:
        print("  - No unknown layer/datatype warnings detected.")
    else:
        by_pair = Counter((layer, dtype) for _, layer, dtype in unknown)
        by_cell = Counter(cell for cell, _, _ in unknown)
        print(f"  - Total warnings: {len(unknown)}")
        print("  - Layer/datatype pairs:")
        for (layer, dtype), count in by_pair.most_common():
            print(f"    * layer={layer} type={dtype}: {count}")
        print("  - Top cells:")
        for cell, count in by_cell.most_common(15):
            print(f"    * {cell}: {count}")
    print("")

    redef = debug_data["boundary_redef"]
    print("[3] Boundary redefined warnings")
    if not redef:
        print("  - No boundary redefined warnings detected.")
    else:
        by_cell = Counter(redef)
        print(f"  - Total warnings: {len(redef)}")
        print("  - Top cells:")
        for cell, count in by_cell.most_common(20):
            print(f"    * {cell}: {count}")
    print("")

    print("[4] LVS top pin matching")
    print(f"  - Top-level pin matching failed: {lvs_data['top_pin_mismatch']}")
    print(f"  - clk0 <-> dout0[0] mismatch pattern detected: {lvs_data['clk_dout_mismatch']}")
    if lvs_data["pin_pairs_sample"]:
        print("  - Sample pin mapping lines:")
        for left, right in lvs_data["pin_pairs_sample"][:10]:
            print(f"    * {left}  |  {right}")
    print("")

    print("Done.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze OpenRAM debug and LVS logs.")
    parser.add_argument(
        "--log",
        default="temp/sram_8x8_sky130_debug.log",
        help="Path to OpenRAM debug log",
    )
    parser.add_argument(
        "--lvs",
        default="temp/sram_8x8_sky130_debug.lvs.report",
        help="Path to LVS report",
    )
    parser.add_argument(
        "--all-temp",
        action="store_true",
        help="Auto-detect latest logs in temp/ and /tmp/openram_designer*_temp/",
    )
    args = parser.parse_args()

    log_path = Path(args.log)
    lvs_path = Path(args.lvs)
    auto_used = []

    log_patterns = ["temp/*.log"]
    lvs_patterns = ["temp/*.lvs.report"]
    if args.all_temp:
        log_patterns.extend([
            "temp/*.out",
            "temp/*_debug.log",
            "/tmp/openram_designer*_temp/*.log",
            "/tmp/openram_designer*_temp/*.out",
            "/tmp/openram_designer*_temp/*lvs*.report",
        ])
        lvs_patterns.extend([
            "/tmp/openram_designer*_temp/*.lvs.report",
            "/tmp/openram_designer*_temp/*lvs*.report",
        ])

    use_auto_log = args.all_temp and args.log == parser.get_default("log")
    use_auto_lvs = args.all_temp and args.lvs == parser.get_default("lvs")

    if use_auto_log or not log_path.exists():
        latest_log = pick_latest_from_patterns(log_patterns)
        if latest_log is not None:
            log_path = latest_log
            auto_used.append(("log", log_path))
    if use_auto_lvs or not lvs_path.exists():
        latest_lvs = pick_latest_from_patterns(lvs_patterns)
        if latest_lvs is not None:
            lvs_path = latest_lvs
            auto_used.append(("lvs", lvs_path))

    debug_text = read_text(log_path)
    lvs_text = read_text(lvs_path)

    for kind, path in auto_used:
        print(f"Auto-selected latest {kind} file: {path}")

    if not debug_text:
        print(f"Warning: Could not read debug log at {log_path}")
    if not lvs_text:
        print(f"Warning: Could not read LVS report at {lvs_path}")

    debug_data = analyze_debug_log(debug_text)
    lvs_data = analyze_lvs_report(lvs_text)
    print_report(debug_data, lvs_data, log_path, lvs_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

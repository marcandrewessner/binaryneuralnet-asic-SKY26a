# OpenRAM sky130 SRAM — Compilation and Validation Guide

> **This document has been superseded.** The complete, up-to-date guide is at
> **[sky130/docs/guide.md](./sky130/docs/guide.md)**, which covers both SRAM
> and ROM compilation, expected output, verbose levels, xschem simulation,
> and troubleshooting.

> This file is kept for historical reference only. It reflects the state of
> the project during early development (before the DRC fixes were finalized)
> and some details may be outdated.

---

Tool stack: OpenRAM v1.2.48 · KLayout 0.30.2 · Magic 8.3.528 · Docker `iic-osic-tools_chipathon_xserver`

## Quick links to current documentation

| Document | Contents |
|----------|----------|
| [sky130/README.md](./sky130/README.md) | Quickstart, prerequisites, output files |
| [sky130/configs/README.md](./sky130/configs/README.md) | Config template and all options explained |
| [sky130/docs/guide.md](./sky130/docs/guide.md) | Full compilation guide (replaces this file) |
| [sky130/docs/drc_fixes.md](./sky130/docs/drc_fixes.md) | Technical root-cause analysis for each fix |
| [sky130/docs/architecture.md](./sky130/docs/architecture.md) | Compiler internals |
| [sky130/CHANGELOG.md](./sky130/CHANGELOG.md) | History of all fixes and additions |

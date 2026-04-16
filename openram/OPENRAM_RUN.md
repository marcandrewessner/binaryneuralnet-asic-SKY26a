# How to run OpenRAM without mixing the `pip` package with the repo

> **Note:** This guide assumes you are running inside the
> `iic-osic-tools_chipathon_xserver` Docker container, where OpenRAM may be
> pre-installed as a pip package. If you are running from a fresh clone
> without a system-installed `openram`, you can skip directly to the
> [quickstart in sky130/README.md](./sky130/README.md).

---

If you installed `openram` with pip **and** have a copy of the code in your
designs directory, Python may load the package from
`site-packages/openram` instead of your local patched code. This causes:

- `install_conda` trying to create `miniconda` in **non-writable** paths
- `OPENRAM_TECH` undefined or pointing to the pip package
- Empty bitcell SPICE → `Custom cell pin names do not match spice file ... vs []`

## Recommended solution

Always use the compiler script from the repository root:

```bash
cd /path/to/OpenRAM
python3 sram_compiler.py sky130/configs/my_sram.py
```

`sram_compiler.py` prepends the repo directory to `sys.path` so that the
local patched code is **always** used instead of any system-installed package.

Docker example (`iic-osic-tools_chipathon_xserver`):

```bash
export PATH=/foss/tools/bin:$PATH
cd /foss/designs/OpenRAM
python3 sram_compiler.py sky130/configs/my_sram.py
```

Explicit alternative (any environment):

```bash
cd /path/to/OpenRAM
PYTHONPATH=$(pwd) python3 sram_compiler.py sky130/configs/my_sram.py
```

## Conda in Docker (read-only filesystem)

Set `use_conda = False` in your config to use `magic`/`netgen` from `PATH`
without installing Miniconda. The reference configs in `sky130/configs/`
already do this.

To force skipping conda from the environment:

```bash
export OPENRAM_SKIP_CONDA=1
```

## Environment variables

| Variable | Usage |
|----------|-------|
| `PDK_ROOT` | Root of open_pdks (required for sky130 `technology/__init__.py`). Docker: `/foss/pdks`. |
| `OPENRAM_TECH` | Set automatically when using the local repo via `sram_compiler.py` |
| `OPENRAM_MAGIC_NO_USER_RC` | Set to `1` to prevent loading `~/.magicrc` with a different PDK before sky130 |
| `OPENRAM_SKIP_CONDA` | Set to `1` to skip Miniconda installation |
| `OPENRAM_TMP` | Magic/Netgen temporary directory (defaults to `/tmp/openram_<user>_<pid>_temp/`). Verification artifacts are copied to `output_path` after completion. |

## See also

- [sky130/README.md](./sky130/README.md) — Quickstart and compilation guide
- [sky130/docs/guide.md](./sky130/docs/guide.md) — Full guide with troubleshooting

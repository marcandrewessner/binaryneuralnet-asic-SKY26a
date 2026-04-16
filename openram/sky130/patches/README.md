# Applying patches to upstream OpenRAM

These patches apply cleanly to **OpenRAM v1.2.48**.
Each patch is independent and can be applied individually.

## Apply all patches at once

```bash
cd /path/to/openram
for p in sky130/patches/*.patch; do
    echo "Applying $p ..."
    patch -p1 < "$p"
done
```

## Apply individually

```bash
cd /path/to/openram

# Fix Docker getpwuid crash
patch -p1 < sky130/patches/0001-fix-docker-getpwuid-keyerror.patch

# Fix m1.2 DRC violations (bitline jog trunk spacing)
patch -p1 < sky130/patches/0002-fix-m1.2-bitline-jog-trunk-spacing.patch

# Fix m3.2 DRC violations (data-bus channel y-offset)
patch -p1 < sky130/patches/0003-fix-m3.2-data-bus-channel-y-offset.patch

# Waive m2.4 PDK violations + silence Magic DRC noise
patch -p1 < sky130/patches/0004-fix-magic-drc-sky130-noise-and-m2.4-waiver.patch
```

## Check if already applied

```bash
patch -p1 --dry-run < sky130/patches/0002-fix-m1.2-bitline-jog-trunk-spacing.patch
```

## Patch descriptions

| File | Targets | Description |
|------|---------|-------------|
| `0001-fix-docker-getpwuid-keyerror.patch` | `compiler/globals.py` | Handle missing uid in `/etc/passwd` inside Docker containers |
| `0002-fix-m1.2-bitline-jog-trunk-spacing.patch` | `compiler/modules/bank.py` | Clamp bitline jog yoffset using instance bbox bottom instead of BL pin position |
| `0003-fix-m3.2-data-bus-channel-y-offset.patch` | `compiler/modules/sram_1bank.py` | Push M3 data-bus channel down by `m3_to_m3` spacing for sky130 |
| `0004-fix-magic-drc-sky130-noise-and-m2.4-waiver.patch` | `compiler/verify/magic.py` | Parse lyrdb XML, waive m2.4 PDK violations, downgrade Magic DRC noise to info(1) |

import sys
import os

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 run_local.py <config_file.py>")
        sys.exit(1)

# 1. Strip broken system package from Python's search path
sys.path = [p for p in sys.path if 'dist-packages' not in p]

# 2. Add local compiler to path
base_dir = os.path.abspath(".")
compiler_dir = os.path.join(base_dir, "compiler")
sys.path.insert(0, base_dir)
sys.path.insert(0, compiler_dir)

# 3. Map local compiler as 'openram' module so imports resolve correctly
import globals as openram_globals
import sram_compiler
sys.modules['openram'] = sram_compiler
sys.modules['openram.globals'] = openram_globals

if __name__ == "__main__":
    # Pass config file argument through to sram_compiler
    sys.argv = ["sram_compiler.py"] + sys.argv[1:]

    print("--- Running OpenRAM Local (system package bypassed) ---")
    try:
        sram_compiler.main()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

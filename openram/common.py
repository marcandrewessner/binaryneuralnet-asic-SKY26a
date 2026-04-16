# See LICENSE for licensing information.
#
# Copyright (c) 2016-2024 Regents of the University of California, Santa Cruz
# All rights reserved.
#
"""
Common functions for top-level scripts
"""

import sys
import os


def make_openram_package():
    """ Make sure that OpenRAM can be used as a Python package. """

    import importlib
    import importlib.util

    # If OPENRAM_HOME points at a source tree, force-load the LOCAL openram
    # package so we never pick up a pip-installed one from site-packages.
    OPENRAM_HOME = os.getenv("OPENRAM_HOME")
    if OPENRAM_HOME:
        root = os.path.abspath(os.path.join(OPENRAM_HOME, ".."))
        init_file = os.path.join(root, "__init__.py")
        if os.path.isfile(init_file):
            # Remove any cached openram from sys.modules (site-packages)
            sys.modules.pop("openram", None)
            # Put repo root at front of sys.path so Python finds it first
            if root not in sys.path:
                sys.path.insert(0, root)
            # Remove site-packages openram paths to avoid confusion
            sys.path = [p for p in sys.path if "dist-packages/openram" not in p
                        and "site-packages/openram" not in p]
            # Now import — Python will find our local __init__.py
            import openram
            return

    # Fallback: use the system-installed openram package
    openram_loader = importlib.util.find_spec("openram")
    if openram_loader is None and OPENRAM_HOME:
        spec = importlib.util.spec_from_file_location("openram", "{}/../__init__.py".format(OPENRAM_HOME))
        module = importlib.util.module_from_spec(spec)
        sys.modules["openram"] = module
        spec.loader.exec_module(module)

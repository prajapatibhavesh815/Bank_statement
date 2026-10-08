"""
Root convenience launcher for Bank Statement Processing CLI.
Delegates execution directly to backend/cli.py.
"""
import os
import sys
import importlib.util

BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

backend_cli_file = os.path.join(BACKEND_DIR, "cli.py")
spec = importlib.util.spec_from_file_location("backend_cli", backend_cli_file)
backend_cli_module = importlib.util.module_from_spec(spec)
sys.modules["backend_cli"] = backend_cli_module
spec.loader.exec_module(backend_cli_module)

main = backend_cli_module.main

if __name__ == "__main__":
    main()

"""
Root convenience launcher for the Bank Statement Backend Server.
Delegates execution directly to backend/server.py.
"""
import os
import sys
import importlib.util

BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

backend_server_file = os.path.join(BACKEND_DIR, "server.py")
spec = importlib.util.spec_from_file_location("backend_server", backend_server_file)
backend_module = importlib.util.module_from_spec(spec)
sys.modules["backend_server"] = backend_module
spec.loader.exec_module(backend_module)

app = backend_module.app

if __name__ == "__main__":
    os.chdir(BACKEND_DIR)
    import uvicorn
    port = int(os.environ.get("PORT", 8001))
    print(f"Starting Bank Statement Processing API server (backend) on http://127.0.0.1:{port}...")
    uvicorn.run(app, host="127.0.0.1", port=port)

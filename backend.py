"""SkillGap AI - Backend Application Launcher.

Run directly via:
    python backend.py

Starts the FastAPI REST server and serves the frontend dashboard.
"""

import sys
from pathlib import Path
import uvicorn

WORKSPACE_ROOT = Path(__file__).resolve().parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from backend.main import app

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  SkillGap AI - Backend Server Starting")
    print("  Interactive Dashboard: http://127.0.0.1:8000")
    print("  Interactive API Docs:  http://127.0.0.1:8000/docs")
    print("=" * 60 + "\n")
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)

import os
import pathlib
import subprocess
import sys

ROOT_DIR = pathlib.Path(__file__).resolve().parents[2]
ENV_PATH = ROOT_DIR / ".env"

if ENV_PATH.exists():
    for raw_line in ENV_PATH.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ[key.strip()] = value.strip()

cmd = [
    sys.executable,
    "-m",
    "pytest",
    "backend/tests/test_ai_pipeline.py",
    "backend/tests/test_ai_integrations.py",
]
result = subprocess.run(cmd, cwd=str(ROOT_DIR))
sys.exit(result.returncode)

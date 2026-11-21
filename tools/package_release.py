from __future__ import annotations

import subprocess
from pathlib import Path

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    subprocess.run(
        ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(root / "build_submission.ps1")],
        cwd=root,
        check=True,
    )

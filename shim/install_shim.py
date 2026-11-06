"""Install the legacy MediaPipe solutions shim into the BatesPosture venv.

Modern mediapipe wheels dropped ``mediapipe.python.solutions``.  This script
copies ``shim/python`` into ``<site-packages>/mediapipe/python`` so that
``import mediapipe.python.solutions.pose`` works again (BatesPosture needs it).

Run with the venv interpreter::

    D:\\Apps\\PostureGuard\\venv\\Scripts\\python.exe D:\\Apps\\PostureGuard\\shim\\install_shim.py
"""

from __future__ import annotations

import shutil
import sys
import sysconfig
from pathlib import Path


def main() -> int:
    here = Path(__file__).resolve().parent
    source = here / "python"
    if not source.is_dir():
        print(f"ERROR: shim source missing: {source}")
        return 1

    site_packages = Path(sysconfig.get_paths()["purelib"])
    mediapipe_dir = site_packages / "mediapipe"
    if not mediapipe_dir.is_dir():
        print(f"ERROR: mediapipe is not installed in this interpreter ({mediapipe_dir})")
        return 1

    target = mediapipe_dir / "python"
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)
    print(f"Installed shim: {target}")

    import mediapipe  # noqa: F401 - verify after install
    from mediapipe.python.solutions import pose  # noqa: F401

    print(f"mediapipe {mediapipe.__version__}: mediapipe.python.solutions.pose OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

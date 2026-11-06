"""Compatibility shim: restores the legacy ``mediapipe.python`` namespace.

Modern MediaPipe wheels (0.10.3x and 1.x) no longer ship the legacy
``mediapipe.python.solutions`` Python API.  BatesPosture is written against it,
so this package is dropped into ``site-packages/mediapipe/`` to provide the
small surface the application needs (``solutions.pose`` and
``solutions.drawing_utils``), implemented on top of the Tasks API.

Installed by ``D:\\Apps\\PostureGuard\\shim\\install_shim.py``.
"""

from __future__ import annotations

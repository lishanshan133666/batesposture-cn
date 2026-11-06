"""End-to-end smoke test: camera -> PoseDetector -> posture score."""

from __future__ import annotations

import sys
import time
from pathlib import Path

import cv2
import numpy as np

OUT = Path(r"C:\Users\Administrator\Documents\dsh-tmp")


def main() -> int:
    from batesposture.services.settings_service import SettingsService
    from batesposture.ml.pose_detector import PoseDetector

    settings = SettingsService()
    print("settings ok; runtime frame:", settings.runtime.frame_width, settings.runtime.frame_height)
    t0 = time.monotonic()
    detector = PoseDetector(settings)
    print(f"PoseDetector ready in {(time.monotonic() - t0) * 1000:.0f} ms "
          f"(mediapipe prewarm {detector.prewarm_duration_ms:.0f} ms)")

    backend = cv2.CAP_DSHOW if sys.platform == "win32" else cv2.CAP_ANY
    cap = cv2.VideoCapture(settings.runtime.default_camera_id, backend)
    if not cap.isOpened():
        print("ERROR: camera did not open")
        return 1
    print("camera:", cap.get(cv2.CAP_PROP_FRAME_WIDTH), "x", cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    best = None
    for i in range(90):
        ok, frame = cap.read()
        if not ok:
            print("frame read failed at", i)
            break
        annotated, score, result = detector.process_frame(frame)
        if result is not None:
            best = (score, result.metrics, annotated)
            print(f"frame {i}: score={score:.1f} metrics={ {k: round(v, 3) for k, v in result.metrics.items()} }")
            if i % 10 == 0:
                cv2.imwrite(str(OUT / f"posture_test_{i}.jpg"), annotated)
        time.sleep(0.03)
    cap.release()

    if best is None:
        print("NO POSE DETECTED in 90 frames")
        return 2
    cv2.imwrite(str(OUT / "posture_test_best.jpg"), best[2])
    print("saved annotated frames to", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

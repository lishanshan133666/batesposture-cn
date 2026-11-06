"""Legacy ``mediapipe.solutions.pose`` adapter implemented on the Tasks API.

MediaPipe 0.10.3x / 1.x wheels only ship ``mediapipe.tasks``; the old
``mp.solutions.pose.Pose`` class is gone.  BatesPosture calls that legacy class,
so this module re-implements the slice of its surface the app actually uses:

* ``Pose(...)`` with ``static_image_mode``, ``model_complexity``,
  ``min_detection_confidence`` and ``min_tracking_confidence``
* ``Pose.process(rgb_frame)`` returning an object with ``pose_landmarks``
  (``.landmark[i].x/.y/.z/.visibility``) and ``pose_world_landmarks``
* ``PoseLandmark`` (33-point IntEnum) and ``POSE_CONNECTIONS``

Model assets are the official MediaPipe pose landmarker ``.task`` bundles,
downloaded on demand from ``storage.googleapis.com`` and cached locally.
"""

from __future__ import annotations

import enum
import os
import time
import urllib.request
from pathlib import Path
from typing import Any

import numpy as np
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import (
    PoseLandmarker,
    PoseLandmarkerOptions,
    PoseLandmarksConnections,
    RunningMode,
)

__all__ = [
    "Pose",
    "PoseLandmark",
    "POSE_CONNECTIONS",
    "ensure_model",
    "model_directory",
]

_MODEL_URLS = {
    0: (
        "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
        "pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
    ),
    1: (
        "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
        "pose_landmarker_full/float16/1/pose_landmarker_full.task"
    ),
    2: (
        "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
        "pose_landmarker_heavy/float16/1/pose_landmarker_heavy.task"
    ),
}

_MODEL_FILES = {
    0: "pose_landmarker_lite.task",
    1: "pose_landmarker_full.task",
    2: "pose_landmarker_heavy.task",
}


class PoseLandmark(enum.IntEnum):
    """The 33 pose landmarks, matching the legacy MediaPipe ordering."""

    NOSE = 0
    LEFT_EYE_INNER = 1
    LEFT_EYE = 2
    LEFT_EYE_OUTER = 3
    RIGHT_EYE_INNER = 4
    RIGHT_EYE = 5
    RIGHT_EYE_OUTER = 6
    LEFT_EAR = 7
    RIGHT_EAR = 8
    MOUTH_LEFT = 9
    MOUTH_RIGHT = 10
    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    LEFT_ELBOW = 13
    RIGHT_ELBOW = 14
    LEFT_WRIST = 15
    RIGHT_WRIST = 16
    LEFT_PINKY = 17
    RIGHT_PINKY = 18
    LEFT_INDEX = 19
    RIGHT_INDEX = 20
    LEFT_THUMB = 21
    RIGHT_THUMB = 22
    LEFT_HIP = 23
    RIGHT_HIP = 24
    LEFT_KNEE = 25
    RIGHT_KNEE = 26
    LEFT_ANKLE = 27
    RIGHT_ANKLE = 28
    LEFT_HEEL = 29
    RIGHT_HEEL = 30
    LEFT_FOOT_INDEX = 31
    RIGHT_FOOT_INDEX = 32


POSE_CONNECTIONS = frozenset(
    (int(c.start), int(c.end)) for c in PoseLandmarksConnections.POSE_LANDMARKS
)


class NormalizedLandmark:
    """Minimal stand-in for ``NormalizedLandmark`` proto messages."""

    __slots__ = ("x", "y", "z", "visibility", "presence")

    def __init__(
        self,
        x: float,
        y: float,
        z: float = 0.0,
        visibility: float = 0.0,
        presence: float = 0.0,
    ) -> None:
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.visibility = float(visibility)
        self.presence = float(presence)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return (
            f"NormalizedLandmark(x={self.x:.4f}, y={self.y:.4f}, z={self.z:.4f},"
            f" visibility={self.visibility:.3f})"
        )


class NormalizedLandmarkList:
    """Minimal stand-in for a MediaPipe ``NormalizedLandmarkList``."""

    __slots__ = ("landmark",)

    def __init__(self, landmark: list[NormalizedLandmark]) -> None:
        self.landmark = landmark

    def __len__(self) -> int:
        return len(self.landmark)

    def __bool__(self) -> bool:
        return bool(self.landmark)


class _PoseResult:
    """Return value of :meth:`Pose.process`."""

    __slots__ = ("pose_landmarks", "pose_world_landmarks")

    def __init__(
        self,
        pose_landmarks: NormalizedLandmarkList | None,
        pose_world_landmarks: NormalizedLandmarkList | None,
    ) -> None:
        self.pose_landmarks = pose_landmarks
        self.pose_world_landmarks = pose_world_landmarks


def _candidate_model_directories() -> list[Path]:
    candidates: list[Path] = []
    override = os.environ.get("BATESPOSTURE_POSE_MODEL_DIR")
    if override:
        candidates.append(Path(override))
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        candidates.append(Path(local_app_data) / "BatesPosture" / "models")
    candidates.append(Path(r"D:\Apps\PostureGuard\models"))
    candidates.append(Path.home() / ".cache" / "batesposture" / "models")
    return candidates


def model_directory() -> Path:
    """Return the first existing model cache directory, creating one if needed."""

    candidates = _candidate_model_directories()
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    target = candidates[-1]
    target.mkdir(parents=True, exist_ok=True)
    return target


def ensure_model(model_complexity: int) -> str:
    """Download (once) and return the path of the pose landmarker model."""

    complexity = max(0, min(2, int(model_complexity)))
    target = model_directory() / _MODEL_FILES[complexity]
    if target.is_file() and target.stat().st_size > 1_000_000:
        return str(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(target.name + ".part")
    urllib.request.urlretrieve(_MODEL_URLS[complexity], partial)
    partial.replace(target)
    return str(target)


class Pose:
    """Drop-in replacement for ``mp.solutions.pose.Pose`` built on PoseLandmarker."""

    def __init__(
        self,
        static_image_mode: bool = False,
        model_complexity: int = 1,
        smooth_landmarks: bool = True,
        enable_segmentation: bool = False,
        smooth_segmentation: bool = True,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
        model_asset_path: str | None = None,
    ) -> None:
        self.static_image_mode = bool(static_image_mode)
        self.model_complexity = int(model_complexity)
        self.smooth_landmarks = bool(smooth_landmarks)
        self.enable_segmentation = bool(enable_segmentation)
        self.smooth_segmentation = bool(smooth_segmentation)
        self.min_detection_confidence = float(min_detection_confidence)
        self.min_tracking_confidence = float(min_tracking_confidence)

        asset = model_asset_path or ensure_model(self.model_complexity)
        options = PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=asset),
            running_mode=(
                RunningMode.IMAGE if self.static_image_mode else RunningMode.VIDEO
            ),
            num_poses=1,
            min_pose_detection_confidence=self.min_detection_confidence,
            min_pose_presence_confidence=self.min_detection_confidence,
            min_tracking_confidence=self.min_tracking_confidence,
            output_segmentation_masks=False,
        )
        self._landmarker = PoseLandmarker.create_from_options(options)
        self._closed = False
        self._last_timestamp_ms = -1

    # -- public API -------------------------------------------------------
    def process(self, image: Any) -> _PoseResult:
        """Run pose detection on an RGB uint8 ``numpy`` frame."""

        if self._closed:
            raise RuntimeError("Pose object has been closed")
        frame = np.ascontiguousarray(image)
        if frame.ndim != 3 or frame.shape[2] != 3:
            raise ValueError(f"expected HxWx3 RGB image, got shape {frame.shape}")
        if frame.dtype != np.uint8:
            frame = frame.astype(np.uint8)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)

        if self.static_image_mode:
            raw = self._landmarker.detect(mp_image)
        else:
            timestamp_ms = int(time.monotonic() * 1000)
            if timestamp_ms <= self._last_timestamp_ms:
                timestamp_ms = self._last_timestamp_ms + 1
            self._last_timestamp_ms = timestamp_ms
            raw = self._landmarker.detect_for_video(mp_image, timestamp_ms)

        normalized = getattr(raw, "pose_landmarks", None) or []
        world = getattr(raw, "pose_world_landmarks", None) or []
        return _PoseResult(
            self._to_landmark_list(normalized[0]) if normalized else None,
            self._to_landmark_list(world[0]) if world else None,
        )

    def close(self) -> None:
        if not self._closed:
            self._closed = True
            try:
                self._landmarker.close()
            except Exception:  # noqa: BLE001 - closing must never raise
                pass

    def __enter__(self) -> "Pose":
        return self

    def __exit__(self, *_exc: Any) -> None:
        self.close()

    # -- helpers ----------------------------------------------------------
    @staticmethod
    def _to_landmark_list(landmarks: list[Any]) -> NormalizedLandmarkList:
        return NormalizedLandmarkList(
            [
                NormalizedLandmark(
                    lm.x,
                    lm.y,
                    lm.z,
                    getattr(lm, "visibility", 0.0),
                    getattr(lm, "presence", 0.0),
                )
                for lm in landmarks
            ]
        )

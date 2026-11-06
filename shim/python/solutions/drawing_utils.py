"""Legacy ``mediapipe.solutions.drawing_utils`` adapter (OpenCV based)."""

from __future__ import annotations

from typing import Any, Iterable, Sequence

import cv2

__all__ = ["DrawingSpec", "draw_landmarks", "draw_landmark", "draw_connecting_line"]


class DrawingSpec:
    """Same shape as ``mediapipe.solutions.drawing_utils.DrawingSpec``."""

    def __init__(
        self,
        color: tuple[int, int, int] = (0, 255, 0),
        thickness: int = 2,
        circle_radius: int = 2,
    ) -> None:
        self.color = color
        self.thickness = thickness
        self.circle_radius = circle_radius


def _visible(landmark: Any, threshold: float = 0.2) -> bool:
    visibility = getattr(landmark, "visibility", 0.0)
    presence = getattr(landmark, "presence", 0.0)
    return visibility >= threshold or presence >= threshold


def draw_landmark(
    image: Any,
    landmark: Any,
    drawing_spec: DrawingSpec | None = None,
    *,
    width: int | None = None,
    height: int | None = None,
) -> None:
    spec = drawing_spec or DrawingSpec()
    h, w = (height, width) if height and width else image.shape[:2]
    cx, cy = int(landmark.x * w), int(landmark.y * h)
    if spec.circle_radius > 0:
        cv2.circle(image, (cx, cy), spec.circle_radius, spec.color, spec.thickness)


def draw_connecting_line(
    image: Any,
    start: Any,
    end: Any,
    drawing_spec: DrawingSpec | None = None,
    *,
    width: int | None = None,
    height: int | None = None,
) -> None:
    spec = drawing_spec or DrawingSpec()
    h, w = (height, width) if height and width else image.shape[:2]
    cv2.line(
        image,
        (int(start.x * w), int(start.y * h)),
        (int(end.x * w), int(end.y * h)),
        spec.color,
        spec.thickness,
    )


def draw_landmarks(
    image: Any,
    landmark_list: Any,
    connections: Iterable[Sequence[int]] | None = None,
    landmark_drawing_spec: DrawingSpec | None = None,
    connection_drawing_spec: DrawingSpec | None = None,
) -> Any:
    """Draw landmark points and skeleton connections onto a BGR ``numpy`` image."""

    if landmark_list is None or not getattr(landmark_list, "landmark", None):
        return image
    landmarks = landmark_list.landmark
    h, w = image.shape[:2]
    point_spec = landmark_drawing_spec or DrawingSpec()
    line_spec = connection_drawing_spec or DrawingSpec()

    if connections:
        for start_idx, end_idx in connections:
            if start_idx >= len(landmarks) or end_idx >= len(landmarks):
                continue
            start, end = landmarks[start_idx], landmarks[end_idx]
            if not (_visible(start) and _visible(end)):
                continue
            draw_connecting_line(
                image, start, end, line_spec, width=w, height=h
            )

    for landmark in landmarks:
        if not _visible(landmark):
            continue
        draw_landmark(image, landmark, point_spec, width=w, height=h)

    return image

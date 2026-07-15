"""
commands/camera_cmd.py
Camera capture logic (lazy-imports cv2 so app startup stays fast).
The GUI drives frame reading on a QThread; this module only wraps
OpenCV calls with clean error handling.
"""

from __future__ import annotations

import datetime
from typing import Optional

from core.result import CommandResult


class CameraSession:
    """Thin wrapper around cv2.VideoCapture, opened lazily."""

    def __init__(self) -> None:
        self._cap = None
        self._writer = None
        self.recording = False

    def open(self) -> CommandResult:
        import cv2  # lazy import — heavy library

        self._cap = cv2.VideoCapture(0)
        if not self._cap.isOpened():
            self._cap = None
            return CommandResult.error("Cannot open camera")
        return CommandResult.success("Camera active")

    def read_frame(self):
        if self._cap is None:
            return None
        ret, frame = self._cap.read()
        return frame if ret else None

    def take_photo(self, frame) -> CommandResult:
        import cv2

        if frame is None:
            return CommandResult.error("Failed to capture photo")
        filename = f"photo_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        cv2.imwrite(filename, frame)
        return CommandResult.success(f"Photo saved: {filename}", filename=filename)

    def start_recording(self, frame_width: int, frame_height: int) -> CommandResult:
        import cv2

        if self.recording:
            return CommandResult.error("Video already recording!")
        fourcc = cv2.VideoWriter_fourcc(*"XVID")
        filename = f"video_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.avi"
        self._writer = cv2.VideoWriter(filename, fourcc, 20.0, (frame_width, frame_height))
        self.recording = True
        return CommandResult.success(f"Recording video → {filename}", filename=filename)

    def write_frame(self, frame) -> None:
        if self.recording and self._writer is not None and frame is not None:
            self._writer.write(frame)

    def stop_recording(self) -> CommandResult:
        if not self.recording:
            return CommandResult.error("No video is being recorded")
        self.recording = False
        if self._writer is not None:
            self._writer.release()
            self._writer = None
        return CommandResult.success("Video recording stopped and saved")

    def close(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None
        if self._writer is not None:
            self._writer.release()
            self._writer = None
        self.recording = False

#!/usr/bin/env python3
"""
Amcrest Camera RTSP Handler — Cherokee AI Federation

Handles digest-authenticated RTSP streams from Amcrest IP cameras.
Supports direct LAN and tunneled (greenfin) connections.

For Seven Generations
"""

import os
import cv2
import yaml
import time
import logging
import urllib.parse
from typing import Optional, Generator, Tuple, Dict

logger = logging.getLogger(__name__)

REGISTRY_PATH = "/ganuda/config/camera_registry.yaml"


def load_camera_registry() -> Dict:
    """Load camera registry from YAML config."""
    with open(REGISTRY_PATH) as f:
        return yaml.safe_load(f)


def get_camera_password(camera_config: Dict) -> str:
    """Get camera password from environment or fallback."""
    env_key = camera_config.get("password_env", "")
    password = os.environ.get(env_key, "")
    if not password:
        password = camera_config.get("password_fallback", "")
    return password


class AmcrestCamera:
    """Handle Amcrest camera RTSP streams with digest auth."""

    def __init__(self, camera_id: str, stream: str = "sub"):
        """
        Initialize camera from registry.

        Args:
            camera_id: Key from camera_registry.yaml (e.g., 'garage')
            stream: 'main' for full resolution, 'sub' for low-res
        """
        registry = load_camera_registry()
        if camera_id not in registry["cameras"]:
            raise ValueError(f"Unknown camera: {camera_id}")

        self.config = registry["cameras"][camera_id]
        self.camera_id = camera_id
        self.password = get_camera_password(self.config)
        encoded_pw = urllib.parse.quote(self.password, safe="")

        # Build RTSP URL
        rtsp_template = self.config[f"rtsp_{stream}"]
        self.rtsp_url = rtsp_template.replace("{password}", encoded_pw)

        self._cap = None
        logger.info(f"AmcrestCamera initialized: {camera_id} ({stream} stream)")

    def _ensure_capture(self) -> cv2.VideoCapture:
        """Ensure video capture is open, reconnecting if needed."""
        if self._cap is None or not self._cap.isOpened():
            self._cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
            if not self._cap.isOpened():
                raise ConnectionError(
                    f"Failed to open RTSP stream for {self.camera_id}"
                )
        return self._cap

    def get_frame(self) -> Optional[Tuple[bool, any]]:
        """Capture single frame from RTSP stream."""
        try:
            cap = self._ensure_capture()
            ret, frame = cap.read()
            if not ret:
                logger.warning(f"No frame from {self.camera_id}, reconnecting")
                self.release()
                cap = self._ensure_capture()
                ret, frame = cap.read()
            return ret, frame
        except Exception as e:
            logger.error(f"Frame capture error on {self.camera_id}: {e}")
            self.release()
            return False, None

    def stream_frames(
        self, max_frames: int = 0
    ) -> Generator[Tuple[any, float], None, None]:
        """
        Yield (frame, timestamp) continuously.

        Args:
            max_frames: Stop after N frames (0 = infinite)
        """
        count = 0
        while max_frames == 0 or count < max_frames:
            ret, frame = self.get_frame()
            if ret and frame is not None:
                yield frame, time.time()
                count += 1
            else:
                time.sleep(0.5)

    def release(self):
        """Release video capture resources."""
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def __del__(self):
        self.release()
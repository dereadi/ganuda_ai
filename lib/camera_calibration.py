#!/usr/bin/env python3
"""
Camera Lens Calibration — Cherokee AI Federation

Computes intrinsic parameters (focal length, principal point, distortion
coefficients) for Amcrest IP5M cameras using known-dimension reference
objects visible in the frame.

Produces undistortion maps that can be applied to every frame in real-time.

For Seven Generations — Eyes that see true
"""

import os
import sys
import cv2
import json
import yaml
import numpy as np
import logging
from pathlib import Path
from typing import Dict, Tuple, Optional

sys.path.insert(0, "/ganuda")
sys.path.insert(0, "/ganuda/lib")

logger = logging.getLogger(__name__)

REGISTRY_PATH = "/ganuda/config/camera_registry.yaml"
CALIBRATION_DIR = "/ganuda/config/calibration"

# Standard US reference object dimensions (meters)
STOP_SIGN_WIDTH_M = 0.762  # 30 inches
STREET_SIGN_HEIGHT_M = 0.1524  # 6 inches
STREET_SIGN_WIDTH_M = 0.6096  # 24 inches (conservative)
POST_WIDTH_M = 0.0508  # 2 inches
POST_MOUNT_HEIGHT_M = 2.1336  # 7 feet


class CameraCalibrator:
    """Compute and apply lens calibration for Amcrest cameras."""

    def __init__(self, camera_id: str):
        self.camera_id = camera_id
        self.calibration_file = Path(CALIBRATION_DIR) / f"{camera_id}_intrinsics.json"

        with open(REGISTRY_PATH) as f:
            registry = yaml.safe_load(f)
        self.config = registry["cameras"][camera_id]

        self.mount_height_ft = self.config.get("mount_height_ft", 6.0)
        self.lens_mm = self.config.get("lens_mm", 2.8)
        self.hfov_deg = self.config.get("hfov_deg", 110)

        # Intrinsic parameters (loaded or computed)
        self.K = None  # Camera matrix (3x3)
        self.dist_coeffs = None  # Distortion coefficients
        self.map1 = None  # Undistortion remap X
        self.map2 = None  # Undistortion remap Y
        self.new_K = None  # Optimal camera matrix after undistortion

        # Try to load existing calibration
        if self.calibration_file.exists():
            self.load_calibration()

    def estimate_intrinsics_from_fov(self, frame_width: int, frame_height: int):
        """
        Estimate initial intrinsic matrix from known FOV and frame size.
        This gives a starting point before full calibration.
        """
        hfov_rad = np.radians(self.hfov_deg)
        fx = frame_width / (2 * np.tan(hfov_rad / 2))
        fy = fx  # Square pixels assumed
        cx = frame_width / 2.0
        cy = frame_height / 2.0

        self.K = np.array([
            [fx, 0, cx],
            [0, fy, cy],
            [0, 0, 1]
        ], dtype=np.float64)

        # Initial distortion estimate for 2.8mm wide-angle
        # Typical k1 for this lens type: -0.3 to -0.5 (barrel distortion)
        self.dist_coeffs = np.array([-0.35, 0.12, 0.0, 0.0, -0.02], dtype=np.float64)

        logger.info(
            f"Estimated intrinsics for {self.camera_id}: "
            f"fx={fx:.1f}, fy={fy:.1f}, cx={cx:.1f}, cy={cy:.1f}"
        )

    def calibrate_from_reference_points(
        self,
        frame: np.ndarray,
        reference_points: list,
    ):
        """
        Calibrate from known reference points in the frame.

        reference_points: list of dicts with:
            - 'pixel': (px, py) — pixel coordinates in frame
            - 'world': (wx, wy, wz) — world coordinates in meters
            - 'label': str — description of the point
        """
        if len(reference_points) < 4:
            logger.warning("Need at least 4 reference points for calibration")
            return False

        h, w = frame.shape[:2]

        # Build object points (3D) and image points (2D)
        obj_points = np.array(
            [p["world"] for p in reference_points], dtype=np.float32
        ).reshape(-1, 1, 3)
        img_points = np.array(
            [p["pixel"] for p in reference_points], dtype=np.float32
        ).reshape(-1, 1, 2)

        # Estimate initial camera matrix from FOV
        self.estimate_intrinsics_from_fov(w, h)

        # Calibrate with fixed principal point
        flags = (
            cv2.CALIB_USE_INTRINSIC_GUESS
            | cv2.CALIB_FIX_PRINCIPAL_POINT
        )

        ret, K, dist, rvecs, tvecs = cv2.calibrateCamera(
            [obj_points], [img_points], (w, h),
            self.K.copy(), self.dist_coeffs.copy(),
            flags=flags
        )

        if ret:
            self.K = K
            self.dist_coeffs = dist.ravel()
            self._compute_undistortion_maps(w, h)
            logger.info(
                f"Calibration successful for {self.camera_id}: "
                f"reprojection error = {ret:.4f} px"
            )
            return True
        else:
            logger.error(f"Calibration failed for {self.camera_id}")
            return False

    def calibrate_from_checkerboard(
        self,
        frames: list,
        board_size: Tuple[int, int] = (9, 6),
        square_size_m: float = 0.025,
    ):
        """
        Full calibration using checkerboard pattern photographed
        from multiple angles. Gold standard accuracy.

        frames: list of grayscale frames containing the checkerboard
        board_size: (cols, rows) inner corners
        square_size_m: physical size of each square in meters
        """
        obj_p = np.zeros((board_size[0] * board_size[1], 3), np.float32)
        obj_p[:, :2] = np.mgrid[
            0:board_size[0], 0:board_size[1]
        ].T.reshape(-1, 2) * square_size_m

        obj_points = []
        img_points = []

        for frame in frames:
            gray = frame if len(frame.shape) == 2 else cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            ret, corners = cv2.findChessboardCorners(gray, board_size, None)
            if ret:
                corners_refined = cv2.cornerSubPix(
                    gray, corners, (11, 11), (-1, -1),
                    (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
                )
                obj_points.append(obj_p)
                img_points.append(corners_refined)

        if len(obj_points) < 3:
            logger.error(f"Only {len(obj_points)} valid frames — need at least 3")
            return False

        h, w = frames[0].shape[:2]
        ret, K, dist, rvecs, tvecs = cv2.calibrateCamera(
            obj_points, img_points, (w, h), None, None
        )

        if ret:
            self.K = K
            self.dist_coeffs = dist.ravel()
            self._compute_undistortion_maps(w, h)
            logger.info(
                f"Checkerboard calibration for {self.camera_id}: "
                f"error={ret:.4f}px, {len(obj_points)} frames used"
            )
            return True
        return False

    def _compute_undistortion_maps(self, w: int, h: int):
        """Precompute undistortion remap tables for real-time use."""
        self.new_K, roi = cv2.getOptimalNewCameraMatrix(
            self.K, self.dist_coeffs, (w, h), 1, (w, h)
        )
        self.map1, self.map2 = cv2.initUndistortRectifyMap(
            self.K, self.dist_coeffs, None, self.new_K, (w, h), cv2.CV_16SC2
        )
        logger.info(f"Undistortion maps computed for {self.camera_id} ({w}x{h})")

    def undistort(self, frame: np.ndarray) -> np.ndarray:
        """Apply lens undistortion to a frame. ~1ms on CPU."""
        if self.map1 is None or self.map2 is None:
            h, w = frame.shape[:2]
            if self.K is None:
                self.estimate_intrinsics_from_fov(w, h)
            self._compute_undistortion_maps(w, h)

        return cv2.remap(frame, self.map1, self.map2, cv2.INTER_LINEAR)

    def pixel_to_ground(
        self, px: float, py: float
    ) -> Optional[Tuple[float, float]]:
        """
        Convert undistorted pixel coordinates to ground plane
        coordinates (meters from camera base).

        Requires calibrated intrinsics and known mount height.
        Returns (ground_x_m, ground_y_m) or None if above horizon.
        """
        if self.new_K is None:
            return None

        mount_height_m = self.mount_height_ft * 0.3048
        fx = self.new_K[0, 0]
        fy = self.new_K[1, 1]
        cx = self.new_K[0, 2]
        cy = self.new_K[1, 2]

        # Ray from camera through pixel
        ray_x = (px - cx) / fx
        ray_y = (py - cy) / fy
        ray_z = 1.0

        # Intersect with ground plane (z = -mount_height in camera frame)
        # Assuming camera looks roughly forward with some tilt down
        if ray_y <= 0:
            return None  # Above horizon

        t = mount_height_m / ray_y
        ground_x = ray_x * t
        ground_y = ray_z * t  # Forward distance

        return (ground_x, ground_y)

    def ground_distance(
        self, p1: Tuple[float, float], p2: Tuple[float, float]
    ) -> Optional[float]:
        """
        Calculate ground-plane distance in meters between two
        undistorted pixel positions.
        """
        g1 = self.pixel_to_ground(p1[0], p1[1])
        g2 = self.pixel_to_ground(p2[0], p2[1])
        if g1 is None or g2 is None:
            return None
        dx = g2[0] - g1[0]
        dy = g2[1] - g1[1]
        return (dx**2 + dy**2) ** 0.5

    def save_calibration(self):
        """Save calibration to JSON file."""
        Path(CALIBRATION_DIR).mkdir(parents=True, exist_ok=True)

        data = {
            "camera_id": self.camera_id,
            "mount_height_ft": self.mount_height_ft,
            "lens_mm": self.lens_mm,
            "hfov_deg": self.hfov_deg,
            "K": self.K.tolist() if self.K is not None else None,
            "dist_coeffs": self.dist_coeffs.tolist() if self.dist_coeffs is not None else None,
            "new_K": self.new_K.tolist() if self.new_K is not None else None,
        }

        with open(self.calibration_file, "w") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Calibration saved: {self.calibration_file}")

    def load_calibration(self) -> bool:
        """Load calibration from JSON file."""
        try:
            with open(self.calibration_file) as f:
                data = json.load(f)

            self.K = np.array(data["K"], dtype=np.float64) if data.get("K") else None
            self.dist_coeffs = (
                np.array(data["dist_coeffs"], dtype=np.float64)
                if data.get("dist_coeffs") else None
            )
            self.new_K = (
                np.array(data["new_K"], dtype=np.float64)
                if data.get("new_K") else None
            )
            self.mount_height_ft = data.get("mount_height_ft", self.mount_height_ft)
            logger.info(f"Calibration loaded: {self.calibration_file}")
            return True
        except Exception as e:
            logger.warning(f"Failed to load calibration: {e}")
            return False


def run_calibration_capture(camera_id: str):
    """
    Interactive calibration capture tool.
    Captures a snapshot, user identifies reference points,
    and computes calibration.
    """
    from lib.amcrest_camera import AmcrestCamera

    cam = AmcrestCamera(camera_id, stream="main")  # Use main stream for calibration
    calibrator = CameraCalibrator(camera_id)

    logger.info(f"Capturing calibration frame from {camera_id}...")
    ret, frame = cam.get_frame()
    cam.release()

    if not ret:
        logger.error("Failed to capture frame")
        return

    # Save calibration frame
    cal_dir = Path(CALIBRATION_DIR)
    cal_dir.mkdir(parents=True, exist_ok=True)
    frame_path = cal_dir / f"{camera_id}_calibration_frame.jpg"
    cv2.imwrite(str(frame_path), frame)
    logger.info(f"Calibration frame saved: {frame_path}")

    h, w = frame.shape[:2]
    logger.info(f"Frame size: {w}x{h}")

    # Estimate intrinsics from FOV as baseline
    calibrator.estimate_intrinsics_from_fov(w, h)
    calibrator.save_calibration()

    logger.info(
        f"Initial calibration saved for {camera_id}. "
        f"To refine: provide reference points or use checkerboard."
    )
    return frame_path


if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="Camera Calibration Tool")
    parser.add_argument("camera_id", choices=["garage", "traffic", "office_pii"])
    parser.add_argument("--capture", action="store_true", help="Capture calibration frame")
    args = parser.parse_args()

    if args.capture:
        run_calibration_capture(args.camera_id)
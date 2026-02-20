#!/usr/bin/env python3
"""
Vision API Routes — Cherokee AI Federation SAG Dashboard

Provides REST endpoints for camera status, speed detections,
calibration data, and live snapshots.

For Seven Generations
"""

import os
import sys
import json
import yaml
import time
import logging
import io
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from flask import Blueprint, jsonify, request, send_file

sys.path.insert(0, "/ganuda")
sys.path.insert(0, "/ganuda/lib")

from lib.secrets_loader import get_db_config
from sag.routes.auth import require_api_key
import psycopg2

logger = logging.getLogger(__name__)

vision_bp = Blueprint("vision", __name__, url_prefix="/api/vision")

REGISTRY_PATH = "/ganuda/config/camera_registry.yaml"
CALIBRATION_DIR = "/ganuda/config/calibration"
SNAPSHOT_CACHE = {}  # camera_id -> (timestamp, bytes)
SNAPSHOT_TTL = 30  # seconds


def _get_db():
    return psycopg2.connect(**get_db_config())


def _load_registry():
    with open(REGISTRY_PATH) as f:
        return yaml.safe_load(f)


@vision_bp.route("/cameras", methods=["GET"])
def camera_status():
    """Camera fleet status with connection info."""
    registry = _load_registry()
    cameras = []
    for cam_id, cam in registry.get("cameras", {}).items():
        cal_file = Path(CALIBRATION_DIR) / f"{cam_id}_intrinsics.json"
        cameras.append({
            "id": cam_id,
            "model": cam.get("model"),
            "ip": cam.get("ip"),
            "location": cam.get("location"),
            "purpose": cam.get("purpose"),
            "mount_height_ft": cam.get("mount_height_ft"),
            "stereo_role": cam.get("stereo_role"),
            "resolution_main": cam.get("resolution_main"),
            "resolution_sub": cam.get("resolution_sub"),
            "fps": cam.get("fps"),
            "calibrated": cal_file.exists(),
        })

    stereo = registry.get("stereo_pairs", {})
    return jsonify({
        "cameras": cameras,
        "stereo_pairs": stereo,
        "timestamp": datetime.now().isoformat(),
    })


@vision_bp.route("/speed/recent", methods=["GET"])
def speed_recent():
    """Last N speed detections."""
    limit = request.args.get("limit", 50, type=int)
    try:
        conn = _get_db()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, timestamp, track_id, speed_mph, position_x,
                       position_y, confidence, camera_pair,
                       plate_text, plate_confidence, vehicle_type
                FROM stereo_speed_detections
                ORDER BY timestamp DESC
                LIMIT %s
            """, (limit,))
            rows = cur.fetchall()
        conn.close()

        detections = []
        for row in rows:
            detections.append({
                "id": row[0],
                "timestamp": row[1].isoformat() if row[1] else None,
                "track_id": row[2],
                "speed_mph": float(row[3]) if row[3] else None,
                "position_x": float(row[4]) if row[4] else None,
                "position_y": float(row[5]) if row[5] else None,
                "confidence": float(row[6]) if row[6] else None,
                "camera": row[7],
                "plate_text": row[8],
                "plate_confidence": float(row[9]) if row[9] else None,
                "vehicle_type": row[10],
            })

        return jsonify({"detections": detections, "count": len(detections)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@vision_bp.route("/speed/stats", methods=["GET"])
def speed_stats():
    """Aggregated speed statistics for the last 24 hours."""
    try:
        conn = _get_db()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    COUNT(*) as total,
                    ROUND(AVG(speed_mph)::numeric, 1) as avg_speed,
                    MAX(speed_mph) as max_speed,
                    COUNT(CASE WHEN speed_mph > 25 THEN 1 END) as alerts,
                    COUNT(DISTINCT track_id) as unique_vehicles,
                    COUNT(CASE WHEN plate_text IS NOT NULL THEN 1 END) as plates_read
                FROM stereo_speed_detections
                WHERE timestamp > NOW() - INTERVAL '24 hours'
            """)
            row = cur.fetchone()

            # Hourly breakdown
            cur.execute("""
                SELECT
                    date_trunc('hour', timestamp) as hour,
                    COUNT(*) as detections,
                    ROUND(AVG(speed_mph)::numeric, 1) as avg_speed,
                    MAX(speed_mph) as max_speed
                FROM stereo_speed_detections
                WHERE timestamp > NOW() - INTERVAL '24 hours'
                GROUP BY hour
                ORDER BY hour
            """)
            hourly = cur.fetchall()
        conn.close()

        return jsonify({
            "period": "24h",
            "total_detections": row[0],
            "avg_speed_mph": float(row[1]) if row[1] else 0,
            "max_speed_mph": float(row[2]) if row[2] else 0,
            "speed_alerts": row[3],
            "unique_vehicles": row[4],
            "plates_read": row[5],
            "hourly": [
                {
                    "hour": h[0].isoformat() if h[0] else None,
                    "detections": h[1],
                    "avg_speed": float(h[2]) if h[2] else 0,
                    "max_speed": float(h[3]) if h[3] else 0,
                }
                for h in hourly
            ],
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@vision_bp.route("/calibration", methods=["GET"])
def calibration_status():
    """Calibration status for all cameras."""
    registry = _load_registry()
    status = {}

    for cam_id in registry.get("cameras", {}):
        cal_file = Path(CALIBRATION_DIR) / f"{cam_id}_intrinsics.json"
        if cal_file.exists():
            with open(cal_file) as f:
                cal_data = json.load(f)
            status[cam_id] = {
                "calibrated": True,
                "file": str(cal_file),
                "mount_height_ft": cal_data.get("mount_height_ft"),
                "lens_mm": cal_data.get("lens_mm"),
                "hfov_deg": cal_data.get("hfov_deg"),
                "has_K": cal_data.get("K") is not None,
                "has_distortion": cal_data.get("dist_coeffs") is not None,
            }
        else:
            status[cam_id] = {"calibrated": False}

    # Stereo pair status
    stereo = registry.get("stereo_pairs", {})
    stereo_file = Path(CALIBRATION_DIR) / "stereo_extrinsics.json"

    return jsonify({
        "cameras": status,
        "stereo_calibrated": stereo_file.exists(),
        "stereo_pairs": stereo,
    })


@vision_bp.route("/snapshot/<camera_id>", methods=["GET"])
def camera_snapshot(camera_id):
    """Live snapshot from a camera (cached for 30s)."""
    import requests
    from requests.auth import HTTPDigestAuth

    registry = _load_registry()
    cam = registry.get("cameras", {}).get(camera_id)
    if not cam:
        return jsonify({"error": f"Unknown camera: {camera_id}"}), 404

    # Check cache
    cached = SNAPSHOT_CACHE.get(camera_id)
    if cached and time.time() - cached[0] < SNAPSHOT_TTL:
        return send_file(
            io.BytesIO(cached[1]),
            mimetype="image/jpeg",
            download_name=f"{camera_id}.jpg",
        )

    # Get password from env
    pw_env = cam.get("password_env", "")
    password = os.environ.get(pw_env, "")
    username = cam.get("username", "admin")

    # Build snapshot URL
    if cam.get("tunnel_http_port"):
        host = cam["tunnel_host"]
        port = cam["tunnel_http_port"]
    else:
        host = cam["ip"]
        port = 80
    url = f"http://{host}:{port}/cgi-bin/snapshot.cgi?channel=1"

    try:
        resp = requests.get(
            url,
            auth=HTTPDigestAuth(username, password),
            timeout=10,
        )
        if resp.status_code == 200:
            SNAPSHOT_CACHE[camera_id] = (time.time(), resp.content)
            return send_file(
                io.BytesIO(resp.content),
                mimetype="image/jpeg",
                download_name=f"{camera_id}.jpg",
            )
        return jsonify({"error": f"Camera returned {resp.status_code}"}), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 502
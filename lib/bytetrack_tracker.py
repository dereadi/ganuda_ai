import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from collections import deque

@dataclass
class STrack:
    track_id: int
    bbox: np.ndarray
    score: float
    history: deque
    is_activated: bool = False
    frame_id: int = 0
    tracklet_len: int = 0

class ByteTracker:
    """ByteTrack: Multi-Object Tracking by Associating Every Detection Box"""

    def __init__(self, track_thresh: float = 0.5, track_buffer: int = 30, match_thresh: float = 0.8):
        self.track_thresh = track_thresh
        self.track_buffer = track_buffer
        self.match_thresh = match_thresh
        self.frame_id = 0
        self.track_id_count = 0
        self.tracked_stracks: List[STrack] = []
        self.lost_stracks: List[STrack] = []
        self.removed_stracks: List[STrack] = []

    def update(self, detections: List[Dict]) -> List[Dict]:
        self.frame_id += 1
        activated_stracks, refind_stracks, lost_stracks, removed_stracks = [], [], [], []

        high_dets = [d for d in detections if d.get("score", 0.5) >= self.track_thresh]
        low_dets = [d for d in detections if d.get("score", 0.5) < self.track_thresh]

        # Match high score detections with tracked
        unmatched_tracks, unmatched_dets = self._match_detections(self.tracked_stracks, high_dets)

        # Match low score detections with unmatched tracks
        if low_dets and unmatched_tracks:
            remaining_tracks, _ = self._match_detections(unmatched_tracks, low_dets)
            for track in remaining_tracks:
                if self.frame_id - track.frame_id > self.track_buffer:
                    removed_stracks.append(track)
                else:
                    lost_stracks.append(track)

        # Create new tracks for unmatched high-score detections
        for det in unmatched_dets:
            if det.get("score", 0.5) >= self.track_thresh:
                self.track_id_count += 1
                new_track = STrack(track_id=self.track_id_count, bbox=np.array(det["bbox"]), score=det.get("score", 0.5), history=deque(maxlen=50), is_activated=True, frame_id=self.frame_id)
                activated_stracks.append(new_track)

        self.tracked_stracks = [t for t in self.tracked_stracks if t not in removed_stracks] + activated_stracks
        self.lost_stracks = lost_stracks

        return [{"track_id": t.track_id, "bbox": t.bbox.tolist(), "score": t.score} for t in self.tracked_stracks if t.is_activated]

    def _match_detections(self, tracks: List[STrack], dets: List[Dict]) -> Tuple[List[STrack], List[Dict]]:
        if not tracks or not dets:
            return tracks, dets
        cost_matrix = self._iou_distance(tracks, dets)
        matched, unmatched_t, unmatched_d = self._linear_assignment(cost_matrix)
        for t_idx, d_idx in matched:
            tracks[t_idx].bbox = np.array(dets[d_idx]["bbox"])
            tracks[t_idx].score = dets[d_idx].get("score", 0.5)
            tracks[t_idx].frame_id = self.frame_id
        return [tracks[i] for i in unmatched_t], [dets[i] for i in unmatched_d]

    def _iou_distance(self, tracks: List[STrack], dets: List[Dict]) -> np.ndarray:
        cost = np.zeros((len(tracks), len(dets)))
        for i, t in enumerate(tracks):
            for j, d in enumerate(dets):
                cost[i, j] = 1 - self._iou(t.bbox, np.array(d["bbox"]))
        return cost

    def _iou(self, box1: np.ndarray, box2: np.ndarray) -> float:
        x1, y1 = max(box1[0], box2[0]), max(box1[1], box2[1])
        x2, y2 = min(box1[2], box2[2]), min(box1[3], box2[3])
        inter = max(0, x2-x1) * max(0, y2-y1)
        area1 = (box1[2]-box1[0]) * (box1[3]-box1[1])
        area2 = (box2[2]-box2[0]) * (box2[3]-box2[1])
        return inter / (area1 + area2 - inter + 1e-6)

    def _linear_assignment(self, cost: np.ndarray) -> Tuple[List, List, List]:
        matched, unmatched_t, unmatched_d = [], list(range(cost.shape[0])), list(range(cost.shape[1]))
        for i in range(min(cost.shape)):
            if cost.size == 0: break
            min_idx = np.unravel_index(np.argmin(cost), cost.shape)
            if cost[min_idx] < self.match_thresh:
                matched.append((min_idx[0], min_idx[1]))
                if min_idx[0] in unmatched_t: unmatched_t.remove(min_idx[0])
                if min_idx[1] in unmatched_d: unmatched_d.remove(min_idx[1])
                cost[min_idx[0], :] = 1
                cost[:, min_idx[1]] = 1
        return matched, unmatched_t, unmatched_d

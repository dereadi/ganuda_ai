"""
Frame processor for ARC-AGI-3 game frames.

Provides frame hashing, flood-fill segmentation, action priority tiering,
frame differencing, and status bar detection/masking.

Input format: frame = list of 2D grids (list[list[list[int]]]), values 0-15,
up to 64x64. Internally we work with the last grid as a numpy uint8 array.

Dependencies: stdlib + numpy only.

Ported from the 3rd-place reference solution (arc-agi-3-just-explore)
by the HeuristicAgent / FrameProcessor class in agents/heuristic_agent.py.
"""

from __future__ import annotations

import hashlib
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

import numpy as np


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# 4-connected and 8-connected neighbour offsets (row, col)
OFFSETS_4: tuple[tuple[int, int], ...] = ((-1, 0), (1, 0), (0, -1), (0, 1))
OFFSETS_8: tuple[tuple[int, int], ...] = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
)

# Colour salience classification (ARC palette indices)
NON_SALIENT_COLORS: frozenset[int] = frozenset({0, 1, 2, 3, 4, 5})
SALIENT_COLORS: frozenset[int] = frozenset({6, 7, 8, 9, 10, 11, 12, 13, 14, 15})

# Sentinel value written into masked (status-bar) pixels before hashing
STATUS_BAR_SENTINEL: int = 16

# Default frame dimensions
DEFAULT_FRAME_SHAPE: tuple[int, int] = (64, 64)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class Component:
    """A single connected component found by flood-fill segmentation."""
    component_id: int
    color: int
    area: int
    bounding_box: tuple[int, int, int, int]  # (x1, y1, x2, y2) inclusive
    is_rectangle: bool
    twin_ids: list[int] = field(default_factory=list)

    @property
    def num_twins(self) -> int:
        return len(self.twin_ids)

    @property
    def width(self) -> int:
        """Bounding-box width in pixels."""
        return self.bounding_box[2] - self.bounding_box[0] + 1

    @property
    def height(self) -> int:
        """Bounding-box height in pixels."""
        return self.bounding_box[3] - self.bounding_box[1] + 1


# ---------------------------------------------------------------------------
# FrameProcessor
# ---------------------------------------------------------------------------

class FrameProcessor:
    """
    Stateless utilities for ARC-AGI-3 frame analysis.

    All public methods accept plain numpy arrays (uint8, shape HxW)
    or the raw list-of-grids format and return pure data -- no side effects,
    no external dependencies beyond numpy.
    """

    def __init__(
        self,
        connectivity: int = 4,
        frame_shape: tuple[int, int] = DEFAULT_FRAME_SHAPE,
        status_bar_edge_threshold: int = 3,
        status_bar_ratio_threshold: float = 5.0,
        status_bar_twins_threshold: int = 3,
        min_clickable_width: int = 2,
        max_clickable_width: int = 32,
    ) -> None:
        """
        Parameters
        ----------
        connectivity : int
            4 or 8 for flood-fill neighbour connectivity.
        frame_shape : tuple[int, int]
            Expected (height, width) of a single frame grid.
        status_bar_edge_threshold : int
            Max distance (in pixels) from a frame edge for a component to be
            considered "on the edge" and thus a potential status-bar element.
        status_bar_ratio_threshold : float
            Minimum aspect ratio (long / short) for a component to be classified
            as a status-bar line segment without needing twin confirmation.
        status_bar_twins_threshold : int
            Minimum number of edge-adjacent twin components required to classify
            a cluster of small identical shapes as status-bar dots.
        min_clickable_width / max_clickable_width : int
            Bounding-box dimension range that qualifies a component as
            "medium-sized" for action-priority grouping.
        """
        if connectivity not in (4, 8):
            raise ValueError("connectivity must be 4 or 8")
        self.connectivity = connectivity
        self.offsets = OFFSETS_4 if connectivity == 4 else OFFSETS_8
        self.frame_shape = frame_shape
        self.status_bar_edge_threshold = status_bar_edge_threshold
        self.status_bar_ratio_threshold = status_bar_ratio_threshold
        self.status_bar_twins_threshold = status_bar_twins_threshold
        self.min_clickable_width = min_clickable_width
        self.max_clickable_width = max_clickable_width
        # Adaptive status bar tracking
        self._prev_frame = None
        self._row_change_counts = None
        self._frame_count = 0

    def reset_tracking(self):
        """Reset adaptive status bar tracking (call on level transition)."""
        self._prev_frame = None
        self._row_change_counts = None
        self._frame_count = 0

    # ------------------------------------------------------------------
    # Helpers: raw frame -> numpy
    # ------------------------------------------------------------------

    @staticmethod
    def to_numpy(frame: list[list[list[int]]]) -> np.ndarray:
        """
        Convert the raw frame format (list of 2D grids) to a single 2D
        uint8 numpy array.  Takes the *last* grid if multiple are present,
        matching the reference behaviour.
        """
        arr = np.array(frame, dtype=np.uint8)
        if arr.ndim == 3:
            arr = arr[-1]  # take last grid
        return arr

    # ------------------------------------------------------------------
    # 1. Frame Hashing -- Blake2b with status-bar masking
    # ------------------------------------------------------------------

    @staticmethod
    def hash_frame(frame: np.ndarray) -> str:
        """
        Deterministic 128-bit Blake2b hash for an integer-valued numpy array
        with elements in 0..15 (4-bit values).

        The algorithm:
        1. Flatten to C-order uint8 array.
        2. Pack two 4-bit values per byte (high nibble | low nibble).
        3. Hash with Blake2b using the array shape as the ``person`` tag,
           so arrays with identical content but different shapes do not
           collide.

        Returns a 32-character hex digest (128 bits).

        Status-bar pixels should be zeroed (or set to 0) *before* calling
        this function so that status-bar changes do not affect the hash.
        The reference code sets masked pixels to 16, then resets them to 0
        before hashing.
        """
        frame = np.asarray(frame, dtype=np.uint8, order="C")
        flat = frame.ravel()

        # Pad to even length so we can pair every two values
        if flat.size & 1:
            flat = np.concatenate([flat, np.zeros(1, dtype=np.uint8)])

        # Pack two 4-bit values per byte: high nibble = even index,
        # low nibble = odd index
        packed = (flat[0::2] << 4) | (flat[1::2] & 0x0F)
        payload = packed.tobytes()

        # Embed the shape in the person field to avoid collisions between
        # identical data in different shapes (e.g. 8x8 vs 4x16)
        shape_tag = repr(frame.shape).encode()
        return hashlib.blake2b(
            payload, digest_size=16, person=shape_tag
        ).hexdigest()

    def hash_frame_masked(
        self,
        frame: np.ndarray,
        status_bar_mask: Optional[np.ndarray] = None,
    ) -> str:
        """
        Hash a frame after applying the status-bar mask.

        The reference workflow:
        1. Set status_bar_mask pixels to sentinel value 16.
        2. Segment the frame (which ignores sentinel pixels).
        3. Reset sentinel pixels to 0.
        4. Hash the cleaned frame.

        This helper does steps 3-4 in a non-mutating way.
        """
        work = frame.copy()
        if status_bar_mask is not None:
            work[status_bar_mask] = 0
        return self.hash_frame(work)

    # ------------------------------------------------------------------
    # 2. Flood-fill connected-component segmentation
    # ------------------------------------------------------------------

    def segment_frame(
        self, frame: np.ndarray
    ) -> tuple[np.ndarray, list[Component]]:
        """
        Segment *frame* into connected components of same-colour pixels.

        Uses BFS flood-fill with the configured connectivity (4 or 8).

        Returns
        -------
        label_map : np.ndarray, shape (H, W), dtype int32
            Each pixel is labelled with its component id (0-based).
        components : list[Component]
            Metadata for each component: bounding box, colour, area,
            rectangularity, and twin relationships.

        Twin detection
        --------------
        After the initial flood fill, a second O(n^2) pass identifies
        "twins" -- components with matching colour, area, and
        rectangularity.  This information feeds into status-bar detection
        (dot patterns along edges).
        """
        h, w = frame.shape[:2]
        label_map = np.full((h, w), -1, dtype=np.int32)
        components: list[Component] = []
        cid = -1
        offsets = self.offsets

        # --- Pass 1: BFS flood fill ---
        for y in range(h):
            for x in range(w):
                if label_map[y, x] != -1:
                    continue
                cid += 1
                color = int(frame[y, x])
                queue: deque[tuple[int, int]] = deque([(y, x)])
                label_map[y, x] = cid

                min_x = max_x = x
                min_y = max_y = y
                area = 0

                while queue:
                    cy, cx = queue.popleft()
                    area += 1
                    if cx < min_x:
                        min_x = cx
                    if cx > max_x:
                        max_x = cx
                    if cy < min_y:
                        min_y = cy
                    if cy > max_y:
                        max_y = cy

                    for dy, dx in offsets:
                        ny, nx = cy + dy, cx + dx
                        if (
                            0 <= ny < h
                            and 0 <= nx < w
                            and label_map[ny, nx] == -1
                            and frame[ny, nx] == color
                        ):
                            label_map[ny, nx] = cid
                            queue.append((ny, nx))

                rect_area = (max_x - min_x + 1) * (max_y - min_y + 1)
                components.append(
                    Component(
                        component_id=cid,
                        color=color,
                        area=area,
                        bounding_box=(min_x, min_y, max_x, max_y),
                        is_rectangle=(area == rect_area),
                    )
                )

        # --- Pass 2: twin identification ---
        n = len(components)
        for i in range(n):
            ci = components[i]
            twins = []
            for j in range(n):
                if i == j:
                    continue
                cj = components[j]
                if (
                    cj.area == ci.area
                    and cj.is_rectangle == ci.is_rectangle
                    and cj.color == ci.color
                ):
                    twins.append(j)
            ci.twin_ids = twins

        return label_map, components

    # ------------------------------------------------------------------
    # 3. Action Priority Tiering (5 groups)
    # ------------------------------------------------------------------

    def assign_action_groups(
        self, components: list[Component], n_groups: int = 5
    ) -> list[set[int]]:
        """
        Partition component indices into *n_groups* priority tiers for
        the graph explorer to try in order.

        Group assignment logic (matching the reference):

        Group 0 (highest priority):
            Salient colour AND medium bounding-box size.
            These are the most likely interactive puzzle elements.

        Group 1:
            Medium size but non-salient colour.
            Structurally interesting but visually muted.

        Group 2:
            Salient colour but outside the medium-size band
            (very small or very large).

        Group 3:
            Non-salient, non-medium, non-status-bar.
            Background clutter.

        Group 4 (lowest priority):
            Status-bar sentinel colour (value 16) -- pixels that were
            masked before segmentation.

        Parameters
        ----------
        components : list[Component]
            Output of segment_frame().
        n_groups : int
            Must be 5 (only 5-group scheme implemented, per reference).

        Returns
        -------
        list[set[int]]
            groups[g] is the set of component indices assigned to tier g.
        """
        if n_groups != 5:
            raise ValueError("Only 5 groups are supported")

        groups: list[set[int]] = [set() for _ in range(n_groups)]

        for idx, comp in enumerate(components):
            is_salient = comp.color in SALIENT_COLORS
            w, h = comp.width, comp.height
            is_medium = (
                self.min_clickable_width <= w <= self.max_clickable_width
                and self.min_clickable_width <= h <= self.max_clickable_width
            )
            is_status_bar = comp.color == STATUS_BAR_SENTINEL

            if is_salient and is_medium:
                groups[0].add(idx)
            elif is_medium:
                groups[1].add(idx)
            elif is_salient:
                groups[2].add(idx)
            elif not is_status_bar:
                groups[3].add(idx)
            else:
                groups[4].add(idx)

        return groups

    # ------------------------------------------------------------------
    # 4. Frame Differencing
    # ------------------------------------------------------------------

    @staticmethod
    def diff_frames(
        frame_a: np.ndarray, frame_b: np.ndarray
    ) -> dict:
        """
        Compare two frames and return a summary of their differences.

        Both frames must have the same shape.

        Returns
        -------
        dict with keys:
            identical : bool
                True if every pixel matches.
            num_changed_pixels : int
                Count of pixels that differ.
            changed_fraction : float
                Fraction of total pixels that changed.
            changed_mask : np.ndarray (bool)
                Boolean mask where True = pixel differs.
            changed_colors_from : set[int]
                Set of colour values that were replaced.
            changed_colors_to : set[int]
                Set of colour values that appeared in changed positions.
        """
        if frame_a.shape != frame_b.shape:
            raise ValueError(
                f"Shape mismatch: {frame_a.shape} vs {frame_b.shape}"
            )
        mask = frame_a != frame_b
        n_changed = int(mask.sum())
        total = frame_a.size

        colors_from: set[int] = set()
        colors_to: set[int] = set()
        if n_changed > 0:
            colors_from = set(frame_a[mask].tolist())
            colors_to = set(frame_b[mask].tolist())

        return {
            "identical": n_changed == 0,
            "num_changed_pixels": n_changed,
            "changed_fraction": n_changed / total if total > 0 else 0.0,
            "changed_mask": mask,
            "changed_colors_from": colors_from,
            "changed_colors_to": colors_to,
        }

    # ------------------------------------------------------------------
    # 5. Status Bar Detection and Masking
    # ------------------------------------------------------------------

    def _component_edges(self, comp: Component) -> list[str]:
        """
        Return which frame edges a component is fully adjacent to,
        given the configured edge threshold.

        A component is "on" an edge if its bounding box fits entirely
        within *status_bar_edge_threshold* pixels of that edge.
        """
        x1, y1, x2, y2 = comp.bounding_box
        h, w = self.frame_shape
        thr = self.status_bar_edge_threshold
        edges: list[str] = []

        if max(x1, x2) < thr:
            edges.append("left")
        if min(x1, x2) > w - thr:
            edges.append("right")
        if max(y1, y2) < thr:
            edges.append("top")
        if min(y1, y2) > h - thr:
            edges.append("bottom")

        return edges

    def _component_is_elongated(self, comp: Component) -> bool:
        """
        Return True if the component's bounding-box aspect ratio exceeds
        the status_bar_ratio_threshold in either orientation.  Elongated
        edge-adjacent components are classified as status-bar line segments.
        """
        w, h = comp.width, comp.height
        if h == 0 or w == 0:
            return False
        ratio = w / h
        return (
            ratio >= self.status_bar_ratio_threshold
            or ratio <= 1.0 / self.status_bar_ratio_threshold
        )

    def _twins_on_same_edges(
        self,
        comp: Component,
        components: list[Component],
        edges: list[str],
    ) -> list[int]:
        """
        Return twin component ids that are also on (at least one of) the
        same frame edges.
        """
        result: list[int] = []
        for twin_id in comp.twin_ids:
            twin = components[twin_id]
            twin_edges = self._component_edges(twin)
            if any(e in twin_edges for e in edges):
                result.append(twin_id)
        return result

    def detect_status_bars(
        self,
        label_map: np.ndarray,
        components: list[Component],
    ) -> tuple[list[list[int]], np.ndarray]:
        """
        Identify status-bar components using rule-based heuristics.

        A component is a status bar element if it is on a frame edge AND
        either:
          (a) it has an elongated aspect ratio (line segment), or
          (b) it belongs to a cluster of >= status_bar_twins_threshold
              identical twins that are all on the same edge (dot pattern).

        Parameters
        ----------
        label_map : np.ndarray
            Component label map from segment_frame().
        components : list[Component]
            Component list from segment_frame().

        Returns
        -------
        bar_groups : list[list[int]]
            Each inner list is a group of component ids forming one
            detected status bar.
        mask : np.ndarray (bool), same shape as label_map
            True where status-bar pixels are located.
        """
        checked: set[int] = set()
        bar_groups: list[list[int]] = []

        for i, comp in enumerate(components):
            if i in checked:
                continue
            checked.add(i)

            edges = self._component_edges(comp)
            if not edges:
                continue

            group_ids = [i]

            if self._component_is_elongated(comp):
                # Elongated edge component -> status bar line
                bar_groups.append(group_ids)
                continue

            # Not elongated: check for dot-pattern (multiple twins on edge)
            twin_ids_on_edge = self._twins_on_same_edges(
                comp, components, edges
            )
            for tid in twin_ids_on_edge:
                checked.add(tid)

            # Need at least twins_threshold total edge-adjacent copies
            # (including the original) to qualify
            if len(twin_ids_on_edge) + 1 >= self.status_bar_twins_threshold:
                group_ids.extend(twin_ids_on_edge)
                bar_groups.append(group_ids)

        # Build boolean mask
        mask = np.zeros(label_map.shape, dtype=bool)
        for group in bar_groups:
            for cid in group:
                mask[label_map == cid] = True

        return bar_groups, mask

    def mask_status_bars(
        self, frame: np.ndarray, mask: np.ndarray
    ) -> np.ndarray:
        """
        Apply status-bar mask to a frame.  Masked pixels are set to
        STATUS_BAR_SENTINEL (16), matching the reference workflow.
        Returns a copy; the original is not modified.
        """
        out = frame.copy()
        out[mask] = STATUS_BAR_SENTINEL
        return out

    # ------------------------------------------------------------------
    # Convenience: full pipeline
    # ------------------------------------------------------------------

    def process(
        self, raw_frame: list[list[list[int]]]
    ) -> dict:
        """
        Run the full analysis pipeline on a raw frame.

        Returns a dict with:
            frame_np        : np.ndarray -- the 2D frame as uint8
            label_map       : np.ndarray -- component ids per pixel
            components      : list[Component]
            status_bar_mask : np.ndarray (bool)
            status_bar_groups : list[list[int]]
            action_groups   : list[set[int]]
            frame_hash      : str -- Blake2b hash with status bars masked
        """
        frame_np = self.to_numpy(raw_frame)

        # Segment once to find status bars
        label_map_raw, comps_raw = self.segment_frame(frame_np)
        bar_groups, sb_mask = self.detect_status_bars(label_map_raw, comps_raw)

        # Apply mask, then re-segment for clickable components
        masked = self.mask_status_bars(frame_np, sb_mask)
        label_map, components = self.segment_frame(masked)

        # Action priority groups
        action_groups = self.assign_action_groups(components)

        # Adaptive status bar detection: track rows that change on every call
        # and mask them for hashing. This catches step counters, fuel bars, etc.
        # that the geometric detection misses.
        if self._row_change_counts is None:
            self._row_change_counts = np.zeros(frame_np.shape[0], dtype=int)
        if self._prev_frame is not None:
            changed_rows = np.any(frame_np != self._prev_frame, axis=1)
            self._row_change_counts += changed_rows.astype(int)
            self._frame_count += 1
            # After 3+ frames, rows that changed EVERY time are status bars
            if self._frame_count >= 3:
                always_changing = self._row_change_counts >= self._frame_count
                sb_mask = sb_mask | always_changing[:, np.newaxis].repeat(frame_np.shape[1], axis=1)
        self._prev_frame = frame_np.copy()

        # Hash the frame with status bars zeroed out
        frame_for_hash = frame_np.copy()
        frame_for_hash[sb_mask] = 0
        frame_hash = self.hash_frame(frame_for_hash)

        return {
            "frame_np": frame_np,
            "label_map": label_map,
            "components": components,
            "status_bar_mask": sb_mask,
            "status_bar_groups": bar_groups,
            "action_groups": action_groups,
            "frame_hash": frame_hash,
        }


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== FrameProcessor self-test ===\n")
    fp = FrameProcessor()

    # --- Test 1: Frame hashing on synthetic 64x64 grid ---
    print("1. Frame hashing (Blake2b, 128-bit)")
    rng = np.random.default_rng(42)
    grid = rng.integers(0, 16, size=(64, 64), dtype=np.uint8)

    h1 = fp.hash_frame(grid)
    h2 = fp.hash_frame(grid)
    print(f"   Hash of random 64x64 grid : {h1}")
    print(f"   Deterministic (same twice): {h1 == h2}")
    assert h1 == h2, "Hash must be deterministic"

    # Different content -> different hash
    grid2 = grid.copy()
    grid2[0, 0] = (grid2[0, 0] + 1) % 16
    h3 = fp.hash_frame(grid2)
    print(f"   Hash after 1-pixel change : {h3}")
    print(f"   Different from original   : {h1 != h3}")
    assert h1 != h3, "Different frames must hash differently"

    # Shape matters
    h4 = fp.hash_frame(grid.reshape(128, 32))
    print(f"   Hash of reshaped (128x32) : {h4}")
    print(f"   Different from (64x64)    : {h1 != h4}")
    assert h1 != h4, "Different shapes must hash differently"

    # --- Test 2: Flood-fill segmentation ---
    print("\n2. Flood-fill connected-component segmentation")
    small = np.array(
        [
            [0, 0, 1, 1],
            [0, 0, 1, 1],
            [2, 2, 0, 0],
            [2, 2, 0, 0],
        ],
        dtype=np.uint8,
    )
    lm, comps = fp.segment_frame(small)
    print(f"   4x4 frame with 4 quadrants -> {len(comps)} components")
    for c in comps:
        print(f"     id={c.component_id} color={c.color} area={c.area} "
              f"bbox={c.bounding_box} rect={c.is_rectangle}")
    assert len(comps) == 4, "Expected 4 components in 2x2 quadrant grid"

    # --- Test 3: Action priority tiering ---
    print("\n3. Action priority tiering (5 groups)")
    # Create a frame with known components at different salience levels
    tiered = np.zeros((16, 16), dtype=np.uint8)
    tiered[2:6, 2:6] = 9    # salient (blue), medium size -> group 0
    tiered[2:6, 8:12] = 3   # non-salient (gray), medium  -> group 1
    tiered[8:9, 2:3] = 11   # salient (yellow), tiny      -> group 2
    tiered[10:14, 8:12] = 1 # non-salient, medium-ish     -> group 1

    fp16 = FrameProcessor(frame_shape=(16, 16))
    _, t_comps = fp16.segment_frame(tiered)
    groups = fp16.assign_action_groups(t_comps)
    print(f"   Groups: {[len(g) for g in groups]} components per tier")
    # Group 0 should have at least the salient+medium component
    assert any(
        t_comps[idx].color == 9 for idx in groups[0]
    ), "Salient+medium component should be in group 0"

    # --- Test 4: Frame differencing ---
    print("\n4. Frame differencing")
    a = rng.integers(0, 16, size=(8, 8), dtype=np.uint8)
    b = a.copy()
    b[3, 3] = (b[3, 3] + 1) % 16
    b[5, 5] = (b[5, 5] + 2) % 16
    diff = fp.diff_frames(a, b)
    print(f"   Changed pixels: {diff['num_changed_pixels']}")
    print(f"   Changed fraction: {diff['changed_fraction']:.4f}")
    assert diff["num_changed_pixels"] == 2

    # --- Test 5: Status bar detection ---
    print("\n5. Status bar detection and masking")
    sb_frame = np.zeros((16, 16), dtype=np.uint8)
    # Put a long thin bar along the top edge (row 0)
    sb_frame[0, :] = 5
    # Put puzzle content in the middle
    sb_frame[5:10, 5:10] = 9

    fp_sb = FrameProcessor(
        frame_shape=(16, 16),
        status_bar_edge_threshold=3,
        status_bar_ratio_threshold=5.0,
    )
    lm_sb, comps_sb = fp_sb.segment_frame(sb_frame)
    bar_groups, mask = fp_sb.detect_status_bars(lm_sb, comps_sb)
    print(f"   Detected {len(bar_groups)} status bar group(s)")
    print(f"   Masked pixels: {mask.sum()}")
    # The top bar (16 pixels) should be detected
    assert mask[0, 0], "Top-edge bar should be masked"
    assert not mask[7, 7], "Interior puzzle content should not be masked"

    # --- Test 6: Full pipeline ---
    print("\n6. Full pipeline (process)")
    raw = [rng.integers(0, 16, size=(64, 64), dtype=np.uint8).tolist()]
    result = fp.process(raw)
    print(f"   Hash: {result['frame_hash']}")
    print(f"   Components: {len(result['components'])}")
    print(f"   Status bar pixels: {result['status_bar_mask'].sum()}")
    print(f"   Action groups: {[len(g) for g in result['action_groups']]}")

    print("\n=== All tests passed ===")

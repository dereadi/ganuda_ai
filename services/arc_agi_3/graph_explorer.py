"""
Graph Explorer for ARC-AGI-3 state-space search.

Ported from the 3rd-place reference solution (arc-agi-3-just-explore/graph_explorer.py).
Simplified from numpy structured arrays to plain Python dicts/lists.

Core algorithm:
  - Maintains a directed graph of game states (nodes = frame hashes, edges = actions).
  - Tracks a "frontier" of nodes that still have untested actions.
  - Uses multi-source BFS (from all frontier nodes backwards through the reverse graph)
    to compute shortest distances from any node to the nearest frontier node.
  - Edge selection: if current node has untested actions, pick one randomly.
    Otherwise, follow the shortest path toward the nearest frontier node.
  - Actions are grouped by priority. The explorer exhausts all actions in the
    current group before advancing to the next (higher-index) group.
  - Suspicious transitions require 3 consistent observations before being trusted,
    guarding against non-deterministic game behavior.
  - On score increase the graph can be reset (level reset) so exploration starts fresh.
"""

from __future__ import annotations

import random
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Dict, Hashable, List, Optional, Set, Tuple

INFINITY = 2**30


# ---------------------------------------------------------------------------
# Edge record -- one per action candidate at a node
# ---------------------------------------------------------------------------

@dataclass
class EdgeRecord:
    """Metadata for a single action (edge candidate) at a node."""
    group: int = 0          # priority group (0 = highest priority)
    result: int = 0         # 1 = success, -1 = failed, 0 = untested
    target: Optional[Hashable] = None  # target node hash (None if untested/failed)
    distance: int = 0       # BFS distance from target to nearest frontier node
    errors: int = 0         # consecutive error count for suspicious-transition logic


# ---------------------------------------------------------------------------
# NodeInfo -- one per discovered game state
# ---------------------------------------------------------------------------

@dataclass
class NodeInfo:
    """
    Represents a single discovered game state in the exploration graph.

    Each node holds N action candidates (edges). Candidates are partitioned into
    priority groups. The explorer exhausts lower-index groups first.

    Attributes:
        name: Unique identifier (frame hash) for this state.
        total_candidates: Number of action candidates at this node.
        num_groups: Number of priority groups.
        group_to_remaining: List of sets; group_to_remaining[g] holds indices of
            untested candidates belonging to group g.
        edges: List of EdgeRecord, one per candidate.
        error_threshold: How many errors before an edge is promoted to the next group
            (suspicious-transition / 3-strike rule).
        closed: True once all candidates in the active group have been tested.
        distance: Shortest BFS distance to any frontier node (through tested edges).
    """
    name: Hashable
    total_candidates: int
    num_groups: int = 1

    group_to_remaining: List[Set[int]] = field(default_factory=list)
    edges: List[EdgeRecord] = field(default_factory=list)

    error_threshold: int = 3
    closed: bool = False
    distance: int = INFINITY

    def __post_init__(self):
        # Build default group assignment if none provided
        if not self.group_to_remaining:
            self.group_to_remaining = [set(range(self.total_candidates))]

        # Ensure we have the right number of group buckets
        while len(self.group_to_remaining) < self.num_groups:
            self.group_to_remaining.append(set())

        # Build edge records with group assignments
        self.edges = [EdgeRecord() for _ in range(self.total_candidates)]
        for group_id, candidate_ids in enumerate(self.group_to_remaining):
            for idx in candidate_ids:
                self.edges[idx].group = group_id

    # -- queries ---------------------------------------------------------------

    def has_open_group(self, active_group: int) -> bool:
        """True if this node has at least one untested edge in group <= active_group."""
        for g in range(active_group + 1):
            if g < len(self.group_to_remaining) and self.group_to_remaining[g]:
                return True
        return False

    # -- mutations -------------------------------------------------------------

    def record_test(
        self,
        edge_idx: int,
        success: int,
        target_node: Optional[Hashable] = None,
    ) -> bool:
        """
        Record the outcome of testing action *edge_idx*.

        Args:
            edge_idx: Index of the action candidate.
            success: 1 = reached a new state, 0 = no effect (failed), -1 = error.
            target_node: Hash of the resulting state (required when success=1).

        Returns:
            True if the edge status was finalized (success or permanent failure).
            False if the edge got an error but hasn't hit the threshold yet
            (3-strike rule: errors accumulate, and after *error_threshold* strikes
            the edge is either promoted to the next group or marked failed).
        """
        edge = self.edges[edge_idx]
        edge_group = edge.group

        if success == -1:
            # Error path -- accumulate strikes
            edge.errors += 1
            if edge.errors >= self.error_threshold:
                edge.errors = 0
                next_group = edge_group + 1
                if next_group > self.num_groups - 1:
                    # All groups exhausted -- mark permanently failed
                    self.group_to_remaining[edge_group].discard(edge_idx)
                    edge.result = -1
                    edge.distance = INFINITY
                    return True
                else:
                    # Promote to next (lower-priority) group
                    edge.group = next_group
                    self.group_to_remaining[next_group].add(edge_idx)
                    self.group_to_remaining[edge_group].discard(edge_idx)
            return False

        # Remove from its group's remaining set
        self.group_to_remaining[edge_group].discard(edge_idx)

        if success == 1:
            edge.target = target_node
            edge.distance = -1  # placeholder; GraphExplorer._rebuild_distances sets real value
            edge.result = 1
        elif success == 0:
            edge.distance = INFINITY
            edge.result = -1

        return True


# ---------------------------------------------------------------------------
# GraphExplorer -- the main exploration controller
# ---------------------------------------------------------------------------

class GraphExplorer:
    """
    Directed state graph that drives exploration through a game's state space.

    The graph grows as the agent discovers new states. At each step the explorer
    either picks an untested action at the current node or navigates toward the
    nearest frontier node (one that still has untested actions).

    Key data structures:
        _nodes:    node hash -> NodeInfo
        _graph:    node hash -> set of (edge_idx, target_hash) -- forward edges
        _graph_rev: node hash -> set of (edge_idx, source_hash) -- reverse edges
        _frontier: set of node hashes that still have untested actions
        _dist:     node hash -> shortest BFS distance to any frontier node
        _next_hop: node hash -> (edge_idx, next_node) on shortest path to frontier
    """

    def __init__(self, n_groups: int = 1, verbose: bool = False) -> None:
        self._n_groups = max(1, n_groups)
        self._verbose = verbose
        self.reset()

    # -- lifecycle -------------------------------------------------------------

    def reset(self) -> None:
        """Clear all graph state (used on level reset / score increase)."""
        self._nodes: Dict[Hashable, NodeInfo] = {}
        self._graph: Dict[Hashable, Set[Tuple[int, Hashable]]] = defaultdict(set)
        self._graph_rev: Dict[Hashable, Set[Tuple[int, Hashable]]] = defaultdict(set)
        self._frontier: Set[Hashable] = set()
        self._dist: Dict[Hashable, int] = {}
        self._next_hop: Dict[Hashable, Tuple[int, Hashable]] = {}
        self._active_group: int = 0
        self._empty: bool = True

        # Suspicious transition tracking: (source, edge_idx, target) -> count
        self.suspicious_transitions: Dict[Tuple[Hashable, int, Hashable], int] = {}
        self.suspicious_threshold: int = 3

    def initialize(
        self,
        start_node: Hashable,
        num_candidates: int,
        group_to_remaining: Optional[List[Set[int]]] = None,
    ) -> None:
        """Seed the graph with the initial game state."""
        self._add_node(start_node, num_candidates, group_to_remaining)

    @property
    def active_group(self) -> int:
        return self._active_group

    @property
    def empty(self) -> bool:
        return self._empty

    def is_finished(self) -> bool:
        """True when no frontier nodes remain (all actions exhausted)."""
        return not self._frontier

    def get_distance(self, node: Hashable) -> Optional[int]:
        """Return BFS distance to nearest frontier, or None if unreachable."""
        d = self._dist.get(node)
        if d is None or d >= INFINITY:
            return None
        return d

    def get_next_hop_node(self, node: Hashable) -> Optional[Hashable]:
        """
        Return the next node to visit on the shortest path to a frontier node.
        If *node* is itself on the frontier, returns *node*.
        """
        if node in self._frontier:
            return node
        hop = self._next_hop.get(node)
        if hop is None:
            return None
        return hop[1]

    # -- recording transitions -------------------------------------------------

    def record_test(
        self,
        node: Hashable,
        edge_idx: int,
        success: int,
        target_node: Optional[Hashable] = None,
        target_num_candidates: Optional[int] = None,
        target_group_to_remaining: Optional[List[Set[int]]] = None,
        suspicious_transition: bool = False,
    ) -> None:
        """
        Record the result of testing action *edge_idx* from *node*.

        Args:
            node: The state where the action was taken.
            edge_idx: Index of the action candidate.
            success: 1 = new state reached, 0 = no effect, -1 = error.
            target_node: Hash of the resulting state (required when success=1).
            target_num_candidates: Number of action candidates at the target
                (required when target_node is newly discovered).
            target_group_to_remaining: Optional group assignments for target node.
            suspicious_transition: If True, apply the 3-strike rule before trusting.
        """
        if node not in self._nodes:
            raise KeyError(f"Unknown node {node!r}")

        node_info = self._nodes[node]

        # Handle closed-node re-test: only allow if new target is closer to frontier
        if node_info.closed:
            existing_target = node_info.edges[edge_idx].target
            if target_node == existing_target:
                return  # duplicate, skip
            # Allow re-test only if new target is closer to frontier
            new_dist = self._dist.get(target_node, 0)
            old_dist = self._dist.get(existing_target, INFINITY) if existing_target else INFINITY
            if new_dist >= old_dist:
                return

        # Suspicious transition gate (3-strike rule)
        if suspicious_transition:
            key = (node, edge_idx, target_node)
            self.suspicious_transitions[key] = self.suspicious_transitions.get(key, 0) + 1
            count = self.suspicious_transitions[key]
            if self._verbose:
                print(f"Suspicious transition {key}, count={count}")
            if count < self.suspicious_threshold:
                return  # not yet trusted

        # Record on the node
        node_info.record_test(edge_idx, success, target_node)

        if success == 1:
            if target_node is None:
                raise ValueError("target_node required when success=1")

            # Discover new node if needed
            if target_node not in self._nodes:
                if target_num_candidates is None:
                    raise ValueError("target_num_candidates required for a new node")
                self._add_node(target_node, target_num_candidates, target_group_to_remaining)

            # Record the directed edge
            self._graph[node].add((edge_idx, target_node))
            self._graph_rev[target_node].add((edge_idx, node))

            # Maybe close source node
            if not node_info.has_open_group(self._active_group):
                self._close_node(node)

            # Update frontier / distances for target
            if self._nodes[target_node].has_open_group(self._active_group):
                self._rebuild_distances()
            else:
                self._close_node(target_node)
                self._maybe_advance_group(target_node)
        else:
            # Failed or error -- maybe close source
            if not node_info.has_open_group(self._active_group):
                self._close_node(node)
                self._maybe_advance_group(node)

    # -- edge selection --------------------------------------------------------

    def choose_edge(self, node: Hashable) -> Tuple[int, str]:
        """
        Pick the next action to take from *node*.

        Strategy:
          1. If the node has untested actions in the active group (or below),
             pick one at random from the remaining candidates.
          2. Otherwise, follow the shortest tested edge toward the nearest
             frontier node.

        Returns:
            (edge_index, reasoning_string)
        """
        node_info = self._nodes[node]

        if node_info.has_open_group(self._active_group):
            # Collect untested candidates from active group and below
            untested = []
            for g in range(self._active_group + 1):
                if g < len(node_info.group_to_remaining):
                    untested.extend(node_info.group_to_remaining[g])
            if not untested:
                raise ValueError("Node reports open group but no untested edges found")
            edge_idx = random.choice(untested)
            reason = (
                f"Randomly chose untested edge {edge_idx} from "
                f"active_group<={self._active_group}"
            )
        else:
            # Navigate toward frontier: pick a tested-success edge with lowest distance
            best_dist = node_info.distance
            candidates = [
                i for i, e in enumerate(node_info.edges)
                if e.distance <= best_dist
                and e.result == 1
                and e.group <= self._active_group
            ]
            if not candidates:
                # No navigable path to frontier — try advancing group
                self._maybe_advance_group(node)
                # Try again with new group
                candidates = [
                    i for i, e in enumerate(node_info.edges)
                    if e.result == 1 and e.group <= self._active_group
                ]
                if not candidates:
                    # Last resort: pick any untested edge regardless of group
                    any_untested = [i for i, e in enumerate(node_info.edges) if e.result == 0]
                    if any_untested:
                        edge_idx = random.choice(any_untested)
                        return edge_idx, f"Escape: random untested edge {edge_idx} (no frontier path)"
                    # Truly stuck — pick any tested edge for random walk
                    any_tested = [i for i, e in enumerate(node_info.edges) if e.result == 1]
                    if any_tested:
                        edge_idx = random.choice(any_tested)
                        return edge_idx, f"Random walk: edge {edge_idx} (fully explored node)"
                    raise ValueError(
                        f"No edges at all from node {node!r}"
                    )
            edge_idx = random.choice(candidates)
            reason = f"Chose tested edge {edge_idx} toward frontier (dist={best_dist})"

        return edge_idx, reason

    # -- internal helpers ------------------------------------------------------

    def _add_node(
        self,
        node: Hashable,
        n_candidates: int,
        group_to_remaining: Optional[List[Set[int]]] = None,
    ) -> None:
        """Register a new node in the graph."""
        if n_candidates < 1:
            raise ValueError("n_candidates must be >= 1")

        self._nodes[node] = NodeInfo(
            name=node,
            total_candidates=n_candidates,
            num_groups=self._n_groups,
            group_to_remaining=(
                [set(ids) for ids in group_to_remaining]
                if group_to_remaining
                else [set(range(n_candidates))]
            ),
        )
        self._graph[node] = set()
        self._graph_rev[node] = set()

        if self._empty:
            self._empty = False

        if self._nodes[node].has_open_group(self._active_group):
            self._frontier.add(node)
        else:
            self._close_node(node)
            self._maybe_advance_group(node)

    def _close_node(self, node: Hashable) -> None:
        """Mark a node as fully explored and remove from frontier."""
        info = self._nodes[node]
        if info.closed:
            return
        info.closed = True
        self._frontier.discard(node)
        self._rebuild_distances()

    def _rebuild_distances(self) -> None:
        """
        Multi-source BFS from all frontier nodes, walking backward through
        the reverse graph. Computes shortest distance from every discovered
        node to its nearest frontier node, and records the next-hop for
        navigation.

        This is the core pathfinding that lets the explorer navigate from
        an exhausted node back toward unexplored territory.
        """
        self._dist.clear()
        self._next_hop.clear()

        # Initialize all distances to infinity
        for node, info in self._nodes.items():
            info.distance = INFINITY
            self._dist[node] = INFINITY

        # Seed: frontier nodes are distance 0 from themselves
        queue = deque(self._frontier)
        for src in self._frontier:
            self._nodes[src].distance = 0
            self._dist[src] = 0

        # BFS backward through reverse edges
        while queue:
            v = queue.popleft()
            v_dist = self._dist.get(v, INFINITY)

            for edge_idx, u in self._graph_rev.get(v, ()):
                u_info = self._nodes[u]
                new_dist = v_dist + 1

                # Update the specific edge's distance
                u_info.edges[edge_idx].distance = new_dist

                # Update node distance if this is a shorter path
                if self._dist.get(u, INFINITY) > new_dist:
                    u_info.distance = new_dist
                    self._dist[u] = new_dist
                    self._next_hop[u] = (edge_idx, v)
                    queue.append(u)

    def _maybe_advance_group(self, current_node: Hashable) -> None:
        """
        If no frontier is reachable from current_node under the active group,
        advance to the next priority group and rebuild frontier + distances.

        Group advancement allows the explorer to try lower-priority actions
        only after all higher-priority actions across the entire reachable
        graph have been exhausted.
        """
        distance = self._nodes[current_node].distance

        while distance >= INFINITY and self._active_group < self._n_groups - 1:
            self._active_group += 1

            # Rebuild frontier under the new group
            self._frontier.clear()
            for node, info in self._nodes.items():
                if info.has_open_group(self._active_group):
                    self._frontier.add(node)
                    info.closed = False

            self._rebuild_distances()
            distance = self._dist.get(current_node, INFINITY)

    # -- introspection ---------------------------------------------------------

    def dump(self) -> str:
        """Return a summary string of the current graph state."""
        lines = [
            f"GraphExplorer: {len(self._nodes)} nodes, "
            f"{len(self._frontier)} frontier, "
            f"active_group={self._active_group}",
            f"  frontier: {self._frontier}",
        ]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Simple test
# ---------------------------------------------------------------------------

def _test_basic_exploration():
    """
    Simulate a small state graph to verify the explorer's core behavior.

    States:  A -> B -> C
    Each state has 3 action candidates. Only action 0 succeeds (leads to next state).
    """
    print("=== Basic exploration test ===\n")

    gx = GraphExplorer(n_groups=1, verbose=True)
    gx.initialize(start_node="A", num_candidates=3)

    assert not gx.is_finished(), "Should not be finished with untested actions"
    assert "A" in gx._frontier, "A should be on the frontier"

    # Test action 1 from A -- fails (no effect)
    gx.record_test("A", 1, success=0)
    print(f"After A/action1 fail: {gx.dump()}\n")

    # Test action 0 from A -- succeeds, discovers B
    gx.record_test("A", 0, success=1, target_node="B", target_num_candidates=3)
    print(f"After A->B success: {gx.dump()}\n")
    assert "B" in gx._frontier, "B should be on the frontier"

    # Test action 2 from A -- fails
    gx.record_test("A", 2, success=0)
    print(f"After A/action2 fail: {gx.dump()}\n")
    assert "A" not in gx._frontier, "A should be closed (all actions tested)"

    # From A (exhausted), choose_edge should navigate toward B
    edge_idx, reason = gx.choose_edge("A")
    print(f"choose_edge(A) = {edge_idx}, reason: {reason}")
    assert edge_idx == 0, "Should navigate via edge 0 (the one leading to B)"

    # From B, choose_edge should pick an untested action
    edge_idx_b, reason_b = gx.choose_edge("B")
    print(f"choose_edge(B) = {edge_idx_b}, reason: {reason_b}")
    assert gx._nodes["B"].edges[edge_idx_b].result == 0, "Should pick untested edge"

    # Test action 0 from B -- succeeds, discovers C
    gx.record_test("B", 0, success=1, target_node="C", target_num_candidates=3)
    print(f"After B->C success: {gx.dump()}\n")

    # Test remaining B actions as failures
    gx.record_test("B", 1, success=0)
    gx.record_test("B", 2, success=0)
    assert "B" not in gx._frontier

    # C should still be on frontier
    assert "C" in gx._frontier
    assert not gx.is_finished()

    # Exhaust C
    gx.record_test("C", 0, success=0)
    gx.record_test("C", 1, success=0)
    gx.record_test("C", 2, success=0)
    assert gx.is_finished(), "All nodes exhausted, should be finished"
    print(f"\nFinal state: {gx.dump()}")
    print("\n--- Basic test PASSED ---\n")


def _test_suspicious_transitions():
    """
    Verify the 3-strike suspicious transition rule.
    A transition must be observed 3 times before being recorded.
    """
    print("=== Suspicious transition test ===\n")

    gx = GraphExplorer(n_groups=1, verbose=True)
    gx.initialize(start_node="X", num_candidates=2)

    # First two attempts are ignored (suspicious)
    gx.record_test("X", 0, success=1, target_node="Y",
                    target_num_candidates=2, suspicious_transition=True)
    assert "Y" not in gx._nodes, "Y should NOT be added yet (strike 1)"

    gx.record_test("X", 0, success=1, target_node="Y",
                    target_num_candidates=2, suspicious_transition=True)
    assert "Y" not in gx._nodes, "Y should NOT be added yet (strike 2)"

    # Third attempt -- trusted
    gx.record_test("X", 0, success=1, target_node="Y",
                    target_num_candidates=2, suspicious_transition=True)
    assert "Y" in gx._nodes, "Y SHOULD be added (strike 3 = trusted)"
    print(f"\nState after trust: {gx.dump()}")
    print("\n--- Suspicious transition test PASSED ---\n")


def _test_group_advancement():
    """
    Verify that the explorer advances to higher-priority groups when
    all actions in the current group are exhausted across the graph.
    """
    print("=== Group advancement test ===\n")

    # 2 groups: group 0 has action 0, group 1 has action 1
    gx = GraphExplorer(n_groups=2, verbose=True)
    gx.initialize(
        start_node="S",
        num_candidates=2,
        group_to_remaining=[{0}, {1}],
    )

    assert gx.active_group == 0

    # Exhaust group 0 action
    gx.record_test("S", 0, success=0)
    print(f"After group-0 exhausted: active_group={gx.active_group}")
    # Group should advance because no frontier reachable under group 0
    assert gx.active_group == 1, "Should advance to group 1"
    assert not gx.is_finished(), "Group 1 still has untested actions"

    # Now exhaust group 1
    gx.record_test("S", 1, success=0)
    assert gx.is_finished(), "All groups exhausted"
    print(f"\nFinal: {gx.dump()}")
    print("\n--- Group advancement test PASSED ---\n")


def _test_level_reset():
    """
    Verify that reset() clears all state for a fresh start (level reset on score increase).
    """
    print("=== Level reset test ===\n")

    gx = GraphExplorer(n_groups=1)
    gx.initialize(start_node="L1", num_candidates=2)
    gx.record_test("L1", 0, success=1, target_node="L2", target_num_candidates=2)
    assert len(gx._nodes) == 2

    # Simulate score increase -> reset
    gx.reset()
    assert gx.empty
    assert len(gx._nodes) == 0
    assert gx.is_finished()  # no frontier

    # Re-initialize for new level
    gx.initialize(start_node="M1", num_candidates=3)
    assert not gx.is_finished()
    assert "M1" in gx._frontier
    print(f"After reset + re-init: {gx.dump()}")
    print("\n--- Level reset test PASSED ---\n")


if __name__ == "__main__":
    _test_basic_exploration()
    _test_suspicious_transitions()
    _test_group_advancement()
    _test_level_reset()
    print("All tests passed.")

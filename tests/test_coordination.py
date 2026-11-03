"""
Unit tests for multi-robot movement resolution.
Tests all requirements specified in Priority 1:
- Empty destination
- Single robot
- Two robots requesting the same destination
- Two robots requesting opposite directions on the same edge (head-on swap)
- Three-robot rotation (A -> B -> C -> A)
- Four-robot rotation (A -> B -> E -> D -> A)
- Movement chain ending at an empty node
- Robot blocked by a stationary robot
- Multiple independent movement chains
"""

import pytest
from tests.test_coordination_helpers import check_movement_safety, build_test_robot


def resolve_simultaneous_moves_improved(robots, time_step=0):
    """
    Improved Simultaneous Movement Resolver:
    1. Guarantees collision prevention (vertex conflicts).
    2. Guarantees head-on swap prevention (edge conflicts).
    3. Prevents movement into stationary occupied nodes.
    4. Supports safe movement chains ending at empty/vacated nodes.
    5. Supports safe circular rotations of 3 or more robots (length >= 3).
    6. Reconsiders alternative destination requesters when top-priority cannot move.
    7. Provides starvation-free fairness using waiting steps + rotating priority.
    8. Preserves simultaneous update semantics.
    """
    active_robots = [r for r in robots if not r.get("completed", False)]
    occupancy = {r["current_node"]: r["robot_id"] for r in active_robots}
    robot_by_id = {r["robot_id"]: r for r in active_robots}

    requests = {}
    for r in active_robots:
        idx = r.get("path_index", 0)
        path = r.get("path", [])
        if idx + 1 < len(path):
            requests[r["robot_id"]] = path[idx + 1]

    if not requests:
        return requests, set()

    # Destination grouping
    dest_groups = {}
    for rid, dest in requests.items():
        dest_groups.setdefault(dest, []).append(rid)

    # Priority ranking function (waiting steps descending, then rotating order)
    total_active = max(len(active_robots), 1)
    robot_order = {r["robot_id"]: i for i, r in enumerate(active_robots)}

    def priority_key(rid):
        r = robot_by_id[rid]
        waiting = r.get("waiting_steps", 0)
        rotating_pos = (robot_order[rid] - time_step) % total_active
        return (waiting, -rotating_pos, -robot_order[rid])

    for dest in dest_groups:
        dest_groups[dest].sort(key=priority_key, reverse=True)

    # Helper to evaluate candidate moves
    def evaluate_candidate_moves(candidate_moves):
        """
        Given candidate_moves: dict mapping robot_id -> dest.
        Every destination appears at most once in candidate_moves.values().
        Find the approved subset of collision-safe moves.
        """
        # Build dependency graph
        # For each r in candidate_moves, who does it depend on?
        dep = {}  # r -> other_r or None
        for rid, dest in candidate_moves.items():
            occ = occupancy.get(dest)
            if occ is None:
                dep[rid] = None  # Destination is empty
            elif occ not in candidate_moves:
                dep[rid] = "STATIONARY"  # Destination occupied by non-moving robot
            else:
                # Check for 2-cycle (head-on swap)
                curr_node = robot_by_id[rid]["current_node"]
                if candidate_moves.get(occ) == curr_node:
                    dep[rid] = "HEAD_ON"
                else:
                    dep[rid] = occ

        # Now classify each robot's component
        approved = set()
        visited = {}  # rid -> status: 'approved', 'blocked', 'visiting'

        def check_robot(rid, path_set):
            target = dep[rid]
            if target is None:
                return True
            if target in ("STATIONARY", "HEAD_ON"):
                return False
            if target in path_set:
                # We found a cycle!
                # Find length of cycle
                cycle_len = len(path_set) - path_set.index(target)
                return cycle_len >= 3
            if target in visited:
                return visited[target] == "approved"

            path_set.append(target)
            result = check_robot(target, path_set)
            path_set.pop()
            return result

        for rid in candidate_moves:
            if check_robot(rid, [rid]):
                approved.add(rid)

        return approved

    # Iterative assignment with fallback reconsideration:
    # Start with top-ranked candidate for each destination
    candidate_indices = {dest: 0 for dest in dest_groups}
    best_approved = set()

    max_iterations = 10
    for _ in range(max_iterations):
        candidate_moves = {}
        for dest, idx in candidate_indices.items():
            if idx < len(dest_groups[dest]):
                candidate_moves[dest_groups[dest][idx]] = dest

        approved = evaluate_candidate_moves(candidate_moves)
        if len(approved) > len(best_approved):
            best_approved = approved

        # Check if any destination's candidate was not approved, and has a fallback
        changed = False
        for dest, idx in candidate_indices.items():
            if idx < len(dest_groups[dest]):
                cand_id = dest_groups[dest][idx]
                if cand_id not in approved and idx + 1 < len(dest_groups[dest]):
                    candidate_indices[dest] += 1
                    changed = True
        if not changed:
            break

    return requests, best_approved


# ====================================================================
# TEST CASES
# ====================================================================

def test_single_robot_empty_destination():
    robots = [build_test_robot("AMR-01", "A", "B")]
    requests, approved = resolve_simultaneous_moves_improved(robots)
    assert approved == {"AMR-01"}
    check_movement_safety(robots, approved, requests)


def test_two_robots_competing_for_same_destination():
    # AMR-01 at A wants B; AMR-02 at C wants B
    r1 = build_test_robot("AMR-01", "A", "B", waiting_steps=2)
    r2 = build_test_robot("AMR-02", "C", "B", waiting_steps=0)
    robots = [r1, r2]
    requests, approved = resolve_simultaneous_moves_improved(robots, time_step=0)
    # Higher waiting steps should win
    assert approved == {"AMR-01"}
    check_movement_safety(robots, approved, requests)


def test_head_on_swap_prevention():
    # AMR-01 at A wants B; AMR-02 at B wants A (head-on collision)
    r1 = build_test_robot("AMR-01", "A", "B")
    r2 = build_test_robot("AMR-02", "B", "A")
    robots = [r1, r2]
    requests, approved = resolve_simultaneous_moves_improved(robots)
    # Neither should move
    assert len(approved) == 0
    check_movement_safety(robots, approved, requests)


def test_three_robot_safe_rotation():
    # 3-robot cycle: A -> B -> C -> A
    r1 = build_test_robot("AMR-01", "A", "B")
    r2 = build_test_robot("AMR-02", "B", "C")
    r3 = build_test_robot("AMR-03", "C", "A")
    robots = [r1, r2, r3]
    requests, approved = resolve_simultaneous_moves_improved(robots)
    # All 3 should be approved safely
    assert approved == {"AMR-01", "AMR-02", "AMR-03"}
    check_movement_safety(robots, approved, requests)


def test_four_robot_safe_rotation():
    # 4-robot cycle: A -> B -> E -> D -> A
    r1 = build_test_robot("AMR-01", "A", "B")
    r2 = build_test_robot("AMR-02", "B", "E")
    r3 = build_test_robot("AMR-03", "E", "D")
    r4 = build_test_robot("AMR-04", "D", "A")
    robots = [r1, r2, r3, r4]
    requests, approved = resolve_simultaneous_moves_improved(robots)
    # All 4 should be approved safely
    assert approved == {"AMR-01", "AMR-02", "AMR-03", "AMR-04"}
    check_movement_safety(robots, approved, requests)


def test_movement_chain_ending_at_empty_node():
    # Chain: AMR-01 at A -> B, AMR-02 at B -> C, C is empty
    r1 = build_test_robot("AMR-01", "A", "B")
    r2 = build_test_robot("AMR-02", "B", "C")
    robots = [r1, r2]
    requests, approved = resolve_simultaneous_moves_improved(robots)
    # Both should be approved
    assert approved == {"AMR-01", "AMR-02"}
    check_movement_safety(robots, approved, requests)


def test_robot_blocked_by_stationary_robot():
    # AMR-01 at A wants B; AMR-02 at B is stationary (no request/completed)
    r1 = build_test_robot("AMR-01", "A", "B")
    r2 = build_test_robot("AMR-02", "B", None)  # stationary
    robots = [r1, r2]
    requests, approved = resolve_simultaneous_moves_improved(robots)
    # AMR-01 must not move
    assert len(approved) == 0
    check_movement_safety(robots, approved, requests)


def test_multiple_independent_movement_chains():
    # Chain 1: A -> B (B empty)
    # Chain 2: G -> H -> I (I empty)
    r1 = build_test_robot("AMR-01", "A", "B")
    r2 = build_test_robot("AMR-02", "G", "H")
    r3 = build_test_robot("AMR-03", "H", "I")
    robots = [r1, r2, r3]
    requests, approved = resolve_simultaneous_moves_improved(robots)
    assert approved == {"AMR-01", "AMR-02", "AMR-03"}
    check_movement_safety(robots, approved, requests)


def test_chain_blocked_at_tail():
    # AMR-01 at A -> B; AMR-02 at B -> C; AMR-03 at C -> D; AMR-04 at D stationary
    r1 = build_test_robot("AMR-01", "A", "B")
    r2 = build_test_robot("AMR-02", "B", "C")
    r3 = build_test_robot("AMR-03", "C", "D")
    r4 = build_test_robot("AMR-04", "D", None)
    robots = [r1, r2, r3, r4]
    requests, approved = resolve_simultaneous_moves_improved(robots)
    assert len(approved) == 0
    check_movement_safety(robots, approved, requests)


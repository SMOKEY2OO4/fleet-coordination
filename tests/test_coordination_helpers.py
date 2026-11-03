"""
Unit tests for multi-robot movement resolution.
Verifies safety, rotation cycles, chain movement, head-on swap prevention,
and collision avoidance under simultaneous discrete updates.
"""

import pytest


def check_movement_safety(robots, approved_moves, requests):
    """
    Independent invariant checker for simultaneous movement safety.
    Verifies across all active robots:
    1. No two robots occupy the same node after movement.
    2. No head-on edge swap occurs between any two robots.
    3. No robot moves into a node that was occupied and not vacated.
    4. Approved moves are a subset of requested moves.
    """
    active_robots = [r for r in robots if not r.get("completed", False)]
    initial_positions = {r["robot_id"]: r["current_node"] for r in active_robots}
    new_positions = {}

    for r in active_robots:
        rid = r["robot_id"]
        if rid in approved_moves:
            assert rid in requests, f"Robot {rid} approved without request"
            new_positions[rid] = requests[rid]
        else:
            new_positions[rid] = initial_positions[rid]

    # Invariant 1: Destination uniqueness / No node collisions
    seen_nodes = {}
    for rid, pos in new_positions.items():
        assert pos not in seen_nodes, (
            f"Collision at node {pos}: {seen_nodes[pos]} and {rid}"
        )
        seen_nodes[pos] = rid

    # Invariant 2: No head-on edge swap
    for r1 in active_robots:
        id1 = r1["robot_id"]
        if id1 not in approved_moves:
            continue
        u1, v1 = initial_positions[id1], new_positions[id1]
        for r2 in active_robots:
            id2 = r2["robot_id"]
            if id2 <= id1 or id2 not in approved_moves:
                continue
            u2, v2 = initial_positions[id2], new_positions[id2]
            assert not (u1 == v2 and v1 == u2), (
                f"Head-on edge swap between {id1} ({u1}->{v1}) and {id2} ({u2}->{v2})"
            )

    # Invariant 3: Vacated or empty destination
    for rid in approved_moves:
        dest = requests[rid]
        for other_id, init_pos in initial_positions.items():
            if other_id != rid and init_pos == dest:
                assert other_id in approved_moves, (
                    f"Robot {rid} moved into node {dest} which was occupied by stationary robot {other_id}"
                )


def build_test_robot(robot_id, current_node, next_node=None, waiting_steps=0):
    path = [current_node]
    if next_node:
        path.append(next_node)
    return {
        "robot_id": robot_id,
        "current_node": current_node,
        "path": path,
        "path_index": 0,
        "waiting_steps": waiting_steps,
        "total_waiting_steps": waiting_steps,
        "completed": False,
    }

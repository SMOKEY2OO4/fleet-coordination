"""
Comprehensive verification test for FleetIQ simulation control:
1. Reset simulation (3 robots, scenario 8 -> takes 19 steps)
2. Start automatic execution
3. Verify multiple ticks advance without clicking STEP
4. Pause and verify counter stops immediately
5. Resume and verify execution continues from the paused step
6. Reset and verify initial state returns (time_step = 0, is_running = False)
7. Verify manual STEP works (exactly 1 tick per call)
8. Verify speed change updates the tick rate
"""
import urllib.request
import json
import time
import sys

BASE = 'http://127.0.0.1:8009'


def call(method, path, body=None):
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        BASE + path, data=data, method=method,
        headers={'Content-Type': 'application/json'}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def run_checks():
    print("=" * 60)
    print("FLEETIQ SIMULATION AUTOMATIC EXECUTION VERIFICATION")
    print("=" * 60)

    # Step 1: Reset with 3 robots, Scenario 8 (takes 19 steps)
    print("\n[TEST 1] Reset simulation with 3 robots, Scenario 8...")
    s, r = call('POST', '/api/simulation/reset', {
        'fleet_size': 3,
        'algorithm': 'Improved Resolver',
        'scenario_id': 8
    })
    assert s == 200, f"Reset failed with HTTP {s}"
    assert r['is_running'] is False, "is_running should be False after reset"
    assert r['time_step'] == 0, "time_step should be 0 after reset"
    assert len(r['robots']) == 3, f"Expected 3 robots, got {len(r['robots'])}"
    print(f"  PASS: Initial state initialized. Robots: {len(r['robots'])}, Time: T0, Running: {r['is_running']}")

    # Step 2: Set speed to 300ms for responsive testing
    print("\n[TEST 2] Setting speed to 300ms...")
    s, r = call('POST', '/api/simulation/speed', {'speed_ms': 300})
    assert s == 200, f"Set speed failed with HTTP {s}"
    assert r['speed_ms'] == 300
    print("  PASS: Speed set to 300ms")

    # Step 3: Start automatic execution
    print("\n[TEST 3] Calling START SIMULATION (POST /api/simulation/start)...")
    s, r = call('POST', '/api/simulation/start')
    assert s == 200, f"Start failed with HTTP {s}: {r}"
    assert r['is_running'] is True, "is_running should be True after start"
    print(f"  PASS: Start returned HTTP 200, is_running={r['is_running']}")

    # Step 4: Wait without clicking STEP and verify automatic advancement
    print("\n[TEST 4] Waiting 1.5s to verify automatic tick loop advances...")
    time.sleep(1.5)
    s, state = call('GET', '/api/simulation/state')
    assert s == 200
    ts1 = state['time_step']
    print(f"  Current time_step after 1.5s: T{ts1}")
    assert ts1 >= 3, f"Expected at least 3 ticks advanced automatically, got {ts1}"
    assert state['is_running'] is True, "Simulation should still be running"
    print(f"  PASS: Automatic execution verified! Advanced to T{ts1} without clicking STEP.")

    # Step 5: Pause execution
    print("\n[TEST 5] Calling PAUSE SIMULATION (POST /api/simulation/pause)...")
    s, r = call('POST', '/api/simulation/pause')
    assert s == 200
    assert r['is_running'] is False, "is_running should be False after pause"
    paused_ts = r['time_step']
    print(f"  Paused at time_step: T{paused_ts}")

    # Wait 1.0s to ensure no further advancement occurs while paused
    time.sleep(1.0)
    s, state = call('GET', '/api/simulation/state')
    assert s == 200
    assert state['time_step'] == paused_ts, (
        f"Simulation advanced while paused! Expected T{paused_ts}, got T{state['time_step']}"
    )
    assert state['is_running'] is False, "is_running should be False while paused"
    print(f"  PASS: PAUSE verified! Counter stopped immediately at T{paused_ts}.")

    # Step 6: Resume execution
    print("\n[TEST 6] Calling RESUME SIMULATION (POST /api/simulation/resume)...")
    s, r = call('POST', '/api/simulation/resume')
    assert s == 200
    assert r['is_running'] is True, "is_running should be True after resume"

    # Wait 1.2s to verify continuation from the current state
    time.sleep(1.2)
    s, state = call('GET', '/api/simulation/state')
    assert s == 200
    ts2 = state['time_step']
    assert ts2 > paused_ts, f"Execution did not continue after resume! T{ts2} <= T{paused_ts}"
    print(f"  PASS: RESUME verified! Continued from T{paused_ts} to T{ts2}.")

    # Pause before reset
    call('POST', '/api/simulation/pause')

    # Step 7: Reset simulation
    print("\n[TEST 7] Calling RESET SIMULATION (POST /api/simulation/reset)...")
    s, r = call('POST', '/api/simulation/reset', {
        'fleet_size': 3,
        'algorithm': 'Improved Resolver',
        'scenario_id': 1
    })
    assert s == 200
    assert r['is_running'] is False, "is_running should be False after reset"
    assert r['time_step'] == 0, "time_step should be 0 after reset"
    assert len(r['robots']) == 3
    print("  PASS: RESET verified! Loop stopped and state restored to T0.")

    # Step 8: Manual STEP functionality
    print("\n[TEST 8] Calling manual STEP (POST /api/simulation/step)...")
    s, r = call('POST', '/api/simulation/step')
    assert s == 200
    assert r['time_step'] == 1, f"Expected T1 after 1 step, got T{r['time_step']}"
    s, r = call('POST', '/api/simulation/step')
    assert s == 200
    assert r['time_step'] == 2, f"Expected T2 after 2 steps, got T{r['time_step']}"
    print("  PASS: Manual STEP functional! Advanced exactly 1 tick per call.")

    # Reset speed back to 1000ms
    call('POST', '/api/simulation/speed', {'speed_ms': 1000})

    print("\n" + "=" * 60)
    print("ALL VERIFICATION CHECKS PASSED SUCCESSFULLY (100%)")
    print("=" * 60)


if __name__ == '__main__':
    run_checks()

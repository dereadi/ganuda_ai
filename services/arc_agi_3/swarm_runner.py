#!/usr/bin/env python3
"""
WOPR Swarm Runner — Parallel Game-Playing Across the Federation

Launches multiple agent instances per game with different random seeds.
Can run locally (multiprocess) or distributed across federation nodes.
All instances share experiences via the Experience Bank.

The Augusta Pattern applied to game-playing:
  Parallel instances, shared memory, strongest solutions propagate.

Usage:
    # 5 parallel instances of vc33 on local machine
    python swarm_runner.py vc33 --instances 5

    # All 25 games, 3 instances each
    python swarm_runner.py --all --instances 3

    # Distribute across federation (CPU-only, no LLM needed)
    python swarm_runner.py vc33 --instances 10 --distributed

    # Check which nodes are reachable
    python swarm_runner.py --status

    # Install deps on remote nodes
    python swarm_runner.py --setup-remote
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)

# Federation nodes for distributed execution
FEDERATION_NODES = {
    'redfin': {
        'host': 'localhost',
        'cores': 32,
        'usable_cores': 32,
        'has_gpu': True,
        'has_vllm': True,
        'has_mlx': False,
    },
    'bluefin': {
        'host': '10.100.0.2',
        'cores': 32,
        'usable_cores': 16,
        'has_gpu': False,
        'has_vllm': False,
        'has_mlx': False,
    },
    'bmasass': {
        'host': '192.168.132.100',
        'cores': 16,
        'usable_cores': 16,
        'has_gpu': False,
        'has_vllm': False,
        'has_mlx': True,
    },
}

AGENT_DIR = Path(__file__).parent
REMOTE_AGENT_DIR = '/ganuda/services/arc_agi_3'
VENV_PYTHON = AGENT_DIR / 'venv' / 'bin' / 'python'
REMOTE_VENV_PYTHON = f'{REMOTE_AGENT_DIR}/venv/bin/python'
RESULTS_DIR = AGENT_DIR / 'swarm_results'

# All 25 public games
ALL_GAMES = [
    'ls20', 'ka59', 'wa30', 're86', 'bp35', 'sp80', 'lf52', 'ft09',
    'sb26', 'lp85', 'm0r0', 'sk48', 'vc33', 'sc25', 'g50t', 'cn04',
    'r11l', 'dc22', 'tu93', 's5i5', 'ar25', 'su15', 'tn36', 'tr87', 'cd82',
]

# SSH options for non-interactive, timeout-aware connections
SSH_OPTS = [
    '-o', 'BatchMode=yes',
    '-o', 'ConnectTimeout=10',
    '-o', 'StrictHostKeyChecking=accept-new',
]


# ---------------------------------------------------------------------------
# Node status / health checks
# ---------------------------------------------------------------------------

def check_node_status(node_name: str, node_cfg: dict) -> dict:
    """Check if a federation node is reachable and ready."""
    host = node_cfg['host']
    result = {
        'node': node_name,
        'host': host,
        'reachable': False,
        'venv_ready': False,
        'arc_agi_ready': False,
        'error': None,
    }

    if host == 'localhost':
        result['reachable'] = True
        result['venv_ready'] = VENV_PYTHON.exists()
        result['arc_agi_ready'] = (AGENT_DIR / 'ganuda_agent.py').exists()
        return result

    # SSH connectivity
    try:
        proc = subprocess.run(
            ['ssh'] + SSH_OPTS + [host, 'echo OK'],
            capture_output=True, text=True, timeout=15,
        )
        if proc.returncode != 0:
            result['error'] = proc.stderr.strip()[:100]
            return result
        result['reachable'] = True
    except (subprocess.TimeoutExpired, Exception) as e:
        result['error'] = str(e)[:100]
        return result

    # Check venv
    try:
        proc = subprocess.run(
            ['ssh'] + SSH_OPTS + [host,
             f'test -x {REMOTE_VENV_PYTHON} && echo VENV_OK'],
            capture_output=True, text=True, timeout=15,
        )
        result['venv_ready'] = 'VENV_OK' in proc.stdout
    except Exception:
        pass

    # Check arc_agi package
    try:
        proc = subprocess.run(
            ['ssh'] + SSH_OPTS + [host,
             f'test -f {REMOTE_AGENT_DIR}/ganuda_agent.py && echo AGENT_OK'],
            capture_output=True, text=True, timeout=15,
        )
        result['arc_agi_ready'] = 'AGENT_OK' in proc.stdout
    except Exception:
        pass

    return result


def print_federation_status():
    """Check and print status of all federation nodes."""
    print(f"\n{'='*65}")
    print(f"  FEDERATION NODE STATUS — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*65}")

    with ThreadPoolExecutor(max_workers=len(FEDERATION_NODES)) as pool:
        futures = {
            pool.submit(check_node_status, name, cfg): name
            for name, cfg in FEDERATION_NODES.items()
        }
        statuses = {}
        for f in as_completed(futures):
            s = f.result()
            statuses[s['node']] = s

    for name in FEDERATION_NODES:
        s = statuses[name]
        cfg = FEDERATION_NODES[name]
        reach = 'OK' if s['reachable'] else 'UNREACHABLE'
        venv = 'OK' if s['venv_ready'] else 'MISSING'
        agent = 'OK' if s['arc_agi_ready'] else 'MISSING'
        gpu_str = 'GPU+vLLM' if cfg['has_vllm'] else ('MLX' if cfg['has_mlx'] else 'CPU-only')
        cores_str = f"{cfg['usable_cores']}/{cfg['cores']} cores"

        status_icon = '+' if (s['reachable'] and s['venv_ready'] and s['arc_agi_ready']) else '-'
        print(f"  [{status_icon}] {name:12s} ({s['host']:>24s})  "
              f"ssh={reach:11s} venv={venv:7s} agent={agent:7s}  "
              f"{cores_str:14s}  {gpu_str}")
        if s['error']:
            print(f"      err: {s['error']}")

    print(f"{'='*65}\n")


# ---------------------------------------------------------------------------
# Remote setup
# ---------------------------------------------------------------------------

def setup_remote_node(node_name: str, node_cfg: dict) -> bool:
    """Install dependencies on a remote node via SSH."""
    host = node_cfg['host']
    if host == 'localhost':
        logger.info(f"  {node_name}: localhost — skipping remote setup")
        return True

    logger.info(f"  {node_name}: setting up on {host}...")

    setup_script = f"""
set -e
echo "--- Creating venv ---"
cd {REMOTE_AGENT_DIR}
if [ ! -d venv ]; then
    python3 -m venv venv
fi
echo "--- Installing dependencies ---"
{REMOTE_VENV_PYTHON} -m pip install --upgrade pip -q
if [ -f requirements.txt ]; then
    {REMOTE_VENV_PYTHON} -m pip install -r requirements.txt -q
fi
# Install arc_agi if setup.py or pyproject.toml exists
if [ -f setup.py ] || [ -f pyproject.toml ]; then
    {REMOTE_VENV_PYTHON} -m pip install -e . -q 2>/dev/null || true
fi
echo "SETUP_COMPLETE"
"""

    try:
        proc = subprocess.run(
            ['ssh'] + SSH_OPTS + [host, 'bash -s'],
            input=setup_script,
            capture_output=True, text=True, timeout=300,
        )
        if 'SETUP_COMPLETE' in proc.stdout:
            logger.info(f"  {node_name}: setup complete")
            return True
        else:
            logger.error(f"  {node_name}: setup failed — {proc.stderr[-200:]}")
            return False
    except subprocess.TimeoutExpired:
        logger.error(f"  {node_name}: setup timed out (5 min)")
        return False
    except Exception as e:
        logger.error(f"  {node_name}: setup error — {e}")
        return False


def setup_all_remote_nodes():
    """Run setup on all non-localhost federation nodes."""
    logger.info("Setting up remote federation nodes...")
    with ThreadPoolExecutor(max_workers=len(FEDERATION_NODES)) as pool:
        futures = {
            pool.submit(setup_remote_node, name, cfg): name
            for name, cfg in FEDERATION_NODES.items()
        }
        for f in as_completed(futures):
            f.result()  # logs internally
    logger.info("Remote setup complete.")


# ---------------------------------------------------------------------------
# Single agent execution (local + remote)
# ---------------------------------------------------------------------------

def run_single_agent(game_id: str, max_actions: int, seed: int,
                     instance_id: int, disable_llm: bool = False) -> dict:
    """Run a single agent instance as a subprocess (local).

    Returns a result dict with game_id, levels_completed, actions, timing, etc.
    """
    start = time.time()

    # Build the agent command — disable LLM for CPU-only parallel runs
    cmd = [
        str(VENV_PYTHON), '-c', f'''
import sys, os, random
sys.path.insert(0, "{AGENT_DIR}")
os.environ["PYTHONHASHSEED"] = "{seed}"
random.seed({seed})

# Disable LLM if requested (CPU-only exploration)
if {disable_llm}:
    import ganuda_agent
    ganuda_agent.CWM_AVAILABLE = False
    ganuda_agent.GOAL_AVAILABLE = False

from ganuda_agent import GanudaAgent
from arcengine import FrameData, GameAction, GameState
from arc_agi import Arcade

arcade = Arcade()
env = arcade.make("{game_id}")
agent = GanudaAgent(game_id="{game_id}")

obs = env.observation_space
frame = FrameData(game_id=obs.game_id, frame=[arr.tolist() for arr in obs.frame],
    state=obs.state, levels_completed=obs.levels_completed, win_levels=obs.win_levels,
    guid=obs.guid, full_reset=obs.full_reset, available_actions=obs.available_actions)

level_ups = []
game_overs = 0
for i in range({max_actions}):
    action = agent.choose_action(frame)
    data = action.action_data.model_dump() if action.is_complex() else {{}}
    raw = env.step(action, data=data, reasoning={{}})
    frame = FrameData(game_id=raw.game_id, frame=[arr.tolist() for arr in raw.frame],
        state=raw.state, levels_completed=raw.levels_completed, win_levels=raw.win_levels,
        guid=raw.guid, full_reset=raw.full_reset, available_actions=raw.available_actions)
    if frame.levels_completed > len(level_ups):
        level_ups.append(i + 1)
    if frame.state == GameState.GAME_OVER:
        game_overs += 1
    if agent.is_done(frame):
        break

import json
print("SWARM_RESULT:" + json.dumps({{
    "game_id": "{game_id}",
    "seed": {seed},
    "instance": {instance_id},
    "levels": frame.levels_completed,
    "actions": i + 1,
    "level_up_actions": level_ups,
    "game_overs": game_overs,
    "won": frame.state == GameState.WIN,
}}))
'''
    ]

    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=300, cwd=str(AGENT_DIR)
        )

        # Parse result from stdout
        for line in proc.stdout.split('\n'):
            if line.startswith('SWARM_RESULT:'):
                result = json.loads(line[len('SWARM_RESULT:'):])
                result['elapsed'] = round(time.time() - start, 1)
                result['error'] = None
                result['node'] = 'redfin'
                return result

        # No result line found
        return {
            'game_id': game_id, 'seed': seed, 'instance': instance_id,
            'levels': 0, 'actions': 0, 'elapsed': round(time.time() - start, 1),
            'error': proc.stderr[-200:] if proc.stderr else 'no result',
            'node': 'redfin',
        }

    except subprocess.TimeoutExpired:
        return {
            'game_id': game_id, 'seed': seed, 'instance': instance_id,
            'levels': 0, 'actions': max_actions, 'elapsed': 300,
            'error': 'timeout', 'node': 'redfin',
        }
    except Exception as e:
        return {
            'game_id': game_id, 'seed': seed, 'instance': instance_id,
            'levels': 0, 'actions': 0, 'elapsed': round(time.time() - start, 1),
            'error': str(e), 'node': 'redfin',
        }


def run_remote_agent(node_name: str, host: str, game_id: str,
                     max_actions: int, seed: int, instance_id: int,
                     disable_llm: bool = True) -> dict:
    """Run a single agent instance on a remote node via SSH.

    Returns a result dict matching the local format.
    """
    start = time.time()

    # Build the remote python snippet — same logic as local but runs over SSH
    disable_flag = 'True' if disable_llm else 'False'
    python_script = f"""
import sys, os, random, json
sys.path.insert(0, "{REMOTE_AGENT_DIR}")
os.environ["PYTHONHASHSEED"] = "{seed}"
random.seed({seed})

if {disable_flag}:
    import ganuda_agent
    ganuda_agent.CWM_AVAILABLE = False
    ganuda_agent.GOAL_AVAILABLE = False

from ganuda_agent import GanudaAgent
from arcengine import FrameData, GameAction, GameState
from arc_agi import Arcade

arcade = Arcade()
env = arcade.make("{game_id}")
agent = GanudaAgent(game_id="{game_id}")

obs = env.observation_space
frame = FrameData(game_id=obs.game_id, frame=[arr.tolist() for arr in obs.frame],
    state=obs.state, levels_completed=obs.levels_completed, win_levels=obs.win_levels,
    guid=obs.guid, full_reset=obs.full_reset, available_actions=obs.available_actions)

level_ups = []
game_overs = 0
for i in range({max_actions}):
    action = agent.choose_action(frame)
    data = action.action_data.model_dump() if action.is_complex() else {{}}
    raw = env.step(action, data=data, reasoning={{}})
    frame = FrameData(game_id=raw.game_id, frame=[arr.tolist() for arr in raw.frame],
        state=raw.state, levels_completed=raw.levels_completed, win_levels=raw.win_levels,
        guid=raw.guid, full_reset=raw.full_reset, available_actions=raw.available_actions)
    if frame.levels_completed > len(level_ups):
        level_ups.append(i + 1)
    if frame.state == GameState.GAME_OVER:
        game_overs += 1
    if agent.is_done(frame):
        break

print("SWARM_RESULT:" + json.dumps({{
    "game_id": "{game_id}",
    "seed": {seed},
    "instance": {instance_id},
    "levels": frame.levels_completed,
    "actions": i + 1,
    "level_up_actions": level_ups,
    "game_overs": game_overs,
    "won": frame.state == GameState.WIN,
}}))
"""

    ssh_cmd = [
        'ssh'] + SSH_OPTS + [
        host,
        f'cd {REMOTE_AGENT_DIR} && {REMOTE_VENV_PYTHON} -c {_shell_quote(python_script)} 2>&1',
    ]

    try:
        proc = subprocess.run(
            ssh_cmd, capture_output=True, text=True, timeout=360,
        )

        # Parse result from stdout (same marker as local)
        for line in proc.stdout.split('\n'):
            if line.startswith('SWARM_RESULT:'):
                result = json.loads(line[len('SWARM_RESULT:'):])
                result['elapsed'] = round(time.time() - start, 1)
                result['error'] = None
                result['node'] = node_name
                return result

        # Check for "Levels completed:" fallback pattern in output
        levels = 0
        for line in proc.stdout.split('\n'):
            if 'Levels completed:' in line:
                try:
                    levels = int(line.split('Levels completed:')[1].strip())
                except (ValueError, IndexError):
                    pass

        return {
            'game_id': game_id, 'seed': seed, 'instance': instance_id,
            'levels': levels, 'actions': 0,
            'elapsed': round(time.time() - start, 1),
            'error': (proc.stdout + proc.stderr)[-200:] if levels == 0 else None,
            'node': node_name,
        }

    except subprocess.TimeoutExpired:
        return {
            'game_id': game_id, 'seed': seed, 'instance': instance_id,
            'levels': 0, 'actions': max_actions, 'elapsed': 360,
            'error': 'timeout', 'node': node_name,
        }
    except Exception as e:
        return {
            'game_id': game_id, 'seed': seed, 'instance': instance_id,
            'levels': 0, 'actions': 0, 'elapsed': round(time.time() - start, 1),
            'error': str(e), 'node': node_name,
        }


def _shell_quote(script: str) -> str:
    """Quote a Python script for passing through SSH as a -c argument."""
    import shlex
    return shlex.quote(script)


# ---------------------------------------------------------------------------
# Work distribution
# ---------------------------------------------------------------------------

def distribute_tasks(games: list, instances_per_game: int,
                     reachable_nodes: dict) -> dict:
    """Split tasks across nodes proportional to their usable core count.

    redfin (or any node with vLLM) gets LLM-enabled runs.
    Other nodes get CPU-only (disable_llm=True) runs.

    Returns: {node_name: [(game_id, seed, instance_id, disable_llm), ...]}
    """
    # Build flat task list
    all_tasks = []
    for game_id in games:
        for i in range(instances_per_game):
            seed = hash(f"{game_id}_{i}_{time.time()}") % (2**31)
            all_tasks.append((game_id, seed, i))

    total_tasks = len(all_tasks)
    if total_tasks == 0:
        return {}

    # Calculate proportional share based on usable cores
    total_cores = sum(
        FEDERATION_NODES[n]['usable_cores'] for n in reachable_nodes
    )
    if total_cores == 0:
        total_cores = 1

    node_assignments = {}
    assigned = 0

    node_list = sorted(reachable_nodes.keys())
    for idx, node_name in enumerate(node_list):
        cfg = FEDERATION_NODES[node_name]
        if idx == len(node_list) - 1:
            # Last node gets remainder to avoid rounding losses
            share = total_tasks - assigned
        else:
            share = max(1, round(total_tasks * cfg['usable_cores'] / total_cores))
            share = min(share, total_tasks - assigned)

        disable_llm = not cfg.get('has_vllm', False)
        node_tasks = []
        for task in all_tasks[assigned:assigned + share]:
            game_id, seed, inst_id = task
            node_tasks.append((game_id, seed, inst_id, disable_llm))

        node_assignments[node_name] = node_tasks
        assigned += share

    return node_assignments


# ---------------------------------------------------------------------------
# Swarm runners (local + distributed)
# ---------------------------------------------------------------------------

def run_swarm(games: list, instances_per_game: int, max_actions: int,
              max_workers: int, disable_llm: bool = False) -> list:
    """Run multiple agent instances in parallel using ProcessPoolExecutor (local only)."""
    RESULTS_DIR.mkdir(exist_ok=True)

    tasks = []
    for game_id in games:
        for i in range(instances_per_game):
            seed = hash(f"{game_id}_{i}_{time.time()}") % (2**31)
            tasks.append((game_id, max_actions, seed, i, disable_llm))

    logger.info(f"Launching {len(tasks)} agent instances across {len(games)} games "
                f"({instances_per_game} per game, {max_workers} workers)")

    results = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(run_single_agent, *task): task
            for task in tasks
        }

        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            status = f"L{result.get('levels', 0)}"
            if result.get('error'):
                status = f"ERR:{result['error'][:30]}"
            elif result.get('won'):
                status = "WIN!"
            logger.info(f"  {result['game_id']}#{result.get('instance',0)}: "
                       f"{status} in {result.get('actions',0)} actions "
                       f"({result.get('elapsed',0)}s)")

    return results


def run_distributed_swarm(games: list, instances_per_game: int,
                          max_actions: int) -> list:
    """Run agent instances distributed across federation nodes via SSH.

    Uses ThreadPoolExecutor since work is I/O-bound (SSH subprocesses).
    redfin tasks run locally; others run over SSH.
    """
    RESULTS_DIR.mkdir(exist_ok=True)

    # Discover reachable nodes
    logger.info("Checking federation node availability...")
    reachable = {}
    with ThreadPoolExecutor(max_workers=len(FEDERATION_NODES)) as pool:
        futures = {
            pool.submit(check_node_status, name, cfg): name
            for name, cfg in FEDERATION_NODES.items()
        }
        for f in as_completed(futures):
            s = f.result()
            if s['reachable'] and s['venv_ready'] and s['arc_agi_ready']:
                reachable[s['node']] = FEDERATION_NODES[s['node']]
                logger.info(f"  {s['node']}: READY ({FEDERATION_NODES[s['node']]['usable_cores']} cores)")
            else:
                reason = 'unreachable' if not s['reachable'] else (
                    'no venv' if not s['venv_ready'] else 'no agent')
                logger.warning(f"  {s['node']}: SKIPPED ({reason})")

    if not reachable:
        logger.error("No federation nodes available. Aborting.")
        return []

    # Distribute work
    assignments = distribute_tasks(games, instances_per_game, reachable)

    total_tasks = sum(len(t) for t in assignments.values())
    logger.info(f"Distributed {total_tasks} tasks across {len(assignments)} nodes:")
    for node_name, tasks in assignments.items():
        llm_mode = "LLM-enabled" if not tasks[0][3] else "CPU-only"
        logger.info(f"  {node_name}: {len(tasks)} tasks ({llm_mode})")

    # Launch all tasks — use threads since each task is a subprocess (or SSH)
    max_threads = sum(
        min(FEDERATION_NODES[n]['usable_cores'], len(assignments.get(n, [])))
        for n in reachable
    )
    max_threads = max(1, min(max_threads, 64))

    results = []
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = {}
        for node_name, tasks in assignments.items():
            cfg = FEDERATION_NODES[node_name]
            host = cfg['host']

            for game_id, seed, inst_id, disable_llm in tasks:
                if host == 'localhost':
                    fut = executor.submit(
                        run_single_agent, game_id, max_actions,
                        seed, inst_id, disable_llm,
                    )
                else:
                    fut = executor.submit(
                        run_remote_agent, node_name, host,
                        game_id, max_actions, seed, inst_id, disable_llm,
                    )
                futures[fut] = (node_name, game_id, inst_id)

        for future in as_completed(futures):
            node_name, game_id, inst_id = futures[future]
            try:
                result = future.result()
            except Exception as e:
                result = {
                    'game_id': game_id, 'seed': 0, 'instance': inst_id,
                    'levels': 0, 'actions': 0, 'elapsed': 0,
                    'error': str(e), 'node': node_name,
                }

            results.append(result)
            status = f"L{result.get('levels', 0)}"
            if result.get('error'):
                status = f"ERR:{result['error'][:30]}"
            elif result.get('won'):
                status = "WIN!"
            logger.info(f"  [{result.get('node','?'):8s}] "
                       f"{result['game_id']}#{result.get('instance',0)}: "
                       f"{status} in {result.get('actions',0)} actions "
                       f"({result.get('elapsed',0)}s)")

    return results


# ---------------------------------------------------------------------------
# Scoreboard
# ---------------------------------------------------------------------------

def print_scoreboard(results: list):
    """Print a summary scoreboard."""
    print(f"\n{'='*60}")
    print(f"WOPR SWARM SCOREBOARD -- {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}")

    # Group by game
    by_game = {}
    for r in results:
        gid = r['game_id']
        if gid not in by_game:
            by_game[gid] = []
        by_game[gid].append(r)

    total_levels = 0
    total_instances = len(results)
    games_with_solves = 0

    # Node contribution summary
    by_node = {}
    for r in results:
        node = r.get('node', 'unknown')
        if node not in by_node:
            by_node[node] = {'tasks': 0, 'levels': 0, 'errors': 0}
        by_node[node]['tasks'] += 1
        by_node[node]['levels'] += r.get('levels', 0)
        if r.get('error'):
            by_node[node]['errors'] += 1

    for game_id in sorted(by_game.keys()):
        runs = by_game[game_id]
        best = max(r.get('levels', 0) for r in runs)
        avg_levels = sum(r.get('levels', 0) for r in runs) / len(runs)
        errors = sum(1 for r in runs if r.get('error'))
        total_levels += best

        if best > 0:
            games_with_solves += 1
            # Find best run details
            best_run = max(runs, key=lambda r: (r.get('levels', 0), -r.get('actions', 9999)))
            level_actions = best_run.get('level_up_actions', [])
            action_str = ','.join(str(a) for a in level_actions) if level_actions else '?'
            node_str = f" [{best_run.get('node', '?')}]" if best_run.get('node') else ''
            print(f"  {game_id}: BEST={best} levels (actions: {action_str}){node_str} "
                  f"| avg={avg_levels:.1f} | {len(runs)} runs, {errors} errors")
        else:
            print(f"  {game_id}: 0 levels | {len(runs)} runs, {errors} errors")

    print(f"\n{'='*60}")
    print(f"  Games with solves: {games_with_solves}/{len(by_game)}")
    print(f"  Total best levels: {total_levels}")
    print(f"  Total instances: {total_instances}")

    # Print node contributions if distributed
    if len(by_node) > 1 or (len(by_node) == 1 and 'redfin' not in by_node):
        print(f"\n  Node contributions:")
        for node in sorted(by_node.keys()):
            n = by_node[node]
            print(f"    {node:12s}: {n['tasks']:3d} tasks, "
                  f"{n['levels']:3d} total levels, {n['errors']} errors")

    print(f"{'='*60}")

    # Save results
    results_file = RESULTS_DIR / f"swarm_{datetime.now().strftime('%Y%m%dT%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n  Results saved: {results_file}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='WOPR Swarm Runner')
    parser.add_argument('games', nargs='*', default=[], help='Game IDs to play')
    parser.add_argument('--all', action='store_true', help='Play all 25 public games')
    parser.add_argument('--instances', type=int, default=3, help='Instances per game')
    parser.add_argument('--actions', type=int, default=3000, help='Max actions per instance')
    parser.add_argument('--workers', type=int, default=5, help='Max parallel workers (local mode)')
    parser.add_argument('--no-llm', action='store_true', help='Disable LLM (CPU-only exploration)')
    parser.add_argument('--distributed', action='store_true',
                        help='Distribute work across federation nodes via SSH')
    parser.add_argument('--status', action='store_true',
                        help='Check which federation nodes are reachable')
    parser.add_argument('--setup-remote', action='store_true',
                        help='Install venv and deps on remote federation nodes')
    args = parser.parse_args()

    # Status check mode
    if args.status:
        print_federation_status()
        return

    # Remote setup mode
    if args.setup_remote:
        setup_all_remote_nodes()
        return

    games = ALL_GAMES if args.all else (args.games or ['vc33'])

    if args.distributed:
        results = run_distributed_swarm(
            games=games,
            instances_per_game=args.instances,
            max_actions=args.actions,
        )
    else:
        results = run_swarm(
            games=games,
            instances_per_game=args.instances,
            max_actions=args.actions,
            max_workers=args.workers,
            disable_llm=args.no_llm,
        )

    if results:
        print_scoreboard(results)
    else:
        logger.error("No results collected.")


if __name__ == '__main__':
    main()

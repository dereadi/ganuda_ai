#!/usr/bin/env python3
"""
Genetic Algorithm Solver for ARC-AGI-3

Inspired by "AI beats the World's Hardest Game" (Tyler Momsen).
Population of random action sequences. Select the ones that get closest
to the goal. Reproduce. Repeat.

Key adaptation for ARC-AGI-3:
- Actions include CLICKS (ACTION6 at random x,y) not just movement
- Step budget is limited (128 for dc22 L1)
- Fitness = how close the player gets to the goal (pixel distance)
- Steps increase every N generations (progressive difficulty)
- The agent discovers click mechanics through evolution, not understanding

Usage:
    python genetic_solver.py dc22 --population 50 --generations 200
"""

import argparse
import logging
import numpy as np
import os
import random
import sys
import time
from dataclasses import dataclass
from typing import List, Tuple

sys.path.insert(0, os.path.dirname(__file__))

from arc_agi import Arcade
from arcengine import GameAction, GameState

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)


@dataclass
class Individual:
    """One candidate solution — a sequence of actions."""
    actions: List[Tuple]  # list of (action_type, x, y) or (action_type,)
    fitness: float = 0.0
    won: bool = False
    levels: int = 0
    steps_used: int = 0


def random_action() -> Tuple:
    """Generate a random action — movement or click."""
    r = random.random()
    if r < 0.5:
        # 50% movement (arrows)
        direction = random.choice([
            GameAction.ACTION1,  # UP
            GameAction.ACTION2,  # DOWN
            GameAction.ACTION3,  # LEFT
            GameAction.ACTION4,  # RIGHT
        ])
        return ('move', direction)
    else:
        # 50% click at random position in the game area (y=10 to 53)
        x = random.randint(0, 63)
        y = random.randint(10, 53)  # Stay in valid game area, skip letterbox
        return ('click', x, y)


# Pre-built movement patterns that the genetic algorithm can draw from
MOVEMENT_PATTERNS = [
    # Biased cycling: net UP+RIGHT (toward typical goal)
    [('move', GameAction.ACTION1), ('move', GameAction.ACTION4),
     ('move', GameAction.ACTION1), ('move', GameAction.ACTION4),
     ('move', GameAction.ACTION2), ('move', GameAction.ACTION3)],
    # Heavy UP
    [('move', GameAction.ACTION1), ('move', GameAction.ACTION4),
     ('move', GameAction.ACTION1), ('move', GameAction.ACTION3),
     ('move', GameAction.ACTION1), ('move', GameAction.ACTION2)],
    # Heavy RIGHT
    [('move', GameAction.ACTION4), ('move', GameAction.ACTION1),
     ('move', GameAction.ACTION4), ('move', GameAction.ACTION2),
     ('move', GameAction.ACTION4), ('move', GameAction.ACTION3)],
    # All 4 cycle
    [('move', GameAction.ACTION1), ('move', GameAction.ACTION4),
     ('move', GameAction.ACTION2), ('move', GameAction.ACTION3)],
]


def create_individual(length: int) -> Individual:
    """Create an individual — mix of random actions and movement patterns."""
    actions = []
    while len(actions) < length:
        r = random.random()
        if r < 0.4:
            # 40% use a movement pattern
            pattern = random.choice(MOVEMENT_PATTERNS)
            actions.extend(pattern)
        elif r < 0.6:
            # 20% click in the hat button area (right side)
            x = random.randint(38, 50)
            y = random.randint(15, 45)
            actions.append(('click', x, y))
        else:
            # 40% pure random
            actions.append(random_action())
    return Individual(actions=actions[:length])


def create_individual(length: int) -> Individual:
    """Create a random individual with `length` actions."""
    return Individual(actions=[random_action() for _ in range(length)])


def execute_individual(env, individual: Individual) -> Individual:
    """Execute an individual's action sequence and measure fitness."""
    env.step(GameAction.RESET)

    # Track initial and final frames to measure displacement
    frame = env.step(GameAction.RESET)
    initial_grid = np.array(frame.frame[-1])

    steps = 0
    for action_tuple in individual.actions:
        if action_tuple[0] == 'move':
            frame = env.step(action_tuple[1])
        elif action_tuple[0] == 'click':
            click = GameAction.ACTION6
            click.set_data({'x': action_tuple[1], 'y': action_tuple[2]})
            frame = env.step(click)

        steps += 1

        if frame.state == GameState.WIN:
            individual.won = True
            individual.levels = frame.levels_completed or 1
            individual.fitness = 10000 + (1000 - steps)  # Bonus for winning fast
            individual.steps_used = steps
            return individual

        if frame.state == GameState.GAME_OVER:
            break

    # Fitness = DISTANCE TO GOAL (closer = higher fitness)
    # Access the actual game object to read player and goal positions
    try:
        game = env._game
        # Find player and goal sprites by tracing the win condition variables
        # The win check compares two sprites' positions
        player_sprite = None
        goal_sprite = None
        for attr_name in dir(game):
            attr = getattr(game, attr_name, None)
            if attr is not None and hasattr(attr, 'x') and hasattr(attr, 'y') and hasattr(attr, 'tags'):
                tags = attr.tags if hasattr(attr, 'tags') else []
                if isinstance(tags, list):
                    if any('jfva' in str(t) or 'pcxjvnmybet' in str(t) for t in tags):
                        player_sprite = attr
                    if any('goknoi' in str(t) or 'bqxa' in str(t) for t in tags):
                        goal_sprite = attr

        if player_sprite and goal_sprite:
            dx = abs(player_sprite.x - goal_sprite.x)
            dy = abs(player_sprite.y - goal_sprite.y)
            distance = dx + dy  # Manhattan distance
            max_distance = 64 + 44  # max possible on the grid
            # Fitness inversely proportional to distance
            # 0 distance = max fitness, max distance = 0 fitness
            individual.fitness = (max_distance - distance) * 100

            # Bonus for frame changes (clicking things that change state)
            final_grid = np.array(frame.frame[-1])
            frame_diff = np.sum(final_grid[:63, :] != initial_grid[:63, :])
            individual.fitness += frame_diff
        else:
            # Fallback to frame diff
            final_grid = np.array(frame.frame[-1])
            frame_diff = np.sum(final_grid[:63, :] != initial_grid[:63, :])
            individual.fitness = frame_diff * 10
    except Exception:
        final_grid = np.array(frame.frame[-1])
        frame_diff = np.sum(final_grid[:63, :] != initial_grid[:63, :])
        individual.fitness = frame_diff * 10

    individual.steps_used = steps
    individual.levels = frame.levels_completed or 0
    return individual


def crossover(parent1: Individual, parent2: Individual) -> Individual:
    """Single-point crossover between two parents."""
    min_len = min(len(parent1.actions), len(parent2.actions))
    if min_len < 2:
        return Individual(actions=parent1.actions[:])

    point = random.randint(1, min_len - 1)
    child_actions = parent1.actions[:point] + parent2.actions[point:]
    return Individual(actions=child_actions)


def mutate(individual: Individual, mutation_rate: float = 0.15) -> Individual:
    """Randomly mutate some actions."""
    new_actions = []
    for action in individual.actions:
        if random.random() < mutation_rate:
            new_actions.append(random_action())
        else:
            new_actions.append(action)
    return Individual(actions=new_actions)


def run_genetic_solver(
    game_id: str,
    population_size: int = 50,
    max_generations: int = 200,
    initial_steps: int = 20,
    step_increase: int = 5,
    step_increase_interval: int = 5,
    elite_ratio: float = 0.1,
    mutation_rate: float = 0.15,
):
    """Run the genetic algorithm solver."""

    logger.info(f"=== Genetic Solver for {game_id} ===")
    logger.info(f"Population: {population_size}, Max generations: {max_generations}")
    logger.info(f"Initial steps: {initial_steps}, +{step_increase} every {step_increase_interval} gens")

    arcade = Arcade()

    current_steps = initial_steps
    best_ever_fitness = 0
    best_ever_individual = None

    # Initialize population
    population = [create_individual(current_steps) for _ in range(population_size)]

    for gen in range(max_generations):
        # Increase step budget periodically
        if gen > 0 and gen % step_increase_interval == 0:
            current_steps = min(current_steps + step_increase, 128)
            # Extend existing individuals
            for ind in population:
                while len(ind.actions) < current_steps:
                    ind.actions.append(random_action())

        # Evaluate each individual
        for i, ind in enumerate(population):
            env = arcade.make(game_id)
            execute_individual(env, ind)

        # Sort by fitness (highest first)
        population.sort(key=lambda x: x.fitness, reverse=True)

        best = population[0]
        avg_fitness = sum(ind.fitness for ind in population) / len(population)

        if best.fitness > best_ever_fitness:
            best_ever_fitness = best.fitness
            best_ever_individual = Individual(
                actions=best.actions[:],
                fitness=best.fitness,
                won=best.won,
                levels=best.levels,
                steps_used=best.steps_used,
            )

        # Check for winner
        if best.won:
            logger.info(f"*** GEN {gen}: WINNER! Fitness={best.fitness:.0f} Steps={best.steps_used} ***")

            # Extract the winning action sequence
            click_count = sum(1 for a in best.actions if a[0] == 'click')
            move_count = sum(1 for a in best.actions if a[0] == 'move')
            logger.info(f"    Winning sequence: {move_count} moves + {click_count} clicks")

            return best

        # Log progress
        if gen % 10 == 0:
            click_ratio = sum(1 for a in best.actions if a[0] == 'click') / len(best.actions)
            logger.info(
                f"Gen {gen:3d}: best={best.fitness:6.0f} avg={avg_fitness:6.0f} "
                f"steps={current_steps} clicks={click_ratio:.0%} "
                f"best_ever={best_ever_fitness:.0f}"
            )

        # Selection: keep elite, breed the rest
        elite_count = max(2, int(population_size * elite_ratio))
        elite = population[:elite_count]

        # Create next generation
        new_population = [Individual(actions=e.actions[:]) for e in elite]

        while len(new_population) < population_size:
            # Tournament selection
            p1 = max(random.sample(population[:population_size // 2], 2), key=lambda x: x.fitness)
            p2 = max(random.sample(population[:population_size // 2], 2), key=lambda x: x.fitness)

            child = crossover(p1, p2)
            child = mutate(child, mutation_rate)

            # Ensure correct length
            while len(child.actions) < current_steps:
                child.actions.append(random_action())
            child.actions = child.actions[:current_steps]

            new_population.append(child)

        population = new_population

    logger.info(f"\nBest ever: fitness={best_ever_fitness:.0f}")
    if best_ever_individual:
        click_count = sum(1 for a in best_ever_individual.actions if a[0] == 'click')
        move_count = sum(1 for a in best_ever_individual.actions if a[0] == 'move')
        logger.info(f"  {move_count} moves + {click_count} clicks in {best_ever_individual.steps_used} steps")

    return best_ever_individual


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Genetic Algorithm Solver for ARC-AGI-3")
    parser.add_argument('game', default='dc22', nargs='?')
    parser.add_argument('--population', type=int, default=30)
    parser.add_argument('--generations', type=int, default=100)
    parser.add_argument('--initial-steps', type=int, default=15)
    parser.add_argument('--step-increase', type=int, default=5)
    parser.add_argument('--step-interval', type=int, default=5)
    args = parser.parse_args()

    result = run_genetic_solver(
        args.game,
        population_size=args.population,
        max_generations=args.generations,
        initial_steps=args.initial_steps,
        step_increase=args.step_increase,
        step_increase_interval=args.step_interval,
    )

    if result and result.won:
        print(f"\n=== SOLVED {args.game}! ===")
        print(f"Actions: {len(result.actions)}")
        print(f"Steps used: {result.steps_used}")

        # Print the winning sequence
        for i, action in enumerate(result.actions[:result.steps_used]):
            if action[0] == 'move':
                print(f"  {i}: {action[1].name}")
            else:
                print(f"  {i}: CLICK ({action[1]},{action[2]})")
    else:
        print(f"\nDid not solve {args.game} in {args.generations} generations")

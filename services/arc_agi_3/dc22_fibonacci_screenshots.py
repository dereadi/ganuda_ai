#!/usr/bin/env python3
"""
dc22 Fibonacci Screenshot Explorer

Take screenshots at Fibonacci intervals to understand the game flow.
Fibonacci: 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 130 (one full cycle before game-over)

Actions: try arrow keys first, then clicks. Save each frame as PNG.
"""

import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

from arc_agi import Arcade
from arcengine import GameAction, GameState

OUTPUT_DIR = "/ganuda/services/arc_agi_3/dc22_screenshots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

FIBONACCI = [1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 130]

# ARC color palette (standard)
ARC_COLORS = {
    0: (0, 0, 0),        # black
    1: (0, 116, 217),    # blue
    2: (255, 65, 54),    # red
    3: (46, 204, 64),    # green
    4: (255, 220, 0),    # yellow
    5: (170, 170, 170),  # gray
    6: (240, 18, 190),   # magenta
    7: (255, 133, 27),   # orange
    8: (127, 219, 255),  # light blue
    9: (135, 12, 37),    # dark red
    10: (255, 255, 255), # white
    11: (0, 0, 0),       # black (for negative/transparent)
    12: (128, 0, 128),   # purple
    13: (0, 128, 128),   # teal
}


def frame_to_png(frame_data, path, scale=8):
    """Convert frame grid to PNG image."""
    from PIL import Image

    if isinstance(frame_data, list):
        grid = np.array(frame_data[-1] if isinstance(frame_data[0], list) and isinstance(frame_data[0][0], list) else frame_data)
    else:
        grid = np.array(frame_data)

    if grid.ndim == 3:
        grid = grid[-1]  # Take last layer

    h, w = grid.shape
    img = Image.new("RGB", (w * scale, h * scale))
    pixels = img.load()

    for y in range(h):
        for x in range(w):
            val = int(grid[y, x])
            color = ARC_COLORS.get(val, ARC_COLORS.get(val % 14, (128, 128, 128)))
            for dy in range(scale):
                for dx in range(scale):
                    pixels[x * scale + dx, y * scale + dy] = color

    img.save(path)
    return img


def main():
    arcade = Arcade()
    env = arcade.make("dc22")

    print(f"dc22 loaded. Taking Fibonacci screenshots...")

    # Reset to start
    frame = env.step(GameAction.RESET)
    frame_to_png(frame.frame, f"{OUTPUT_DIR}/dc22_000_reset.png")
    print(f"  action 0: RESET → saved (state={frame.state})")

    # Available actions for cycling
    actions = [
        GameAction.ACTION1,  # up
        GameAction.ACTION2,  # down
        GameAction.ACTION3,  # left
        GameAction.ACTION4,  # right
        GameAction.ACTION5,  # wait/pass
    ]

    action_idx = 0
    fib_set = set(FIBONACCI)
    game_over_count = 0

    for step in range(1, 140):  # Slightly past one full cycle
        # Cycle through actions
        action = actions[action_idx % len(actions)]
        action_idx += 1

        frame = env.step(action)

        if frame.state == GameState.GAME_OVER:
            frame_to_png(frame.frame, f"{OUTPUT_DIR}/dc22_{step:03d}_GAMEOVER_{game_over_count}.png")
            print(f"  action {step}: {action.name} → GAME_OVER #{game_over_count} — saved")
            game_over_count += 1
            # Reset
            frame = env.step(GameAction.RESET)
            frame_to_png(frame.frame, f"{OUTPUT_DIR}/dc22_{step:03d}_reset_after_go.png")
            action_idx = 0  # restart action cycle
            continue

        if frame.state == GameState.WIN:
            frame_to_png(frame.frame, f"{OUTPUT_DIR}/dc22_{step:03d}_WIN.png")
            print(f"  action {step}: {action.name} → WIN!")
            break

        if step in fib_set:
            frame_to_png(frame.frame, f"{OUTPUT_DIR}/dc22_{step:03d}_fib_{action.name}.png")
            print(f"  action {step}: {action.name} → Fibonacci checkpoint saved (state={frame.state}, score={frame.levels_completed})")
        elif step % 20 == 0:
            frame_to_png(frame.frame, f"{OUTPUT_DIR}/dc22_{step:03d}_{action.name}.png")
            print(f"  action {step}: {action.name} → periodic save")

    print(f"\nDone. {game_over_count} game-overs. Screenshots in {OUTPUT_DIR}/")
    print(f"Files: {sorted(os.listdir(OUTPUT_DIR))}")


if __name__ == "__main__":
    main()

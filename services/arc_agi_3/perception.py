"""
ARC-AGI-3 Perception Layer — Canvas Pixel Reading

Extracts structured game state from the HTML canvas via Playwright JavaScript injection.
No vision model needed — pure pixel color classification at grid resolution.

The "cheat code" discovered during the Apr 12 2026 dry run:
the game renders on a 1024x1024 canvas with a 32x32 tile grid.
Each tile's center pixel color uniquely identifies its type.
"""

# Color classification thresholds (discovered empirically Apr 12 2026)
TILE_TYPES = {
    'wall': lambda r, g, b: 40 < r < 75 and r == g == b,
    'floor': lambda r, g, b: 75 < r < 120 and r == g == b,
    'border': lambda r, g, b: r < 40 and g < 40 and b < 40,
    'player': lambda r, g, b: r > 170 and 90 < g < 130 and b < 60,  # orange
    'player_body': lambda r, g, b: r < 60 and g > 100 and b > 170,  # blue
    'plus': lambda r, g, b: r > 170 and g > 170 and b > 170,  # white
    'fuel': lambda r, g, b: r > 170 and g > 150 and b < 50,  # yellow
    'lgray': lambda r, g, b: 130 < r < 200 and r == g == b,
}

# JavaScript to inject into Playwright page for reading game state
READ_GAME_STATE_JS = '''() => {
    const canvas = document.getElementById("boardCanvas");
    if (!canvas) return {error: "no boardCanvas"};
    const ctx = canvas.getContext("2d");
    const ts = 32;
    const W = Math.floor(canvas.width / ts);
    const H = Math.floor(canvas.height / ts);

    const grid = [];
    let player = null;
    let playerBody = [];
    const blocks = [];
    const plusPositions = [];
    const fuelPickups = [];
    let fuelBar = 0;

    for (let y = 0; y < H; y++) {
        const row = [];
        for (let x = 0; x < W; x++) {
            const p = ctx.getImageData(x * ts + ts / 2, y * ts + ts / 2, 1, 1).data;
            const r = p[0], g = p[1], b = p[2];

            let type = 'wall';
            if (75 < r && r < 120 && r === g && g === b) type = 'floor';
            else if (r < 40 && g < 40 && b < 40) type = 'border';
            else if (r > 170 && g > 90 && g < 130 && b < 60) {
                type = 'player';
                if (!player) player = {x, y};
            }
            else if (r < 60 && g > 100 && b > 170) {
                type = 'blue';
                // Distinguish player body from game blocks by position
                if (player && Math.abs(x - player.x) <= 2 && y > player.y && y <= player.y + 3) {
                    type = 'player_body';
                } else if (y < 25) {  // Game area only (exclude d-pad)
                    blocks.push({x, y});
                }
                playerBody.push({x, y});
            }
            else if (r > 170 && g > 170 && b > 170) {
                type = 'plus';
                plusPositions.push({x, y});
            }
            else if (r > 170 && g > 150 && b < 50) {
                type = 'fuel';
                if (y >= 28) {  // Fuel bar at bottom
                    fuelBar++;
                } else if (y < 26) {  // Fuel pickup on game board
                    fuelPickups.push({x, y});
                }
            }
            else if (130 < r && r < 200 && r === g && g === b) type = 'lgray';

            row.push(type);
        }
        grid.push(row);
    }

    // Filter blocks to only game-area blue tiles (not player body, not d-pad)
    const gameBlocks = blocks.filter(b => b.y < 25 && b.x > 3 && b.x < 28);

    // Build walkability map: 1 = walkable, 0 = wall/border
    const walkable = [];
    for (let y = 0; y < H; y++) {
        const row = [];
        for (let x = 0; x < W; x++) {
            const t = grid[y][x];
            row.push(t === 'floor' || t === 'player' || t === 'player_body' || t === 'blue' || t === 'plus' || t === 'fuel' || t === 'lgray' ? 1 : 0);
        }
        walkable.push(row);
    }

    return {
        player: player,
        gameBlocks: gameBlocks,
        plusPositions: plusPositions,
        fuelPickups: fuelPickups,
        fuelBar: fuelBar,
        gridWidth: W,
        gridHeight: H,
        walkable: walkable
    };
}'''

# JavaScript to read player position only (lightweight, for move-by-move tracking)
READ_PLAYER_POS_JS = '''() => {
    const canvas = document.getElementById("boardCanvas");
    if (!canvas) return null;
    const ctx = canvas.getContext("2d");
    const ts = 32;
    for (let y = 0; y < 25; y++) {
        for (let x = 4; x < 28; x++) {
            const p = ctx.getImageData(x * ts + ts / 2, y * ts + ts / 2, 1, 1).data;
            if (p[0] > 170 && p[1] > 90 && p[1] < 130 && p[2] < 60) return {x, y};
        }
    }
    return null;
}'''

# JavaScript to read fuel bar count
READ_FUEL_JS = '''() => {
    const canvas = document.getElementById("boardCanvas");
    if (!canvas) return 0;
    const ctx = canvas.getContext("2d");
    let count = 0;
    for (let x = 0; x < 1024; x += 8) {
        const p = ctx.getImageData(x, 976, 1, 1).data;
        if (p[0] > 150 && p[1] > 150 && p[2] < 50) count++;
    }
    return count;
}'''

# ASCII grid renderer for Council deliberation input
def render_ascii_grid(game_state, grid_data=None):
    """Render a human/Council-readable ASCII representation of the game state."""
    if not game_state or 'error' in game_state:
        return "ERROR: Could not read game state"

    lines = []
    lines.append(f"Player: ({game_state['player']['x']}, {game_state['player']['y']})")
    lines.append(f"Fuel: {game_state['fuelBar']}")
    lines.append(f"Blocks: {len(game_state['gameBlocks'])}")
    lines.append(f"Plus (+): {game_state['plusPositions']}")
    lines.append(f"Fuel pickups: {game_state['fuelPickups']}")

    return '\n'.join(lines)

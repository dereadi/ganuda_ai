"""
ARC-AGI-3 Game Session Manager — Playwright Browser Control

Manages the browser session, game initialization, move execution,
and level tracking for ARC-AGI-3 tasks on arcprize.org.
"""

from playwright.sync_api import sync_playwright, Page


class ArcGame:
    """Manages a Playwright session playing an ARC-AGI-3 task."""

    def __init__(self, task_id: str = "ls20", headless: bool = True):
        self.task_id = task_id
        self.headless = headless
        self.url = f"https://arcprize.org/tasks/{task_id}"
        self.playwright = None
        self.browser = None
        self.page = None
        self.move_count = 0
        self.level_history = []

    def start(self) -> 'ArcGame':
        """Launch browser and start the game."""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        self.page = self.browser.new_page(viewport={'width': 1280, 'height': 900})
        self.page.goto(self.url)
        self.page.wait_for_load_state('networkidle')
        self.page.wait_for_timeout(5000)

        # Click START button
        start_btn = self.page.query_selector('button.handheld-start-button')
        if start_btn:
            start_btn.click()
            self.page.wait_for_timeout(3000)

        return self

    def move(self, direction: str) -> dict:
        """Execute a move and return the new position.

        Args:
            direction: one of 'up', 'down', 'left', 'right'

        Returns:
            dict with {x, y} of new player position, or None if position couldn't be read
        """
        key_map = {
            'up': 'ArrowUp',
            'down': 'ArrowDown',
            'left': 'ArrowLeft',
            'right': 'ArrowRight',
        }
        key = key_map.get(direction.lower())
        if not key:
            raise ValueError(f"Invalid direction: {direction}. Use up/down/left/right.")

        self.page.keyboard.press(key)
        self.page.wait_for_timeout(300)
        self.move_count += 1

        return self.get_player_pos()

    def get_player_pos(self) -> dict:
        """Read current player position from canvas."""
        from perception import READ_PLAYER_POS_JS
        return self.page.evaluate(READ_PLAYER_POS_JS)

    def get_fuel(self) -> int:
        """Read current fuel level."""
        from perception import READ_FUEL_JS
        return self.page.evaluate(READ_FUEL_JS)

    def get_game_state(self) -> dict:
        """Read full game state from canvas."""
        from perception import READ_GAME_STATE_JS
        return self.page.evaluate(READ_GAME_STATE_JS)

    def get_level(self) -> str:
        """Read current level from DOM."""
        return self.page.evaluate(
            '() => document.querySelector(".shell-level-badge")?.textContent?.trim() || "unknown"'
        )

    def screenshot(self, path: str):
        """Save a screenshot of the current game state."""
        self.page.screenshot(path=path)

    def close(self):
        """Clean up browser resources."""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def __enter__(self):
        return self.start()

    def __exit__(self, *args):
        self.close()

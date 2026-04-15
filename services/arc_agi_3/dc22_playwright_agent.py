#!/usr/bin/env python3
"""
dc22 Visual Agent — Playwright + VLM

Plays dc22 in the browser using Playwright for visual capture and interaction,
Qwen2-VL-7B on bluefin for frame analysis.

The agent:
1. Opens dc22 at arcprize.org
2. Screenshots the game canvas
3. Sends to VLM → describes what it sees
4. Clicks hat buttons, observes changes
5. Plans navigation based on visual understanding
6. Uses arrow keys to reach the goal

No FARA, no AppleScript, no screen capture permissions.
Playwright IS the eyes AND the hands.
"""

import asyncio
import base64
import json
import os
import requests
import time
from playwright.async_api import async_playwright

VLM_URL = "http://10.100.0.2:8090/v1/chat/completions"
VLM_MODEL = "Qwen/Qwen2-VL-7B-Instruct-AWQ"
SCREENSHOT_DIR = "/ganuda/services/arc_agi_3/dc22_playwright_screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


def ask_vlm(image_bytes: bytes, prompt: str, max_tokens: int = 300) -> str:
    """Send an image to the VLM and get a text response."""
    img_b64 = base64.b64encode(image_bytes).decode()
    try:
        resp = requests.post(VLM_URL, json={
            'model': VLM_MODEL,
            'messages': [{
                'role': 'user',
                'content': [
                    {'type': 'image_url', 'image_url': {'url': f'data:image/png;base64,{img_b64}'}},
                    {'type': 'text', 'text': prompt},
                ]
            }],
            'max_tokens': max_tokens,
            'temperature': 0.3,
        }, timeout=30)
        return resp.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"VLM error: {e}"


def ask_vlm_two_frames(before: bytes, after: bytes, prompt: str) -> str:
    """Send two frames to VLM for comparison."""
    b64_before = base64.b64encode(before).decode()
    b64_after = base64.b64encode(after).decode()
    try:
        resp = requests.post(VLM_URL, json={
            'model': VLM_MODEL,
            'messages': [{
                'role': 'user',
                'content': [
                    {'type': 'image_url', 'image_url': {'url': f'data:image/png;base64,{b64_before}'}},
                    {'type': 'image_url', 'image_url': {'url': f'data:image/png;base64,{b64_after}'}},
                    {'type': 'text', 'text': prompt},
                ]
            }],
            'max_tokens': 300,
            'temperature': 0.3,
        }, timeout=30)
        return resp.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"VLM error: {e}"


async def capture_game_canvas(page) -> bytes:
    """Capture just the game canvas element."""
    # Try to find the game canvas
    canvas = await page.query_selector('canvas')
    if canvas:
        return await canvas.screenshot()
    # Fallback: capture the game container
    game = await page.query_selector('.game-container, .game-wrapper, #game, main')
    if game:
        return await game.screenshot()
    # Last resort: full page
    return await page.screenshot()


async def run_agent():
    print("=== dc22 Playwright Visual Agent ===\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width': 1024, 'height': 768})

        # Navigate to dc22
        print("[1] Opening dc22...")
        await page.goto('https://arcprize.org/tasks/dc22', wait_until='networkidle', timeout=30000)
        await asyncio.sleep(3)

        # Capture start screen
        frame_start = await page.screenshot()
        with open(f'{SCREENSHOT_DIR}/00_start_screen.png', 'wb') as f:
            f.write(frame_start)
        print("[2] Start screen captured")

        # Click START button
        print("[3] Clicking START...")
        try:
            start_btn = await page.query_selector('text=START')
            if start_btn:
                await start_btn.click()
            else:
                # Click center of the Game Boy screen
                await page.mouse.click(512, 400)
        except Exception as e:
            print(f"    Click failed: {e}, trying keyboard...")
            await page.keyboard.press('Enter')
        await asyncio.sleep(3)

        # Press Enter or Space to start playing
        await page.keyboard.press('Enter')
        await asyncio.sleep(2)

        # Capture game screen
        frame0 = await page.screenshot()
        with open(f'{SCREENSHOT_DIR}/01_game_loaded.png', 'wb') as f:
            f.write(frame0)
        print(f"[4] Game screen captured ({len(frame0)} bytes)")

        # Ask VLM what it sees
        print("[5] Asking VLM to describe the game...")
        description = ask_vlm(frame0,
            "This is a puzzle game called dc22 on arcprize.org. It shows a Game Boy style interface. "
            "Describe exactly what you see inside the game screen. "
            "Look for: colored blocks, buttons, a player piece, a goal, and any obstacles.",
            max_tokens=400)
        print(f"    VLM says: {description[:500]}\n")

        # Focus the game area
        print("[6] Finding clickable game elements...")
        await page.mouse.click(512, 350)
        await asyncio.sleep(1)

        # Capture after focus
        frame1 = await page.screenshot()
        with open(f'{SCREENSHOT_DIR}/01_focused.png', 'wb') as f:
            f.write(frame1)

        # Experiment: click the right side where hat buttons should be
        # From the visual: right side of game area, roughly upper and lower thirds
        button_positions = [
            (680, 250, "upper-right hat button"),
            (680, 400, "lower-right hat button"),
            (600, 250, "mid-right area"),
            (600, 400, "mid-right lower"),
        ]

        for i, (x, y, label) in enumerate(button_positions):
            print(f"\n[5.{i}] Clicking {label} at ({x}, {y})...")
            before = await page.screenshot()

            await page.mouse.click(x, y)
            await asyncio.sleep(1)

            after = await page.screenshot()
            with open(f'{SCREENSHOT_DIR}/click_{i:02d}_{label.replace(" ", "_")}.png', 'wb') as f:
                f.write(after)

            # Ask VLM what changed
            diff_desc = ask_vlm_two_frames(before, after,
                "These are two screenshots of a puzzle game — BEFORE and AFTER clicking a button. "
                "What changed between the two images? Be specific about any visual differences: "
                "new objects, moved objects, color changes, bridges appearing/disappearing.")
            print(f"    VLM diff: {diff_desc[:400]}")

        # Try arrow keys
        print("\n[6] Testing arrow keys...")
        for key, direction in [('ArrowRight', 'RIGHT'), ('ArrowRight', 'RIGHT'),
                                ('ArrowUp', 'UP'), ('ArrowUp', 'UP')]:
            before = await page.screenshot()
            await page.keyboard.press(key)
            await asyncio.sleep(0.5)
            after = await page.screenshot()

            diff_desc = ask_vlm_two_frames(before, after,
                f"I pressed {direction}. What moved? Did the player piece change position?")
            print(f"    {direction}: {diff_desc[:200]}")

        # Final screenshot
        final = await page.screenshot()
        with open(f'{SCREENSHOT_DIR}/99_final.png', 'wb') as f:
            f.write(final)

        # Ask VLM for a strategy
        print("\n[7] Asking VLM for a strategy...")
        strategy = ask_vlm(final,
            "You are playing a puzzle game. The player (checkered cube) needs to reach "
            "the goal (another cube). There are colored hat-shaped buttons on the right "
            "that flip bridges or spawn teleporters. What sequence of button clicks and "
            "arrow key presses would solve this level? Think step by step.")
        print(f"    Strategy: {strategy[:600]}")

        await browser.close()

    print("\n=== Agent complete. Screenshots in dc22_playwright_screenshots/ ===")


if __name__ == "__main__":
    asyncio.run(run_agent())

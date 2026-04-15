#!/usr/bin/env python3
"""
dc22 Autonomous Player — Playwright + VLM

Plays dc22 Level 1 using visual understanding.
The VLM sees each frame, decides what to do, and the agent executes.
"""

import asyncio
import base64
import json
import os
import requests
import time
from playwright.async_api import async_playwright

# Try local GPU VLM first, fallback to bluefin
VLM_ENDPOINTS = [
    "http://localhost:9101/v1/chat/completions",
    "http://10.100.0.2:8090/v1/chat/completions",
]
VLM_MODEL_LOCAL = "Qwen/Qwen2-VL-7B-Instruct-AWQ"
SCREENSHOT_DIR = "/ganuda/services/arc_agi_3/dc22_play_screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


def ask_vlm(image_bytes: bytes, prompt: str, max_tokens: int = 150) -> str:
    img_b64 = base64.b64encode(image_bytes).decode()
    for endpoint in VLM_ENDPOINTS:
        try:
            resp = requests.post(endpoint, json={
                'model': VLM_MODEL_LOCAL,
                'messages': [{
                    'role': 'user',
                    'content': [
                        {'type': 'image_url', 'image_url': {'url': f'data:image/png;base64,{img_b64}'}},
                        {'type': 'text', 'text': prompt},
                    ]
                }],
                'max_tokens': max_tokens,
                'temperature': 0.1,
            }, timeout=30)
            return resp.json()['choices'][0]['message']['content']
        except Exception:
            continue
    return "VLM_UNAVAILABLE"


async def run():
    print("=== dc22 Autonomous Player ===\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--enable-gpu', '--use-gl=angle']
        )
        page = await browser.new_page(viewport={'width': 1024, 'height': 900})

        # Load game
        print("[LOAD] Opening dc22...")
        await page.goto('https://arcprize.org/tasks/dc22', wait_until='networkidle', timeout=30000)
        await asyncio.sleep(2)

        # Click the START button (pixel-font handheld-start-button at 508, 465)
        print("[LOAD] Clicking START button...")
        try:
            await page.click('.handheld-start-button', timeout=5000)
        except Exception:
            await page.mouse.click(508, 465)
        await asyncio.sleep(3)

        frame = await page.screenshot()
        with open(f'{SCREENSHOT_DIR}/start.png', 'wb') as f:
            f.write(frame)

        # Game playing loop
        step = 0
        max_steps = 40
        prev_frame = frame
        last_actions = []  # track recent actions for stuck detection

        while step < max_steps:
            step += 1

            # Stuck detection: if same action 4+ times, force alternatives
            stuck_override = None
            if len(last_actions) >= 3 and len(set(last_actions[-3:])) == 1:
                stuck_action = last_actions[-1]
                # Cycle through ALL alternatives including buttons
                alternatives = ["CLICK_TOP_BUTTON", "CLICK_BOTTOM_BUTTON", "RIGHT", "LEFT", "DOWN", "UP"]
                alternatives = [a for a in alternatives if a != stuck_action]
                stuck_override = alternatives[(step // 3) % len(alternatives)]
                print(f"  [STUCK] Same action {stuck_action} 3x — forcing {stuck_override}")

            # Ask VLM: what should I do next?
            action_prompt = (
                "You are playing a puzzle game. The checkered cube is the player. "
                "You need to reach the other small cube (the goal). "
                "The right side has hat-shaped colored buttons that change the left side "
                "(flip bridges, spawn teleporters). Green arrow buttons are at the bottom.\n\n"
                "Look at this screenshot and tell me the SINGLE NEXT ACTION to take. "
                "Reply with EXACTLY ONE of these words:\n"
                "UP, DOWN, LEFT, RIGHT (to move the player)\n"
                "CLICK_TOP_BUTTON (to click the upper hat button on the right)\n"
                "CLICK_BOTTOM_BUTTON (to click the lower hat button on the right)\n"
                "DONE (if the player has reached the goal)\n\n"
                "Just the one word. Nothing else."
            )

            if stuck_override:
                action = stuck_override
            else:
                action = ask_vlm(frame, action_prompt, max_tokens=20).strip().upper()
            print(f"  step {step}: {'[OVERRIDE] ' if stuck_override else ''}VLM says → {action}")
            last_actions.append(action.split()[0] if action else "UNKNOWN")

            if action == "VLM_UNAVAILABLE":
                print("  VLM down, skipping...")
                continue

            if "DONE" in action:
                print(f"\n[WIN?] VLM thinks we're done at step {step}!")
                final = await page.screenshot()
                with open(f'{SCREENSHOT_DIR}/done_{step}.png', 'wb') as f:
                    f.write(final)
                break

            # Execute the action by clicking DOM d-pad buttons
            # D-pad positions (from DOM inspection):
            #   UP: (371, 689), LEFT: (335, 725), RIGHT: (407, 725), DOWN: (371, 761)
            # Canvas at (293, 210), 429x429
            # Hat buttons on canvas: upper-right ~(580, 320), lower-right ~(580, 430)
            if "UP" in action and "BUTTON" not in action:
                await page.mouse.click(371, 689)
            elif "DOWN" in action and "BUTTON" not in action:
                await page.mouse.click(371, 761)
            elif "LEFT" in action and "BUTTON" not in action:
                await page.mouse.click(335, 725)
            elif "RIGHT" in action and "BUTTON" not in action:
                await page.mouse.click(407, 725)
            elif "TOP" in action and "BUTTON" in action:
                # Click upper hat button on the game canvas (right side of game)
                await page.mouse.click(580, 320)
            elif "BOTTOM" in action and "BUTTON" in action:
                # Click lower hat button on the game canvas (right side of game)
                await page.mouse.click(580, 430)
            else:
                for d, coords in [("UP", (371, 689)), ("DOWN", (371, 761)),
                                   ("LEFT", (335, 725)), ("RIGHT", (407, 725))]:
                    if d in action:
                        await page.mouse.click(*coords)
                        break

            await asyncio.sleep(0.5)

            # Capture new frame
            frame = await page.screenshot()

            # Save every 5 steps
            if step % 5 == 0:
                with open(f'{SCREENSHOT_DIR}/step_{step:03d}.png', 'wb') as f:
                    f.write(frame)

            prev_frame = frame

        # Final screenshot
        final = await page.screenshot()
        with open(f'{SCREENSHOT_DIR}/final_{step}.png', 'wb') as f:
            f.write(final)

        # Ask VLM for final assessment
        assessment = ask_vlm(final,
            "Did the player (checkered cube) reach the goal? "
            "Is the level complete? Answer YES or NO and explain briefly.",
            max_tokens=100)
        print(f"\n[FINAL] VLM assessment: {assessment}")

        await browser.close()

    print(f"\n=== Completed {step} steps. Screenshots in {SCREENSHOT_DIR}/ ===")


if __name__ == "__main__":
    asyncio.run(run())

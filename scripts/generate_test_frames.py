#!/usr/bin/env python3
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

FRAME_DIR = Path("/ganuda/data/vision/frames/test")
FRAME_DIR.mkdir(parents=True, exist_ok=True)

def create_image(name: str, label: str, color: tuple) -> None:
    """
    Create an image with a specified background color and text label.

    :param name: The filename of the image to be created.
    :param label: The text label to be drawn on the image.
    :param color: The RGB color tuple for the background of the image.
    """
    img = Image.new('RGB', (640, 480), color)
    draw = ImageDraw.Draw(img)
    draw.text((200, 220), label, fill='white')
    img.save(FRAME_DIR / name)
    print(f"Created: {name}")

create_image("sample.jpg", "TEST IMAGE", (100, 100, 100))
create_image("empty_scene.jpg", "EMPTY SCENE", (90, 90, 90))
create_image("person.jpg", "PERSON DETECTED", (80, 100, 80))
create_image("anomaly.jpg", "ANOMALY TEST", (120, 80, 80))
create_image("vehicle.jpg", "VEHICLE", (100, 110, 100))

print(f"Created 5 test images in {FRAME_DIR}")
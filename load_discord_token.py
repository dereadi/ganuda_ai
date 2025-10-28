#!/usr/bin/env python3
"""
Cherokee Constitutional AI - Discord Token Loader
Loads Discord bot token from discord.key file
"""

import os


def load_discord_token(key_file_path='discord.key'):
    """
    Load Discord bot token from file

    Args:
        key_file_path: Path to discord.key file (default: discord.key in current dir)

    Returns:
        str: Discord bot token

    Raises:
        FileNotFoundError: If discord.key doesn't exist
        ValueError: If discord.key is empty or invalid
    """
    # Resolve absolute path
    if not os.path.isabs(key_file_path):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        key_file_path = os.path.join(script_dir, key_file_path)

    # Check if file exists
    if not os.path.exists(key_file_path):
        raise FileNotFoundError(
            f"❌ Discord key file not found: {key_file_path}\n"
            f"   Please create it with: vi {key_file_path}"
        )

    # Read token
    with open(key_file_path, 'r') as f:
        token = f.read().strip()

    # Validate token
    if not token:
        raise ValueError(
            f"❌ Discord key file is empty: {key_file_path}\n"
            f"   Please add your Discord bot token to this file"
        )

    # Check if it looks like a Discord token (basic validation)
    if len(token) < 50:
        raise ValueError(
            f"⚠️  Discord token looks too short ({len(token)} chars)\n"
            f"   Expected format: MTAx...(~72 chars)\n"
            f"   Please verify the token in {key_file_path}"
        )

    return token


if __name__ == '__main__':
    """Test loading the token"""
    try:
        token = load_discord_token()
        print(f"✅ Discord token loaded successfully")
        print(f"   Length: {len(token)} characters")
        print(f"   Preview: {token[:20]}...{token[-10:]}")
    except Exception as e:
        print(str(e))
        exit(1)

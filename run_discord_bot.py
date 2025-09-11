#!/usr/bin/env python3
"""
Discord Bot Runner with embedded API keys
"""

import os
import sys

# Set environment variables BEFORE importing anything
os.environ['DISCORD_TOKEN'] = "MTQwNjcwNDE4ODY3MDQ3NjMyOQ.GdGCva.PMvVe_aNTTgJ1U8Zh1W6_oSIckyEwdR-6WHk9A"
os.environ['ANTHROPIC_API_KEY'] = "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"
os.environ['OPENAI_API_KEY'] = "sk-proj-yzn7JGhnKmofTNMlLwidMIGoh_hTfAsPS_qWweyvKLmlzMi1GGWUZJQbx9lRfZuC2F_AW4gIACT3BlbkFJ9xOHiRASDcW3gkv0qdOteX1pyVHcrwqV-a-7mLOt"

# Add script directory to Python path
sys.path.insert(0, '/home/dereadi/scripts/claude')

# Import and run the bot
try:
    import discord_llm_council
    discord_llm_council.main()
except Exception as e:
    print(f"Error running bot: {e}")
    import traceback
    traceback.print_exc()
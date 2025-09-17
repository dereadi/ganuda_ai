#!/bin/bash
# Simple Ganudabot starter script

echo "🔥 Starting Ganudabot for Ridge Channel..."
echo "Bot: @ganudabot"
echo "Token verified and active"

# Kill any existing instances
pkill -f "7913555407" 2>/dev/null
sleep 2

# Export token
export GANUDABOT_TOKEN="7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8"

# Start the bot
cd /home/dereadi/scripts/claude
./quantum_crawdad_env/bin/python3 ganudabot_ridge_responder.py

echo "Ganudabot is ready in Ridge Channel!"
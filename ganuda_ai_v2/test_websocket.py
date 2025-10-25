#!/usr/bin/env python3
"""Test WebSocket connection to Guardian API"""
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8765/ws"
    print(f"🔥 Connecting to {uri}...")

    async with websockets.connect(uri) as websocket:
        print("✅ WebSocket connected!\n")

        # Receive 3 messages (connection + 2 thermal updates over 60 seconds)
        for i in range(3):
            message = await asyncio.wait_for(websocket.recv(), timeout=35)
            data = json.loads(message)
            print(f"📨 Message {i+1}:")
            print(f"   Type: {data['type']}")
            if 'payload' in data:
                print(f"   Count: {data['payload'].get('count', 'N/A')}")
                print(f"   Timestamp: {data['payload'].get('timestamp', 'N/A')}")
            print()

        print("🦅 WebSocket test complete - Mitakuye Oyasin!")

if __name__ == "__main__":
    asyncio.run(test_websocket())

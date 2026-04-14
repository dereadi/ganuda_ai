import asyncio
import websockets
import json
from typing import Any, Dict, List, Optional

class DeerSignalPipeline:
    def __init__(self, uri: str):
        self.uri = uri
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None

    async def connect(self) -> None:
        """Connect to the WebSocket server."""
        self.websocket = await websockets.connect(self.uri)

    async def send_signal(self, signal: Dict[str, Any]) -> None:
        """Send a signal to the WebSocket server."""
        if self.websocket:
            await self.websocket.send(json.dumps(signal))
        else:
            raise ConnectionError("WebSocket is not connected.")

    async def receive_signal(self) -> Dict[str, Any]:
        """Receive a signal from the WebSocket server."""
        if self.websocket:
            response = await self.websocket.recv()
            return json.loads(response)
        else:
            raise ConnectionError("WebSocket is not connected.")

    async def close(self) -> None:
        """Close the WebSocket connection."""
        if self.websocket:
            await self.websocket.close()

    async def run(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run the pipeline by sending and receiving signals."""
        responses = []
        for signal in signals:
            await self.send_signal(signal)
            response = await self.receive_signal()
            responses.append(response)
        return responses

async def main():
    uri = "ws://localhost:8765"
    pipeline = DeerSignalPipeline(uri)
    
    try:
        await pipeline.connect()
        signals = [
            {"type": "deer_signal", "data": {"url": "https://example.com"}},
            {"type": "deer_signal", "data": {"url": "https://another-example.com"}}
        ]
        responses = await pipeline.run(signals)
        print(responses)
    finally:
        await pipeline.close()

if __name__ == "__main__":
    asyncio.run(main())
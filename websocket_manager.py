#!/usr/bin/env python3
"""
WebSocket Manager - Real-time data feeds
Council requirement for low latency
"""

import websocket
import json
import threading

class WebSocketManager:
    def __init__(self, symbols=['BTC-USD', 'ETH-USD', 'SOL-USD']):
        self.symbols = symbols
        self.prices = {}
        self.ws = None
        
    def on_message(self, ws, message):
        data = json.loads(message)
        if 'price' in data and 'product_id' in data:
            self.prices[data['product_id']] = float(data['price'])
            
    def on_error(self, ws, error):
        print(f"WebSocket error: {error}")
        
    def connect(self):
        # Connect to Coinbase WebSocket
        self.ws = websocket.WebSocketApp(
            "wss://ws-feed.exchange.coinbase.com",
            on_message=self.on_message,
            on_error=self.on_error
        )
        
        # Subscribe to price feeds
        def on_open(ws):
            ws.send(json.dumps({
                "type": "subscribe",
                "product_ids": self.symbols,
                "channels": ["ticker"]
            }))
            
        self.ws.on_open = on_open
        
        # Run in thread
        wst = threading.Thread(target=self.ws.run_forever)
        wst.daemon = True
        wst.start()

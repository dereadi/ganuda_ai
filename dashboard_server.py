#!/usr/bin/env python3
'''
🌐 TRADING DASHBOARD SERVER
Serves the visual monitoring interface
'''

import http.server
import socketserver
import json
import subprocess
from datetime import datetime

PORT = 8080

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            # Get real-time status
            status = self.get_system_status()
            self.wfile.write(json.dumps(status).encode())
            
        elif self.path == '/':
            self.path = '/trading_dashboard.html'
            return http.server.SimpleHTTPRequestHandler.do_GET(self)
        else:
            return http.server.SimpleHTTPRequestHandler.do_GET(self)
            
    def get_system_status(self):
        '''Get real-time trading system status'''
        try:
            # Count active bots
            result = subprocess.run(
                "ps aux | grep -E 'greek|crawdad|trader' | grep python | wc -l",
                shell=True,
                capture_output=True,
                text=True
            )
            active_bots = int(result.stdout.strip()) if result.stdout else 0
            
            return {
                'timestamp': datetime.now().isoformat(),
                'active_bots': active_bots,
                'portfolio': 43.53,  # Would fetch real value
                'alerts': ['BTC Cycle Bottom'],
                'greeks': {
                    'delta': 'active',
                    'gamma': 'active',
                    'theta': 'active',
                    'vega': 'active',
                    'rho': 'fixing'
                }
            }
        except:
            return {'error': 'Could not fetch status'}

print(f'🌐 Dashboard server starting on http://localhost:{PORT}')
print('   Open browser to view dashboard')
print('   Press Ctrl+C to stop')

with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
    httpd.serve_forever()

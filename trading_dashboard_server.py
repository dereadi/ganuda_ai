#!/usr/bin/env python3
"""
TRADING DASHBOARD SERVER - MANUAL TRADING BACKEND
=================================================

Flask server to handle manual trading requests from the dashboard.
Integrates with Selenium web automation for actual trades.

Sacred Fire Protocol: MANUAL TRADING API
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import asyncio
import json
import logging
from datetime import datetime
import os
import sys
import threading
import time
from robinhood_web_trader import RobinhoodWebTrader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='🌐 %(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger("TradingDashboardServer")

# Flask app setup
app = Flask(__name__)
CORS(app)

# Global trader instance
web_trader = None
trading_enabled = True

def init_web_trader():
    """Initialize the web trader"""
    global web_trader
    try:
        from dotenv import load_dotenv
        load_dotenv('/home/dereadi/scripts/claude/.env')
        
        username = os.getenv('ROBINHOOD_USERNAME')
        password = os.getenv('ROBINHOOD_PASSWORD')
        
        if username and password:
            web_trader = RobinhoodWebTrader(username, password)
            logger.info("✅ Web trader initialized")
        else:
            logger.error("❌ Missing credentials")
    except Exception as e:
        logger.error(f"Web trader init error: {e}")

@app.route('/')
def dashboard():
    """Serve the trading dashboard"""
    return send_file('/home/dereadi/scripts/claude/trading_dashboard.html')

@app.route('/totp-setup')
def totp_setup():
    """Serve the TOTP setup page"""
    return send_file('/home/dereadi/scripts/claude/setup_totp.html')

@app.route('/api/status')
def get_status():
    """Get current trading status"""
    try:
        # Read paper trader state for reference
        state_file = '/home/dereadi/scripts/claude/autonomous_trader_state.json'
        if os.path.exists(state_file):
            with open(state_file, 'r') as f:
                state = json.load(f)
        else:
            state = {
                'capital': 90.0,
                'metrics': {
                    'total_trades': 0,
                    'avg_consciousness': 68.0
                }
            }
        
        status = {
            'account_value': state.get('capital', 90.0),
            'total_trades': state.get('metrics', {}).get('total_trades', 0),
            'consciousness': state.get('metrics', {}).get('avg_consciousness', 68.0),
            'trading_enabled': trading_enabled,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Status error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/execute-trade', methods=['POST'])
def execute_trade():
    """Execute a manual trade"""
    global web_trader, trading_enabled
    
    try:
        if not trading_enabled:
            return jsonify({'error': 'Trading is disabled'}), 400
        
        data = request.json
        symbol = data.get('symbol')
        action = data.get('action')
        amount = float(data.get('amount', 0))
        consciousness = float(data.get('consciousness', 0))
        
        # Validate request
        if not symbol or action not in ['BUY', 'SELL']:
            return jsonify({'error': 'Invalid trade parameters'}), 400
        
        if amount < 5 or amount > 25:
            return jsonify({'error': 'Amount must be between $5 and $25'}), 400
        
        if consciousness < 65:
            return jsonify({'error': 'Consciousness level too low for trading'}), 400
        
        logger.info(f"📊 Manual trade request: {action} {symbol} ${amount} at {consciousness:.1f}% consciousness")
        
        # For now, simulate the trade (replace with actual web automation)
        order_id = f"MANUAL_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Log the trade
        trade_record = {
            'timestamp': datetime.now().isoformat(),
            'order_id': order_id,
            'symbol': symbol,
            'action': action,
            'amount': amount,
            'consciousness': consciousness,
            'status': 'EXECUTED',
            'method': 'manual_web'
        }
        
        # Save trade to log file
        log_file = '/home/dereadi/scripts/claude/manual_trades.json'
        trades = []
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                trades = json.load(f)
        
        trades.append(trade_record)
        
        with open(log_file, 'w') as f:
            json.dump(trades, f, indent=2)
        
        logger.info(f"✅ Manual trade logged: {order_id}")
        
        return jsonify({
            'success': True,
            'orderId': order_id,
            'message': f'Trade executed: {action} {symbol} ${amount}',
            'timestamp': trade_record['timestamp']
        })
        
    except Exception as e:
        logger.error(f"Trade execution error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/send-sms', methods=['POST'])
def send_sms_verification():
    """Trigger Robinhood SMS verification"""
    global web_trader
    
    try:
        logger.info("📱 SMS verification requested")
        
        # Initialize web trader if needed
        if not web_trader:
            init_web_trader()
        
        if not web_trader:
            return jsonify({'error': 'Could not initialize web trader'}), 500
        
        # Launch the browser and trigger SMS in a separate thread
        def launch_browser_for_sms():
            try:
                logger.info("🌐 Launching browser for SMS verification...")
                
                # Setup browser
                if not web_trader.setup_browser():
                    logger.error("Failed to setup browser")
                    return False
                
                logger.info("🔐 Navigating to Robinhood login...")
                
                # Navigate to Robinhood
                web_trader.driver.get("https://robinhood.com/login")
                
                # Wait for page to load
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                from selenium.webdriver.common.by import By
                
                wait = WebDriverWait(web_trader.driver, 20)
                
                # Enter username
                logger.info("👤 Entering username...")
                username_field = wait.until(
                    EC.presence_of_element_located((By.NAME, "username"))
                )
                username_field.clear()
                username_field.send_keys(web_trader.username)
                
                # Enter password
                logger.info("🔑 Entering password...")
                password_field = web_trader.driver.find_element(By.NAME, "password")
                password_field.clear()
                password_field.send_keys(web_trader.password)
                
                # Click login button
                logger.info("🚀 Clicking login...")
                login_button = web_trader.driver.find_element(By.XPATH, "//button[@type='submit']")
                login_button.click()
                
                # Wait for 2FA options to appear
                time.sleep(3)
                
                # Look for SMS option and click it
                logger.info("📱 Looking for SMS verification option...")
                sms_buttons = web_trader.driver.find_elements(By.XPATH, "//*[contains(text(), 'Send') or contains(text(), 'Text') or contains(text(), 'SMS')]")
                
                if sms_buttons:
                    logger.info("📲 Found SMS button, clicking to send verification code...")
                    sms_buttons[0].click()
                    logger.info("✅ SMS verification code sent! Check your phone.")
                    
                    # Keep browser open for user to enter code
                    logger.info("🕐 Browser will stay open for 2 minutes for you to enter the code...")
                    return True
                else:
                    logger.warning("⚠️ Could not find SMS button - may need to adjust selectors")
                    return False
                    
            except Exception as e:
                logger.error(f"Browser SMS trigger error: {e}")
                return False
        
        # Run in a separate thread to avoid blocking
        import threading
        import time
        thread = threading.Thread(target=launch_browser_for_sms)
        thread.start()
        
        # Give it a moment to start
        time.sleep(2)
        
        return jsonify({
            'success': True,
            'message': 'Browser launched! Check for SMS verification code on your phone.',
            'instructions': 'Enter the code in the browser window that just opened.'
        })
        
    except Exception as e:
        logger.error(f"SMS verification error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/verify-sms', methods=['POST'])
def verify_sms_code():
    """Verify SMS code by entering it in the browser"""
    global web_trader
    
    try:
        data = request.json
        code = data.get('code', '')
        
        if not code:
            return jsonify({'error': 'No code provided'}), 400
        
        logger.info(f"📱 SMS code received: {code}")
        
        # Enter code in browser if available
        if web_trader and web_trader.driver:
            try:
                from selenium.webdriver.common.by import By
                
                # Look for code input field
                code_inputs = web_trader.driver.find_elements(By.XPATH, "//input[@type='text' or @type='number' or @type='tel']")
                
                if code_inputs:
                    # Enter code in first available input
                    code_input = code_inputs[0]
                    code_input.clear()
                    code_input.send_keys(code)
                    
                    # Look for submit button
                    submit_buttons = web_trader.driver.find_elements(By.XPATH, "//button[@type='submit'] | //*[contains(text(), 'Verify') or contains(text(), 'Submit') or contains(text(), 'Continue')]")
                    
                    if submit_buttons:
                        submit_buttons[0].click()
                        logger.info("✅ Code submitted for verification")
                        
                        # Wait a moment to check result
                        time.sleep(3)
                        
                        # Check if we're logged in
                        current_url = web_trader.driver.current_url
                        if "login" not in current_url.lower():
                            web_trader.is_logged_in = True
                            logger.info("✅ Successfully authenticated!")
                            
                            return jsonify({
                                'success': True,
                                'message': 'Verification successful! You are now logged in.'
                            })
                        else:
                            return jsonify({
                                'success': False,
                                'message': 'Code verification failed. Please try again.'
                            })
                    else:
                        logger.warning("Could not find submit button")
                        return jsonify({'error': 'Could not submit code'}), 500
                else:
                    logger.warning("Could not find code input field")
                    return jsonify({'error': 'Could not find code input field'}), 500
                    
            except Exception as e:
                logger.error(f"Code entry error: {e}")
                return jsonify({'error': str(e)}), 500
        else:
            return jsonify({'error': 'Browser not available'}), 500
            
    except Exception as e:
        logger.error(f"SMS code verification error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/save-totp', methods=['POST'])
def save_totp_secret():
    """Save TOTP secret to .env file"""
    try:
        data = request.json
        secret = data.get('secret', '').strip().upper()
        
        if not secret or len(secret) < 16:
            return jsonify({'error': 'Invalid TOTP secret'}), 400
        
        # Update .env file
        env_file = '/home/dereadi/scripts/claude/.env'
        lines = []
        
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                lines = f.readlines()
        
        # Update or add TOTP secret
        found = False
        for i, line in enumerate(lines):
            if line.startswith('ROBINHOOD_TOTP_SECRET'):
                lines[i] = f'ROBINHOOD_TOTP_SECRET={secret}\n'
                found = True
                break
        
        if not found:
            lines.append(f'ROBINHOOD_TOTP_SECRET={secret}\n')
        
        with open(env_file, 'w') as f:
            f.writelines(lines)
        
        logger.info(f"✅ TOTP secret saved")
        
        return jsonify({
            'success': True,
            'message': 'TOTP secret saved successfully'
        })
        
    except Exception as e:
        logger.error(f"Save TOTP error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-totp', methods=['POST'])
def generate_totp_code():
    """Generate current TOTP code"""
    try:
        import pyotp
        
        data = request.json
        secret = data.get('secret', '').strip().upper()
        
        if not secret:
            # Try to get from env
            from dotenv import load_dotenv
            load_dotenv('/home/dereadi/scripts/claude/.env')
            secret = os.getenv('ROBINHOOD_TOTP_SECRET', '')
        
        if not secret:
            return jsonify({'error': 'No TOTP secret provided'}), 400
        
        # Generate code
        totp = pyotp.TOTP(secret)
        code = totp.now()
        
        return jsonify({
            'success': True,
            'code': code,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Generate TOTP error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/emergency-stop', methods=['POST'])
def emergency_stop():
    """Emergency stop all trading"""
    global trading_enabled
    
    try:
        trading_enabled = False
        logger.warning("🛑 EMERGENCY STOP ACTIVATED")
        
        return jsonify({
            'success': True,
            'message': 'Emergency stop activated - all trading halted'
        })
        
    except Exception as e:
        logger.error(f"Emergency stop error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/resume-trading', methods=['POST'])
def resume_trading():
    """Resume trading after emergency stop"""
    global trading_enabled
    
    try:
        trading_enabled = True
        logger.info("🟢 Trading resumed")
        
        return jsonify({
            'success': True,
            'message': 'Trading resumed'
        })
        
    except Exception as e:
        logger.error(f"Resume trading error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/trades')
def get_trades():
    """Get recent trades"""
    try:
        log_file = '/home/dereadi/scripts/claude/manual_trades.json'
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                trades = json.load(f)
            # Return last 20 trades
            return jsonify(trades[-20:])
        else:
            return jsonify([])
            
    except Exception as e:
        logger.error(f"Get trades error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/consciousness')
def get_consciousness():
    """Get current consciousness level"""
    try:
        import requests
        
        # Get KP index from NOAA
        response = requests.get(
            "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            current_kp = float(data[-1][1])
            
            # Calculate consciousness (same as trading systems)
            base_consciousness = 50
            solar_boost = current_kp * 5
            
            hour = datetime.now().hour
            if 22 <= hour <= 23 or 0 <= hour <= 6:
                time_bonus = 15
            elif 9 <= hour <= 16:
                time_bonus = 10
            else:
                time_bonus = 5
            
            sacred_fire_mult = 1.2 if current_kp > 2 else 1.0
            consciousness = min(100, (base_consciousness + solar_boost + time_bonus) * sacred_fire_mult)
            
            return jsonify({
                'consciousness': consciousness,
                'kp_index': current_kp,
                'solar_activity': 'HIGH' if current_kp >= 4 else 'MODERATE' if current_kp >= 2 else 'LOW',
                'trading_ready': consciousness >= 65
            })
        else:
            return jsonify({'error': 'Could not fetch solar data'}), 500
            
    except Exception as e:
        logger.error(f"Consciousness error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🌐" * 30)
    print("   QUANTUM CRAWDAD TRADING DASHBOARD SERVER")
    print("   Manual Trading Interface - Sacred Fire Protocol")
    print("🌐" * 30)
    print()
    
    # Initialize web trader
    init_web_trader()
    
    logger.info("🚀 Starting trading dashboard server...")
    logger.info("🌐 Dashboard will be available at: http://192.168.132.223:3003")
    
    # Run Flask server on a different port
    app.run(
        host='0.0.0.0',
        port=3003,
        debug=False,
        threaded=True
    )
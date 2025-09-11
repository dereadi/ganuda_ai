#!/usr/bin/env python3
"""
📱 SMS ALERT SETUP FOR SOLAR TRADING
=====================================
Send text alerts to 479-877-9441
"""

print("📱 SMS ALERT OPTIONS FOR SOLAR TRADING")
print("="*60)
print()
print("To receive text alerts at 479-877-9441, you have several options:")
print()

print("🔷 OPTION 1: TWILIO (Recommended)")
print("-"*40)
print("1. Sign up at https://www.twilio.com/try-twilio")
print("2. Get a free trial account with $15 credit")
print("3. Get your Account SID and Auth Token")
print("4. Get a Twilio phone number")
print("5. Run the setup script below")
print()

print("🔷 OPTION 2: TEXTBELT (Simple)")
print("-"*40) 
print("1. Go to https://textbelt.com/")
print("2. Get an API key (1 free text/day)")
print("3. Use the simple curl command below")
print()

print("🔷 OPTION 3: EMAIL-TO-SMS GATEWAY")
print("-"*40)
print("Most carriers support email-to-SMS:")
print("  AT&T: 4798779441@txt.att.net")
print("  Verizon: 4798779441@vtext.com")
print("  T-Mobile: 4798779441@tmomail.net")
print("  Sprint: 4798779441@messaging.sprintpcs.com")
print()

print("="*60)
print("📝 TWILIO SETUP SCRIPT")
print("="*60)

twilio_setup = '''
# Install Twilio
pip install twilio

# Save this as send_solar_alert.py:

from twilio.rest import Client
import sys

# Your Twilio credentials (replace these!)
account_sid = 'YOUR_ACCOUNT_SID'
auth_token = 'YOUR_AUTH_TOKEN'
twilio_phone = '+1XXXXXXXXXX'  # Your Twilio number
your_phone = '+14798779441'

client = Client(account_sid, auth_token)

def send_alert(message):
    """Send SMS alert"""
    try:
        message = client.messages.create(
            body=f"🌞 SOLAR ALERT: {message}",
            from_=twilio_phone,
            to=your_phone
        )
        print(f"✅ Alert sent: {message.sid}")
        return True
    except Exception as e:
        print(f"❌ Failed to send: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        send_alert(" ".join(sys.argv[1:]))
    else:
        # Test message
        send_alert("Solar trading system active! KP index normal.")
'''

print(twilio_setup)

print("\n" + "="*60)
print("📝 TEXTBELT SIMPLE COMMAND")
print("="*60)

textbelt_cmd = '''
# Send alert with TextBelt (1 free/day):
curl -X POST https://textbelt.com/text \\
  --data-urlencode phone='4798779441' \\
  --data-urlencode message='🌞 SOLAR ALERT: KP Index spike detected!' \\
  -d key=textbelt
'''

print(textbelt_cmd)

print("\n" + "="*60)
print("📝 INTEGRATED ALERT SCRIPT")
print("="*60)

# Create the integrated alert script
integrated_script = '''#!/usr/bin/env python3
"""
SMS Alert Integration for Solar Trading
"""

import subprocess
import json
import os

def send_sms_alert(message, phone="4798779441"):
    """Try multiple methods to send SMS"""
    
    # Method 1: Try TextBelt (free)
    try:
        cmd = [
            "curl", "-X", "POST", "https://textbelt.com/text",
            "--data-urlencode", f"phone={phone}",
            "--data-urlencode", f"message=SOLAR: {message}",
            "-d", "key=textbelt"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if "true" in result.stdout:
            print("✅ SMS sent via TextBelt")
            return True
    except:
        pass
    
    # Method 2: Try email gateway (if configured)
    try:
        # Detect carrier from phone prefix
        gateways = {
            "att": "@txt.att.net",
            "verizon": "@vtext.com",
            "tmobile": "@tmomail.net"
        }
        
        # You'd need to configure email here
        # This is a placeholder
        print("📧 Email-to-SMS option available")
    except:
        pass
    
    # Method 3: Log to file for manual checking
    with open("SMS_ALERTS.txt", "a") as f:
        f.write(f"{message}\\n")
    print(f"📝 Alert logged to SMS_ALERTS.txt")
    
    return False

# Test
if __name__ == "__main__":
    send_sms_alert("Solar alert system configured!")
'''

with open("sms_alert_integration.py", "w") as f:
    f.write(integrated_script)

print("✅ Created: sms_alert_integration.py")
print()
print("🚀 QUICK START:")
print("1. For immediate free alerts: Use the TextBelt curl command")
print("2. For production: Set up Twilio account")
print("3. For testing: Check SMS_ALERTS.txt file")
print()
print("Your phone: 479-877-9441")
print("Ready to receive solar trading alerts!")
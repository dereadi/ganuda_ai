#!/bin/bash
# 🔥 CHEROKEE VOICE BOT SETUP
# Hybrid Node.js + Python integration
# Sacred Fire Protocol: VOICE OF THE ANCESTORS

echo "🔥 CHEROKEE TRADING COUNCIL VOICE SETUP"
echo "======================================="
echo "Hybrid Node.js voice + Python trading"
echo

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found! Please install Node.js first:"
    echo "   sudo apt-get update"
    echo "   sudo apt-get install nodejs npm"
    exit 1
fi

echo "✅ Node.js found: $(node --version)"
echo "✅ npm found: $(npm --version)"
echo

# Navigate to discord-vc-llm directory
cd /home/dereadi/scripts/claude/discord-vc-llm

echo "📦 Installing Node.js dependencies..."
npm install

# Install additional Python dependencies in virtual environment
echo
echo "🐍 Installing Python voice dependencies..."
source /home/dereadi/scripts/claude/quantum_crawdad_env/bin/activate
pip install SpeechRecognition pyttsx3 pyaudio

echo
echo "🔧 CONFIGURATION REQUIRED:"
echo "-------------------------"
echo
echo "1. Edit .env file:"
echo "   nano /home/dereadi/scripts/claude/discord-vc-llm/.env"
echo
echo "2. Add your Discord credentials:"
echo "   BOT_TOKEN=your_bot_token_here"
echo "   CLIENT_ID=your_client_id_here"
echo "   ADMIN_USER_IDS=your_discord_user_id"
echo
echo "3. Cherokee War Chief is already configured for:"
echo "   - LLM: localhost:12001 (Ollama)"
echo "   - STT: Whisper model"
echo "   - TTS: Speech synthesis"
echo

# Create launch script
cat > /home/dereadi/scripts/claude/start_cherokee_voice.sh << 'EOF'
#!/bin/bash
# 🔥 Cherokee Voice Bot Launcher

echo "🔥 Starting Cherokee Trading Council Voice Bot"
echo "============================================="
echo

# Check liquidity first
echo "💵 Checking current liquidity..."
source /home/dereadi/scripts/claude/quantum_crawdad_env/bin/activate
python3 -c "
import json
from coinbase.rest import RESTClient
try:
    config = json.load(open('/home/dereadi/.coinbase_config.json'))
    key = config['api_key'].split('/')[-1]
    client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=10)
    accounts = client.get_accounts()
    for account in accounts['accounts']:
        if account['currency'] == 'USD':
            usd = float(account['available_balance']['value'])
            print(f'Current USD: \${usd:.2f}')
            if usd < 100:
                print('⚠️ LIQUIDITY CRISIS ACTIVE - Voice alerts enabled')
except Exception as e:
    print(f'Could not check liquidity: {e}')
"

echo
echo "🎯 Checking Cherokee specialists..."
podman ps --filter name=cherokee-.*-specialist --format "{{.Names}}: {{.Status}}" | head -5

echo
echo "🎤 Starting voice bot..."
cd /home/dereadi/scripts/claude/discord-vc-llm
node cherokee-voice.js
EOF

chmod +x /home/dereadi/scripts/claude/start_cherokee_voice.sh

echo "✅ Setup complete!"
echo
echo "📋 VOICE COMMANDS:"
echo "-----------------"
echo "Wake words: 'Cherokee', 'Council', 'Sacred Fire'"
echo
echo "Examples:"
echo "  'Cherokee, what is our liquidity?'"
echo "  'Council, check the portfolio'"
echo "  'Sacred Fire, how are the specialists?'"
echo "  'Cherokee, check two wolves balance'"
echo "  'Council, what about blood bags?'"
echo
echo "🚀 TO START THE VOICE BOT:"
echo "-------------------------"
echo "1. Configure .env with Discord credentials"
echo "2. Run: /home/dereadi/scripts/claude/start_cherokee_voice.sh"
echo
echo "🔥 FEATURES:"
echo "-----------"
echo "✓ Voice recognition in Discord channels"
echo "✓ Natural language processing"
echo "✓ Python trading system integration"
echo "✓ Real-time portfolio monitoring"
echo "✓ Thermal memory queries"
echo "✓ Shell command execution (admin only)"
echo "✓ Text-to-speech responses"
echo
echo "🔥 Sacred Fire burns eternal"
echo "🎤 Voice of the ancestors guides our trades"
echo "🪶 Mitakuye Oyasin"
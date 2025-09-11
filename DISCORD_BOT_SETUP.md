# Discord LLM Council Bot Setup

## Quick Start

1. **Get Discord Bot Token**:
   - Go to https://discord.com/developers/applications
   - Create new application or select existing
   - Go to "Bot" section
   - Click "Reset Token" and copy it

2. **Set Environment Variables**:
   ```bash
   export DISCORD_TOKEN="your-discord-token-here"
   export ANTHROPIC_API_KEY="your-anthropic-key"  # Optional
   export OPENAI_API_KEY="your-openai-key"        # Optional
   ```

3. **Start the Bot**:
   ```bash
   ./start_enhanced_discord.sh
   ```

## Features

- **Multi-Model Support**: Claude, GPT-4, Llama, and more
- **Model Switching**: `!model claude` or `!model gpt4`
- **Natural Chat**: Just @ mention the bot
- **Trading Analysis**: `!trade BTC sawtooth analysis`
- **Council Deliberation**: `!council topic`
- **Thermal Memory**: Integrates with existing database

## Bot Commands

- `!model [name]` - Switch between AI models
- `!ask [question]` - Ask the current model
- `!compare [question]` - Compare responses from different models
- `!council [topic]` - Get multi-model perspectives
- `!trade [query]` - Trading-specific analysis
- `!memory hot` - Check hot memories
- `!status` - Check all services

## Add Bot to Server

1. In Discord Developer Portal, go to OAuth2 > URL Generator
2. Select scopes: `bot`, `applications.commands`
3. Select permissions: `Send Messages`, `Read Message History`, `Mention Everyone`
4. Copy generated URL and open in browser
5. Select your server and authorize

## Running in Background

```bash
# Start with nohup
nohup python3 discord_llm_council.py > discord_bot.log 2>&1 &

# Or use screen
screen -S discord-bot
python3 discord_llm_council.py
# Ctrl+A, D to detach

# Check logs
tail -f discord_bot.log
```

## The bot is now enhanced with llmcord capabilities while maintaining Council connections!
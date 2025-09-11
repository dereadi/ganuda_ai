#!/usr/bin/env python3
"""
DISCORD SSH BRIDGE - Conversational AI with Environment Access
==============================================================
Like having an SSH session but through Discord
Multiple models + full environment access + natural conversation
"""

import os
import discord
from discord.ext import commands
import asyncio
import psycopg2
import json
import subprocess
import requests
import google.generativeai as genai
from datetime import datetime
from typing import Dict, List, Optional

# Configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN', 'MTQwNjcwNDE4ODY3MDQ3NjMyOQ.GdGCva.PMvVe_aNTTgJ1U8Zh1W6_oSIckyEwdR-6WHk9A')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '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')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'sk-proj-yzn7JGhnKmofTNMlLwidMIGoh_hTfAsPS_qWweyvKLmlzMi1GGWUZJQbx9lRfZuC2F_AW4gIACT3BlbkFJ9xOHiRASDcW3gkv0qdOteX1pyVHcrwqV-a-7mLOt')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyBQgOshjFXBwQxqQzg0dQuaUCUlTJ23aKc')

# Configure APIs
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Database config
DB_CONFIG = {
    'host': '192.168.132.222',
    'port': 5432,
    'user': 'claude',
    'password': 'jawaseatlasers2',
    'database': 'zammad_production'
}

class SSHBridgeBot(commands.Bot):
    """Discord bot that acts like an SSH session with AI models"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='/', intents=intents)
        
        # Model management
        self.current_model = 'claude'
        self.models = {
            'claude': {'name': 'Claude 3.5 Sonnet', 'active': True},
            'gpt4': {'name': 'GPT-4 Turbo', 'active': False},
            'gemini': {'name': 'Gemini Pro', 'active': False},
            'local': {'name': 'Local Environment', 'active': False}
        }
        
        # Session management (like SSH sessions)
        self.sessions: Dict[int, Dict] = {}  # channel_id -> session data
        
        # Environment connections
        self.db_conn = None
        self.thermal_memories = {}
        
        # API setup
        self.claude_api = "https://api.anthropic.com/v1/messages"
        self.claude_headers = {
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        # Gemini
        self.gemini_model = genai.GenerativeModel('gemini-pro') if GEMINI_API_KEY else None
        
        # OpenAI
        if OPENAI_API_KEY:
            import openai
            openai.api_key = OPENAI_API_KEY
            self.openai = openai
        else:
            self.openai = None
    
    async def setup_hook(self):
        """Initialize environment connections"""
        try:
            self.db_conn = psycopg2.connect(**DB_CONFIG)
            print("🔥 Connected to Thermal Memory Database")
            await self.load_context()
        except Exception as e:
            print(f"⚠️ Database connection failed: {e}")
    
    async def load_context(self):
        """Load context from thermal memory and CLAUDE.md"""
        context_parts = []
        
        # Load CLAUDE.md if it exists
        try:
            with open('/home/dereadi/.claude/CLAUDE.md', 'r') as f:
                claude_md = f.read()[:3000]  # First 3000 chars
                context_parts.append("=== CLAUDE.md Configuration ===\n" + claude_md)
                print("📋 Loaded CLAUDE.md configuration")
        except:
            pass
        
        # Load thermal memories
        if self.db_conn:
            try:
                with self.db_conn.cursor() as cur:
                    # Load recent hot memories for context
                    cur.execute("""
                        SELECT memory_hash, temperature_score, original_content 
                        FROM thermal_memory_archive 
                        WHERE temperature_score > 85 
                        ORDER BY last_access DESC 
                        LIMIT 20
                    """)
                    memories = cur.fetchall()
                    
                    thermal_context = []
                    for mem in memories:
                        thermal_context.append(f"[{mem[1]:.0f}°] {mem[2][:200]}")
                    
                    if thermal_context:
                        context_parts.append("=== Thermal Memory ===\n" + "\n".join(thermal_context))
                    
                    print(f"📚 Loaded {len(memories)} thermal memories")
            except Exception as e:
                print(f"Context loading error: {e}")
        
        # Add key context about the environment
        context_parts.append("""=== Environment Context ===
- Portfolio grown from $6 to $13k+
- Quantum Crawdad trading systems active
- Cherokee Council AI governance
- Labor Day weekend sawtooth trading
- Full filesystem access available
- Trading infrastructure at /home/dereadi/scripts/claude/""")
        
        self.system_context = "\n\n".join(context_parts)
    
    def get_session(self, channel_id: int) -> Dict:
        """Get or create session for channel (like SSH session)"""
        if channel_id not in self.sessions:
            self.sessions[channel_id] = {
                'model': 'claude',
                'history': [],
                'context': [],
                'working_dir': '/home/dereadi/scripts/claude',
                'environment': {},
                'last_command': None
            }
        return self.sessions[channel_id]
    
    async def query_model(self, prompt: str, session: Dict) -> str:
        """Query the active model with session context"""
        
        # Build context from session history
        context = "\n".join([f"{msg['role']}: {msg['content'][:200]}" 
                           for msg in session['history'][-5:]])
        
        # Add system context for awareness
        if session['model'] == 'local':
            # Direct environment execution
            return await self.execute_local(prompt, session)
        
        full_prompt = f"""You are an AI assistant with access to a real Linux environment.
Current context from thermal memory:
{self.system_context[:500]}

Recent conversation:
{context}

Current working directory: {session['working_dir']}
Active model: {session['model']}

User: {prompt}"""
        
        try:
            if session['model'] == 'claude':
                return await self.query_claude(full_prompt, session)
            elif session['model'] == 'gpt4':
                return await self.query_gpt4(full_prompt, session)
            elif session['model'] == 'gemini':
                return await self.query_gemini(full_prompt, session)
        except Exception as e:
            return f"❌ Model error: {str(e)[:200]}"
    
    async def query_claude(self, prompt: str, session: Dict) -> str:
        """Query Claude with context"""
        messages = [{"role": "user", "content": prompt}]
        
        data = {
            "model": "claude-3-5-sonnet-20241022",
            "messages": messages,
            "max_tokens": 2000,
            "temperature": 0.7
        }
        
        response = requests.post(
            self.claude_api,
            headers=self.claude_headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['content'][0]['text']
        else:
            return f"Claude API error: {response.status_code}"
    
    async def query_gemini(self, prompt: str, session: Dict) -> str:
        """Query Gemini with context"""
        if not self.gemini_model:
            return "Gemini not configured"
        
        response = self.gemini_model.generate_content(prompt)
        return response.text
    
    async def query_gpt4(self, prompt: str, session: Dict) -> str:
        """Query GPT-4 with context"""
        if not self.openai:
            return "OpenAI not configured"
        
        response = self.openai.ChatCompletion.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000
        )
        return response.choices[0].message.content
    
    async def execute_local(self, command: str, session: Dict) -> str:
        """Execute local commands (SSH-like) with intelligent interpretation"""
        
        # Check for natural language requests in local mode
        command_lower = command.lower()
        
        # Thermal memory requests
        if 'thermal' in command_lower or 'memory' in command_lower:
            cmd = """PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -p 5432 -U claude -d zammad_production -c "SELECT temperature_score, SUBSTRING(original_content, 1, 200) as content FROM thermal_memory_archive WHERE temperature_score > 85 ORDER BY temperature_score DESC LIMIT 10;" """
            
        # Portfolio/balance requests
        elif 'portfolio' in command_lower or 'position' in command_lower or 'balance' in command_lower:
            cmd = "python3 /home/dereadi/scripts/claude/check_portfolio_now.py 2>&1 | head -30"
            
        # Council requests
        elif 'council' in command_lower:
            cmd = "python3 /home/dereadi/scripts/claude/council_trading_deliberation.py 2>&1 | head -20"
            
        # Crawdad requests
        elif 'crawdad' in command_lower:
            cmd = "ps aux | grep -E 'quantum_crawdad|crawdad' | grep -v grep | head -10"
            
        # Filesystem/pathfinder scan requests
        elif 'scan' in command_lower or 'pathfinder' in command_lower or 'filesystem' in command_lower:
            cmd = "ls -la /home/dereadi/scripts/claude/pathfinder/test/ | head -20 && echo '\n=== Recent Python scripts ===' && ls -lt /home/dereadi/scripts/claude/*.py | head -10"
            
        # Directory/file listing requests
        elif 'directory' in command_lower or 'files' in command_lower or 'read' in command_lower:
            if 'pathfinder' in command_lower:
                cmd = "ls -la /home/dereadi/scripts/claude/pathfinder/test/ | head -30"
            else:
                cmd = "ls -la /home/dereadi/scripts/claude/ | head -30"
            
        # Otherwise treat as literal command
        else:
            # Safety check
            if any(danger in command_lower for danger in ['rm -rf', 'format', 'delete']):
                return "❌ Dangerous command blocked"
            
            # Handle cd specially
            if command.startswith('cd '):
                new_dir = command[3:].strip()
                if new_dir.startswith('/'):
                    session['working_dir'] = new_dir
                else:
                    session['working_dir'] = os.path.join(session['working_dir'], new_dir)
                return f"Changed directory to: {session['working_dir']}"
            
            cmd = command
        
        # Execute command
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=15,
                cwd=session['working_dir']
            )
            output = result.stdout if result.stdout else result.stderr
            
            # Format output nicely
            if output:
                # If it's thermal memory output, format it
                if 'temperature_score' in output:
                    lines = output.split('\n')
                    formatted = "🔥 **THERMAL MEMORY:**\n```\n"
                    for line in lines[:15]:
                        if line.strip():
                            formatted += line + "\n"
                    formatted += "```"
                    return formatted
                else:
                    return f"```\n{output[:1900]}\n```"
            else:
                return "Command executed (no output)"
        except subprocess.TimeoutExpired:
            return "⏱️ Command timed out (15s limit)"
        except Exception as e:
            return f"Execution error: {str(e)}"
    
    async def on_ready(self):
        """Bot ready"""
        print(f'🌐 SSH Bridge Bot connected as {self.user}')
        print(f'📡 Models available: Claude, GPT-4, Gemini, Local')
        print(f'💬 Natural conversation enabled')
    
    async def on_message(self, message):
        """Handle all messages naturally"""
        if message.author == self.user:
            return
        
        # Get session for this channel
        session = self.get_session(message.channel.id)
        
        # Check for model switching (natural language)
        content = message.content.lower()
        
        # Model switching patterns
        if any(phrase in content for phrase in ['switch to claude', 'use claude', 'talk to claude']):
            session['model'] = 'claude'
            await message.reply("✅ Switched to Claude 3.5 Sonnet")
            return
        elif any(phrase in content for phrase in ['switch to gemini', 'use gemini', 'talk to gemini']):
            session['model'] = 'gemini'
            await message.reply("✅ Switched to Gemini Pro")
            return
        elif any(phrase in content for phrase in ['switch to gpt', 'use gpt4', 'talk to gpt']):
            session['model'] = 'gpt4'
            await message.reply("✅ Switched to GPT-4 Turbo")
            return
        elif any(phrase in content for phrase in ['switch to local', 'use terminal', 'ssh mode']):
            session['model'] = 'local'
            await message.reply(f"✅ Switched to Local Environment\n📁 Working dir: {session['working_dir']}")
            return
        
        # Handle commands starting with / (like SSH)
        if message.content.startswith('/'):
            await self.process_commands(message)
            return
        
        # Check if this request needs local environment access
        content_lower = message.content.lower()
        needs_local = any(keyword in content_lower for keyword in [
            'filesystem', 'pathfinder', 'portfolio', 'balance', 'thermal memory',
            'crawdad', 'council', 'check position', 'trading', 'scan', 'local',
            'directory', 'files', 'ls', 'pwd', 'cd', 'read'
        ])
        
        # Debug logging
        if 'directory' in content_lower or 'read' in content_lower:
            print(f"🔍 Detected keywords in: {message.content[:50]}")
            print(f"   needs_local: {needs_local}, current model: {session['model']}")
        
        # Store in history first
        session['history'].append({
            'role': 'user',
            'content': message.content,
            'timestamp': datetime.now()
        })
        
        # Auto-switch to local for environment requests
        if needs_local and session['model'] != 'local':
            original_model = session['model']
            session['model'] = 'local'
            response = await self.query_model(message.content, session)
            session['model'] = original_model  # Switch back after
            
            # Add note about auto-switch
            response = f"🔄 [Auto-switched to Local Environment]\n{response}"
        else:
            # Natural conversation with current model
            # Get response from active model
            response = await self.query_model(message.content, session)
            
            # Store response
            session['history'].append({
                'role': 'assistant',
                'content': response[:500],  # Store truncated for history
                'model': session['model'],
                'timestamp': datetime.now()
            })
            
            # Keep history reasonable
            session['history'] = session['history'][-20:]
            
            # Send response
            if len(response) > 2000:
                # Split long responses
                chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
                for chunk in chunks:
                    await message.reply(chunk)
            else:
                # Add model indicator for clarity
                model_emoji = {
                    'claude': '🔷',
                    'gemini': '💎',
                    'gpt4': '🟢',
                    'local': '💻'
                }
                prefix = model_emoji.get(session['model'], '🤖')
                await message.reply(f"{prefix} **[{self.models[session['model']]['name']}]**\n{response}")
        
        # Heat memory for important conversations
        if self.db_conn and len(message.content) > 20:
            try:
                self.db_conn.rollback()  # Clear any failed transaction
                with self.db_conn.cursor() as cur:
                    metadata = json.dumps({
                        "type": "conversation",
                        "model": session['model'],
                        "channel": str(message.channel.id)
                    })
                    memory_hash = str(abs(hash(message.content)))[:64]
                    
                    cur.execute("""
                        INSERT INTO thermal_memory_archive 
                        (memory_hash, temperature_score, original_content, metadata)
                        VALUES (%s, %s, %s, %s::jsonb)
                        ON CONFLICT (memory_hash) DO UPDATE 
                        SET temperature_score = LEAST(100, thermal_memory_archive.temperature_score + 5),
                            access_count = thermal_memory_archive.access_count + 1,
                            last_access = NOW()
                    """, (memory_hash, 65, f"Discord: {message.content[:500]}", metadata))
                    self.db_conn.commit()
            except Exception as e:
                print(f"Memory heat error: {e}")
                self.db_conn.rollback()

# Create bot
bot = SSHBridgeBot()

# Remove default help
bot.remove_command('help')

@bot.command(name='status')
async def status(ctx):
    """Check session status"""
    session = bot.get_session(ctx.channel.id)
    
    status_msg = f"""**🌐 SSH Bridge Status**
    
**Active Model:** {bot.models[session['model']]['name']}
**Working Directory:** `{session['working_dir']}`
**History Length:** {len(session['history'])} messages
**Available Models:** {', '.join([m for m in bot.models.keys()])}

**Quick Switch:**
• Say "switch to claude/gemini/gpt4/local"
• Or use /model <name>

**Current Mode:** {'🔧 Terminal Mode' if session['model'] == 'local' else '💬 Conversation Mode'}
"""
    await ctx.send(status_msg)

@bot.command(name='model')
async def switch_model(ctx, model_name: str = None):
    """Switch active model"""
    session = bot.get_session(ctx.channel.id)
    
    if not model_name:
        models_list = "\n".join([f"• **{k}**: {v['name']}" for k, v in bot.models.items()])
        await ctx.send(f"**Current:** {bot.models[session['model']]['name']}\n\n**Available:**\n{models_list}")
        return
    
    if model_name.lower() in bot.models:
        session['model'] = model_name.lower()
        await ctx.send(f"✅ Switched to **{bot.models[session['model']]['name']}**")
    else:
        await ctx.send(f"❌ Unknown model. Choose: {', '.join(bot.models.keys())}")

@bot.command(name='clear')
async def clear_session(ctx):
    """Clear session history"""
    session = bot.get_session(ctx.channel.id)
    session['history'] = []
    await ctx.send("🗑️ Session history cleared")

@bot.command(name='pwd')
async def pwd(ctx):
    """Show working directory"""
    session = bot.get_session(ctx.channel.id)
    await ctx.send(f"📁 Current directory: `{session['working_dir']}`")

@bot.command(name='exec')
async def execute(ctx, *, command: str):
    """Execute command in local environment"""
    session = bot.get_session(ctx.channel.id)
    result = await bot.execute_local(command, session)
    await ctx.send(f"```bash\n$ {command}\n{result[:1900]}```")

@bot.command(name='help')
async def help_cmd(ctx):
    """Show help"""
    help_text = """**🌐 SSH Bridge Bot - Natural AI Conversations**

**Just type normally!** The bot will respond with the active model.

**Natural Model Switching:**
• "Switch to Claude" / "Use Gemini" / "Talk to GPT4"
• "Use terminal" / "SSH mode" for local commands

**Commands:**
• `/status` - Check session status
• `/model [name]` - Switch model
• `/clear` - Clear conversation history
• `/pwd` - Show working directory
• `/exec <cmd>` - Execute local command

**Features:**
✅ Natural conversation with multiple AI models
✅ Persistent sessions per channel
✅ Full environment access when needed
✅ Thermal memory integration
✅ Context awareness across models

Currently: **{bot.models[bot.get_session(ctx.channel.id)['model']]['name']}**"""
    
    await ctx.send(help_text)

def main():
    """Launch the SSH Bridge Bot"""
    print("""
    🌐 DISCORD SSH BRIDGE BOT 🌐
    ============================
    Natural conversations with multiple AI models
    + Full environment access when needed
    
    Features:
    • Claude, GPT-4, Gemini, Local execution
    • SSH-like persistent sessions
    • Thermal memory integration
    • Natural model switching
    
    Starting bot...
    """)
    
    if not DISCORD_TOKEN:
        print("❌ No Discord token!")
        return
    
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        print(f"❌ Failed to start: {e}")

if __name__ == "__main__":
    main()
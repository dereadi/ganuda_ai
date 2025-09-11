#!/usr/bin/env python3
"""
DISCORD STATEFUL SHELL BRIDGE
==============================
Maintains persistent shell sessions per Discord channel
Like SSH but through Discord!
"""

import os
import discord
from discord.ext import commands
import asyncio
import subprocess
import psycopg2
import json
import tempfile
import shlex
from datetime import datetime
from pathlib import Path

# Configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN', 'MTQwNjcwNDE4ODY3MDQ3NjMyOQ.GdGCva.PMvVe_aNTTgJ1U8Zh1W6_oSIckyEwdR-6WHk9A')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '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')

# Database config
DB_CONFIG = {
    'host': '192.168.132.222',
    'port': 5432,
    'user': 'claude',
    'password': 'jawaseatlasers2',
    'database': 'zammad_production'
}

class ShellSession:
    """Persistent shell session for a Discord channel"""
    
    def __init__(self, channel_id):
        self.channel_id = channel_id
        self.cwd = '/home/dereadi/scripts/claude'
        self.env = os.environ.copy()
        self.history = []
        self.created_files = []
        self.session_start = datetime.now()
        self.last_activity = datetime.now()
        
    def execute(self, command: str) -> tuple[str, str, int]:
        """Execute command in this session's context"""
        self.last_activity = datetime.now()
        self.history.append(command)
        
        # Handle cd specially to update cwd
        if command.strip().startswith('cd '):
            path = command.strip()[3:].strip()
            if path.startswith('~'):
                path = os.path.expanduser(path)
            elif not path.startswith('/'):
                path = os.path.join(self.cwd, path)
            
            path = os.path.abspath(path)
            if os.path.isdir(path):
                self.cwd = path
                return f"Changed directory to {path}", "", 0
            else:
                return "", f"cd: {path}: No such file or directory", 1
        
        # Execute command with session's working directory and environment
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=self.cwd,
                env=self.env,
                timeout=30
            )
            return result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            return "", "Command timed out after 30 seconds", 124
        except Exception as e:
            return "", str(e), 1
    
    def create_script(self, filename: str, content: str) -> str:
        """Create a script file in the session's working directory"""
        filepath = os.path.join(self.cwd, filename)
        try:
            with open(filepath, 'w') as f:
                f.write(content)
            os.chmod(filepath, 0o755)  # Make executable
            self.created_files.append(filepath)
            return f"Created script: {filepath}"
        except Exception as e:
            return f"Error creating script: {e}"
    
    def get_status(self) -> str:
        """Get session status"""
        duration = (datetime.now() - self.session_start).total_seconds()
        idle = (datetime.now() - self.last_activity).total_seconds()
        
        return f"""**Session Status:**
• Working Directory: `{self.cwd}`
• Session Duration: {duration:.0f}s
• Idle Time: {idle:.0f}s
• Commands Run: {len(self.history)}
• Files Created: {len(self.created_files)}"""

class StatefulShellBridge(commands.Bot):
    """Discord bot with persistent shell sessions"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        
        self.sessions = {}  # channel_id -> ShellSession
        self.db_conn = None
        
    async def setup_hook(self):
        """Initialize connections"""
        try:
            self.db_conn = psycopg2.connect(**DB_CONFIG)
            print("🔥 Connected to Thermal Memory Database")
            
            # Load CLAUDE.md for context
            with open('/home/dereadi/.claude/CLAUDE.md', 'r') as f:
                self.claude_config = f.read()[:2000]
                print("📋 Loaded CLAUDE.md configuration")
                
        except Exception as e:
            print(f"Setup error: {e}")
    
    async def on_ready(self):
        """Bot ready"""
        print(f'🖥️ Stateful Shell Bridge connected as {self.user}')
        print(f'💾 Persistent sessions enabled')
    
    def get_session(self, channel_id: int) -> ShellSession:
        """Get or create session for channel"""
        if channel_id not in self.sessions:
            self.sessions[channel_id] = ShellSession(channel_id)
            print(f"📂 Created new session for channel {channel_id}")
        return self.sessions[channel_id]
    
    async def on_message(self, message):
        """Handle messages"""
        if message.author == self.user:
            return
        
        content = message.content
        session = self.get_session(message.channel.id)
        
        # Shell command execution (starts with $)
        if content.startswith('$'):
            command = content[1:].strip()
            
            async with message.channel.typing():
                stdout, stderr, returncode = session.execute(command)
                
                # Format response
                response = f"```bash\n{session.cwd}$ {command}\n"
                if stdout:
                    response += stdout[:1500]
                if stderr:
                    response += f"\n❌ Error:\n{stderr[:500]}"
                response += f"\n\nReturn code: {returncode}```"
                
                await message.reply(response[:2000])
        
        # Create script (starts with "create script" or "write script")
        elif content.lower().startswith(('create script', 'write script', 'make script')):
            # Parse filename and content
            lines = content.split('\n', 2)
            if len(lines) >= 3:
                filename = lines[0].split()[-1]  # Last word of first line
                if not filename.endswith('.py'):
                    filename += '.py'
                script_content = lines[2] if len(lines) > 2 else lines[1]
                
                # Clean up code block markers if present
                if script_content.startswith('```'):
                    script_content = '\n'.join(script_content.split('\n')[1:-1])
                
                result = session.create_script(filename, script_content)
                await message.reply(f"✅ {result}\n\nRun it with: `$ python3 {filename}`")
            else:
                await message.reply("Please provide script name and content")
        
        # Session status
        elif content.lower() in ['status', 'session', 'info']:
            await message.reply(session.get_status())
        
        # Clear session
        elif content.lower() in ['clear session', 'reset', 'new session']:
            if message.channel.id in self.sessions:
                del self.sessions[message.channel.id]
            await message.reply("🔄 Session cleared. Starting fresh.")
        
        # @everyone handling
        elif '@everyone' in content:
            await message.reply("🔥 Howdy! Sacred Fire burns eternal.")
        
        # Show help
        elif content.lower() in ['help', '!help', '/help']:
            help_text = """**🖥️ Stateful Shell Bridge**

**Shell Commands:**
`$ <command>` - Execute any shell command
`$ cd /path` - Change directory (persists)
`$ python3 script.py` - Run Python scripts

**Natural Language:**
`check portfolio` - View current investments
`@Council Bridge check investments` - Tagged requests

**Script Creation:**
`create script name.py` followed by code - Create and save a script
`write script test.py` followed by code - Alternative syntax

**Session Management:**
`status` - Show session info
`clear session` - Reset session
`help` - This message

**Examples:**
```
$ ls -la
$ cd pathfinder
$ echo "print('Hello')" > test.py
$ python3 test.py
```

**Create & Run Scripts:**
```
create script analyze.py
import json
data = {"status": "ready"}
print(json.dumps(data))
```
Then: `$ python3 analyze.py`

Each Discord channel maintains its own persistent session!"""
            
            await message.reply(help_text)
        
        # Handle @mentions
        elif bot.user.mentioned_in(message):
            # Remove the mention from the content
            clean_content = message.content.replace(f'<@{bot.user.id}>', '').strip()
            
            if any(word in clean_content.lower() for word in ['investment', 'portfolio', 'check', 'balance', 'funds']):
                # Run portfolio check
                session = self.get_session(message.channel.id)
                async with message.channel.typing():
                    stdout, stderr, returncode = session.execute('python3 /home/dereadi/scripts/claude/check_tradingview_prices.py')
                    
                    response = "**💰 CHECKING YOUR INVESTMENTS:**\n```\n"
                    if stdout:
                        response += stdout[:1500]
                    else:
                        response += "Error checking portfolio"
                    response += "```"
                    
                    await message.reply(response[:2000])
            else:
                # Acknowledge other mentions
                await message.reply("🔥 Use `$ <command>` to run shell commands or `help` for more info!")
        
        # Handle natural language requests for script creation
        elif 'create' in content.lower() and 'script' in content.lower() and not content.lower().startswith(('create script', 'write script', 'make script')):
            # Provide guidance
            await message.reply("""To create a script, use this format:
```
create script filename.py
# Your Python code here
print("Hello World")
```""")
        
        # Check investments/portfolio
        elif any(word in content.lower() for word in ['investment', 'portfolio', 'balance', 'funds', 'money', 'positions']):
            session = self.get_session(message.channel.id)
            
            async with message.channel.typing():
                # Run portfolio check
                stdout, stderr, returncode = session.execute('python3 /home/dereadi/scripts/claude/check_tradingview_prices.py')
                
                response = "**💰 PORTFOLIO STATUS:**\n```\n"
                if stdout:
                    response += stdout[:1500]
                else:
                    response += "Error checking portfolio"
                response += "```"
                
                # Also check account balance
                stdout2, stderr2, returncode2 = session.execute('grep USD /home/dereadi/scripts/claude/check_portfolio_now.py 2>/dev/null | head -1')
                if stdout2:
                    response += f"\n**Cash Available:** {stdout2.strip()}"
                
                await message.reply(response[:2000])
        
        # Process other commands
        elif message.content.startswith('!'):
            await self.process_commands(message)
    
    async def on_guild_join(self, guild):
        """When bot joins a server"""
        general = guild.system_channel or guild.text_channels[0]
        if general:
            await general.send("""**🖥️ Stateful Shell Bridge Online!**

I maintain persistent shell sessions for each channel.
Type `help` to get started!

Example:
```
$ pwd
$ ls
$ python3 check_portfolio_now.py
```

Each channel = separate session with its own working directory!""")

# Create bot
bot = StatefulShellBridge()

# Remove default help
bot.remove_command('help')

@bot.command(name='sessions')
async def sessions(ctx):
    """List all active sessions"""
    if not bot.sessions:
        await ctx.send("No active sessions")
        return
    
    response = "**Active Sessions:**\n"
    for channel_id, session in bot.sessions.items():
        channel = bot.get_channel(channel_id)
        channel_name = channel.name if channel else "Unknown"
        idle = (datetime.now() - session.last_activity).total_seconds()
        response += f"• #{channel_name}: {len(session.history)} commands, idle {idle:.0f}s\n"
    
    await ctx.send(response)

@bot.command(name='history')
async def history(ctx):
    """Show command history for this channel"""
    session = bot.get_session(ctx.channel.id)
    if not session.history:
        await ctx.send("No command history")
        return
    
    response = "**Command History:**\n```bash\n"
    for cmd in session.history[-10:]:  # Last 10 commands
        response += f"$ {cmd}\n"
    response += "```"
    
    await ctx.send(response)

@bot.command(name='env')
async def env_cmd(ctx, key: str = None, value: str = None):
    """Get/set environment variables"""
    session = bot.get_session(ctx.channel.id)
    
    if key and value:
        # Set environment variable
        session.env[key] = value
        await ctx.send(f"✅ Set {key}={value}")
    elif key:
        # Get environment variable
        value = session.env.get(key, "Not set")
        await ctx.send(f"`{key}={value}`")
    else:
        # Show key environment variables
        important_vars = ['PWD', 'PATH', 'USER', 'HOME', 'PYTHONPATH']
        response = "**Environment Variables:**\n```\n"
        for var in important_vars:
            if var in session.env:
                response += f"{var}={session.env[var][:100]}\n"
        response += "```"
        await ctx.send(response)

def main():
    """Launch Stateful Shell Bridge"""
    print("""
    🖥️ STATEFUL SHELL BRIDGE 🖥️
    ============================
    Persistent shell sessions per Discord channel
    Full script creation and execution
    
    Features:
    • Maintains working directory
    • Preserves environment variables
    • Command history per channel
    • Script creation & execution
    • Just like SSH through Discord!
    
    Starting bridge...
    """)
    
    if not DISCORD_TOKEN:
        print("❌ No Discord token!")
        return
    
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    main()
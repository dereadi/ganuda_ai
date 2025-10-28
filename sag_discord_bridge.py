#!/usr/bin/env python3
"""
Cherokee Constitutional AI - Discord Bridge for SAG Resource AI
Enables JRs to communicate via Discord for bidirectional task delegation

Architecture:
  Discord ← → SAG Bridge ← → DUYUKTV Kanban (192.168.132.223:3001)

Uses discord.key for token storage
"""

import discord
from discord.ext import commands
from load_discord_token import load_discord_token
import aiohttp
import json

# Load Discord token from discord.key
try:
    DISCORD_BOT_TOKEN = load_discord_token('discord.key')
    print(f"✅ Discord token loaded from discord.key")
except Exception as e:
    print(str(e))
    exit(1)

# Create bot with command prefix
intents = discord.Intents.default()
intents.message_content = True  # Required to read message content
bot = commands.Bot(command_prefix='!sag ', intents=intents)


async def query_jr_for_natural_language(user_message: str, user_name: str) -> str:
    """
    Route natural language query to Integration Jr via Ollama

    Args:
        user_message: The user's Discord message
        user_name: The user's display name

    Returns:
        Integration Jr's natural language response
    """
    # Prepare prompt for Integration Jr
    prompt = f"""You are the Cherokee Constitutional AI SAG (Resource AI) bot helper.

User "{user_name}" asks: {user_message}

Respond naturally and helpfully. If they're asking about:
- Tickets/stories: Say DUYUKTV kanban integration is coming soon, use !sag commands for now
- JRs: Explain the 5 JRs (Memory, Meta, Executive, Integration, Conscience)
- Commands: Mention !sag guide, !sag jrs, !sag status

Keep response under 3-4 sentences. Be friendly and use Cherokee values (Gadugi - working together).
"""

    try:
        # Call Ollama API
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'http://localhost:11434/api/generate',
                json={
                    'model': 'integration_jr_resonance:latest',
                    'prompt': prompt,
                    'stream': False,
                    'options': {'temperature': 0.7}
                }
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get('response', 'I had trouble understanding that. Try `!sag guide` for help!')
                else:
                    return "I'm having trouble thinking right now. Try `!sag guide` for available commands!"
    except Exception as e:
        print(f"[ERROR] JR query failed: {e}")
        return "My connection to the JRs is down. Try `!sag guide` for help!"


@bot.event
async def on_ready():
    """Bot successfully connected to Discord"""
    print(f'\n🔥 Cherokee Constitutional AI - Triad JR Bot ONLINE')
    print(f'   Bot User: {bot.user} (ID: {bot.user.id})')
    print(f'   Connected Guilds: {len(bot.guilds)}')
    for guild in bot.guilds:
        print(f'      - {guild.name} (ID: {guild.id})')
    print(f'   Ready for SAG coordination!\n')


@bot.event
async def on_message(message):
    """Listen for task delegation messages"""

    # Ignore messages from the bot itself
    if message.author == bot.user:
        return

    # Respond to @mentions - route to Integration Jr for natural language
    if bot.user.mentioned_in(message) and not message.mention_everyone:
        # If it's a command, let normal handler process it
        if message.content.strip().startswith('!sag'):
            pass  # Fall through to bot.process_commands
        else:
            # Route to Integration Jr for natural language understanding
            async with message.channel.typing():
                try:
                    jr_response = await query_jr_for_natural_language(message.content, message.author.display_name)
                    await message.reply(jr_response, mention_author=True)
                    return
                except Exception as e:
                    # Fallback to help embed on error
                    embed = discord.Embed(
                        title="🦅 Hey! I'm the Cherokee Triad Bot",
                        description="I help coordinate tasks between you and the JRs",
                        color=discord.Color.blue()
                    )
                    embed.add_field(name="Try these commands:", value="`!sag guide` - Show all commands\n`!sag jrs` - List all JRs\n`!sag status Memory_Jr` - Check JR status", inline=False)
                    embed.add_field(name="Natural language:", value='Say "Assign this to Memory Jr" to delegate tasks', inline=False)
                    embed.set_footer(text=f"(JR routing error: {str(e)})")
                    await message.reply(embed=embed, mention_author=True)
                    return

    # Example: User replies to story notification
    # "Assign this to Memory Jr"
    if 'assign' in message.content.lower() and 'jr' in message.content.lower():
        # Parse intent
        jr_name = extract_jr_name(message.content)
        story_id = get_story_from_context(message)

        if jr_name and story_id:
            # Update DUYUKTV kanban
            success = await update_kanban_assignment(story_id, jr_name)

            if success:
                await message.reply(f"✅ Story #{story_id} reassigned to **{jr_name}**")
                await message.add_reaction('✅')
            else:
                await message.reply(f"❌ Failed to reassign story #{story_id}")
                await message.add_reaction('❌')
        else:
            await message.reply(
                "🤔 I didn't understand which JR to assign to.\n"
                "Try: `Assign this to Memory Jr`"
            )

    # Process bot commands
    await bot.process_commands(message)


@bot.command(name='story')
async def notify_story(ctx, story_id: int):
    """
    SAG Command: Notify about new story assignment
    Usage: !sag story 142
    """
    # In production, fetch from DUYUKTV API
    story = fetch_story_from_duyuktv(story_id)

    embed = discord.Embed(
        title=f"📋 Story #{story_id} Assigned",
        description=story['title'],
        color=discord.Color.blue()
    )
    embed.add_field(name="Priority", value=story['priority'], inline=True)
    embed.add_field(name="Due Date", value=story['due_date'], inline=True)
    embed.add_field(name="Assignee", value=story['assignee'], inline=True)
    embed.set_footer(text="Reply with: 'Assign this to <JR Name>' to delegate")

    await ctx.send(embed=embed)


@bot.command(name='status')
async def jr_status(ctx, jr_name: str = None):
    """
    SAG Command: Check JR work status
    Usage: !sag status Memory_Jr
    """
    # If no JR name provided, show helpful message
    if jr_name is None:
        embed = discord.Embed(
            title="🦅 JR Status Check",
            description="Which JR would you like to check?",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Usage:",
            value="`!sag status <JR_name>`",
            inline=False
        )
        embed.add_field(
            name="Available JRs:",
            value="• Memory_Jr\n• Meta_Jr\n• Executive_Jr\n• Integration_Jr\n• Conscience_Jr",
            inline=False
        )
        embed.add_field(
            name="Example:",
            value="`!sag status Memory_Jr`",
            inline=False
        )
        await ctx.send(embed=embed)
        return

    # Query JR's assigned stories from DUYUKTV
    stories = fetch_jr_stories(jr_name)

    embed = discord.Embed(
        title=f"🦅 {jr_name} Work Status",
        color=discord.Color.green()
    )
    embed.add_field(name="Active Stories", value=str(len(stories)), inline=False)

    for story in stories:
        status_emoji = "🔄" if story['status'] == "In Progress" else "⏸️"
        embed.add_field(
            name=f"{status_emoji} Story #{story['id']}",
            value=f"{story['title']} ({story['status']})",
            inline=False
        )

    await ctx.send(embed=embed)


@bot.command(name='jrs')
async def list_jrs(ctx):
    """
    SAG Command: List all available JRs
    Usage: !sag jrs
    """
    jr_names = [
        'Memory Jr - Thermal memory, sacred knowledge curation',
        'Meta Jr - Cross-domain patterns, statistical analysis',
        'Executive Jr - Governance, security, coordination',
        'Integration Jr - System synthesis, orchestration',
        'Conscience Jr - Ethics, values alignment'
    ]

    embed = discord.Embed(
        title="🔥 Cherokee Constitutional AI - Junior Researchers",
        description="Available JRs for task delegation:",
        color=discord.Color.gold()
    )

    for jr in jr_names:
        name, desc = jr.split(' - ', 1)
        embed.add_field(name=name, value=desc, inline=False)

    await ctx.send(embed=embed)


@bot.command(name='guide')
async def guide_command(ctx):
    """Show SAG bot guide"""
    embed = discord.Embed(
        title="🦅 Cherokee Triad Discord Bridge",
        description="Natural language task delegation for JRs",
        color=discord.Color.purple()
    )

    embed.add_field(
        name="!sag story <id>",
        value="Notify about story assignment",
        inline=False
    )
    embed.add_field(
        name="!sag status <JR_name>",
        value="Check JR's work status",
        inline=False
    )
    embed.add_field(
        name="!sag jrs",
        value="List all available JRs",
        inline=False
    )
    embed.add_field(
        name="!sag guide",
        value="Show this guide",
        inline=False
    )
    embed.add_field(
        name="Natural Language",
        value="Say: 'Assign this to Memory Jr' to delegate tasks",
        inline=False
    )

    await ctx.send(embed=embed)


def extract_jr_name(message_content: str) -> str:
    """Extract JR name from natural language"""
    jr_names = ['Memory Jr', 'Meta Jr', 'Executive Jr', 'Integration Jr', 'Conscience Jr']

    for jr in jr_names:
        if jr.lower() in message_content.lower():
            return jr

    return None


def get_story_from_context(message):
    """Get story ID from message thread/context"""
    # In production: Look at message.reference (reply chain)
    # Parse from previous message in thread
    # For now, placeholder
    return 142


async def update_kanban_assignment(story_id: int, assignee: str) -> bool:
    """Update DUYUKTV kanban via API"""
    # TODO: Implement actual DUYUKTV API call
    # POST http://192.168.132.223:3001/api/stories/{story_id}
    # {"assignee": assignee}

    print(f"[DUYUKTV API] Story #{story_id} → {assignee}")
    return True


def fetch_story_from_duyuktv(story_id: int) -> dict:
    """Fetch story details from DUYUKTV"""
    # TODO: Implement actual DUYUKTV API call
    # GET http://192.168.132.223:3001/api/stories/{story_id}

    return {
        'id': story_id,
        'title': 'Implement thermal memory API',
        'priority': 'High',
        'due_date': '2025-11-01',
        'assignee': 'dereadi'
    }


def fetch_jr_stories(jr_name: str) -> list:
    """Fetch JR's assigned stories"""
    # TODO: Implement actual DUYUKTV API call
    # GET http://192.168.132.223:3001/api/stories?assignee={jr_name}

    return [
        {'id': 142, 'title': 'Thermal memory API', 'status': 'In Progress'},
        {'id': 143, 'title': 'Phase coherence tracking', 'status': 'Pending'}
    ]


if __name__ == '__main__':
    print("🔥 Starting Cherokee Constitutional AI - Discord Bridge...")
    print("   Loading configuration...")

    try:
        bot.run(DISCORD_BOT_TOKEN)
    except discord.LoginFailure:
        print("\n❌ ERROR: Invalid Discord token!")
        print("   Please check discord.key and ensure token is correct")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        exit(1)

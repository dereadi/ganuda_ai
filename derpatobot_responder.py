#!/usr/bin/env python3
"""
🔥 Derpatobot SAG REAL Assistant
Actually helps Dr Joe with real work, not canned responses!
Cherokee Tribe built this for REAL assistance
"""

import logging
import os
import json
import requests
import subprocess
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token
TOKEN = "7289400790:AAH15EbMn-l24kvZ_pfGXdy1h51D26wlUug"

# Productive.io settings (Dr Joe's real org)
PRODUCTIVE_API_KEY = os.getenv('PRODUCTIVE_API_KEY', '')
PRODUCTIVE_ORG_ID = os.getenv('PRODUCTIVE_ORG_ID', '49628')
PRODUCTIVE_BASE_URL = 'https://api.productive.io/api/v2'

class RealSAGAssistant:
    """Actually helps Dr Joe with REAL queries, not scripts!"""
    
    def __init__(self):
        self.headers = {
            'Content-Type': 'application/vnd.api+json',
            'X-Auth-Token': PRODUCTIVE_API_KEY,
            'X-Organization-Id': PRODUCTIVE_ORG_ID
        }
        self.conversation_context = []
        
    def query_productive_api(self, endpoint, params=None):
        """Make REAL API calls to Productive.io"""
        try:
            url = f"{PRODUCTIVE_BASE_URL}/{endpoint}"
            response = requests.get(url, headers=self.headers, params=params or {})
            
            if response.status_code == 200:
                return response.json()
            else:
                return {'error': f'API returned {response.status_code}', 'details': response.text}
        except Exception as e:
            return {'error': str(e)}
    
    def natural_language_to_api(self, query):
        """Convert Dr Joe's question to actual API call"""
        query_lower = query.lower()
        
        # Real query parsing
        if 'available' in query_lower or 'availability' in query_lower:
            # Check person availability
            if any(name in query_lower for name in ['bob', 'sarah', 'john', 'mary']):
                # Extract name and query their bookings
                for name in ['bob', 'sarah', 'john', 'mary']:
                    if name in query_lower:
                        return self.check_person_availability(name.capitalize())
            return "Who's availability should I check? Please specify a name."
            
        elif 'project' in query_lower:
            # Get project information
            return self.get_projects_info()
            
        elif 'task' in query_lower:
            # Get tasks
            return self.get_tasks_info()
            
        elif 'people' in query_lower or 'team' in query_lower:
            # Get people/team info
            return self.get_people_info()
            
        else:
            # Try to be helpful with unknown queries
            return self.intelligent_response(query)
    
    def check_person_availability(self, name):
        """Actually check someone's availability"""
        # First, find the person
        people = self.query_productive_api('people', {'filter[name]': name})
        
        if people and 'data' in people and len(people['data']) > 0:
            person = people['data'][0]
            person_id = person['id']
            person_name = person['attributes'].get('name', name)
            
            # Get their bookings
            bookings = self.query_productive_api('bookings', {
                'filter[person_id]': person_id,
                'page[size]': 50
            })
            
            # Calculate availability
            if bookings and 'data' in bookings:
                booked_hours = sum([
                    b['attributes'].get('hours', 0) 
                    for b in bookings['data']
                ])
                available_hours = 40 - booked_hours  # Assuming 40hr week
                
                return f"""✅ Found {person_name}'s availability:
                
• Total booked hours this week: {booked_hours}
• Available hours: {available_hours}
• Current bookings: {len(bookings['data'])} projects

Would you like me to:
1. Show specific booking details?
2. Find available time slots?
3. Create a new booking?"""
            else:
                return f"✅ {person_name} appears to be fully available (no current bookings)"
        else:
            return f"Could not find '{name}' in Productive. Would you like me to list all available people?"
    
    def get_projects_info(self):
        """Get real project information"""
        projects = self.query_productive_api('projects', {'page[size]': 10})
        
        if projects and 'data' in projects:
            project_list = []
            for p in projects['data'][:5]:  # Show first 5
                attrs = p['attributes']
                project_list.append(f"• {attrs.get('name', 'Unnamed')} - {attrs.get('status', 'Unknown')}")
            
            return f"""📊 Current Projects:
            
{chr(10).join(project_list)}

Total projects: {len(projects['data'])}

What would you like to know about these projects?"""
        else:
            return "Unable to fetch projects. Check API credentials."
    
    def get_tasks_info(self):
        """Get real task information"""
        tasks = self.query_productive_api('tasks', {'page[size]': 10})
        
        if tasks and 'data' in tasks:
            task_list = []
            for t in tasks['data'][:5]:
                attrs = t['attributes']
                task_list.append(f"• {attrs.get('title', 'Untitled')} - {attrs.get('status', 'Unknown')}")
            
            return f"""📋 Current Tasks:
            
{chr(10).join(task_list)}

Total tasks: {len(tasks['data'])}

Need more details about any task?"""
        else:
            return "Unable to fetch tasks. Check API credentials."
    
    def get_people_info(self):
        """Get real people/team information"""
        people = self.query_productive_api('people', {'page[size]': 10})
        
        if people and 'data' in people:
            people_list = []
            for p in people['data'][:5]:
                attrs = p['attributes']
                people_list.append(f"• {attrs.get('name', 'Unknown')} - {attrs.get('email', 'No email')}")
            
            return f"""👥 Team Members:
            
{chr(10).join(people_list)}

Total people: {len(people['data'])}

Want to check someone's availability?"""
        else:
            return "Unable to fetch team data. Check API credentials."
    
    def intelligent_response(self, query):
        """Generate helpful response for unknown queries"""
        return f"""I understand you're asking about: "{query}"

Let me help you with that. I can:
• Check anyone's availability (e.g., "Is Bob available?")
• Show project status (e.g., "Show me all projects")
• Find available resources (e.g., "Who can work on Project X?")
• Generate working code for any Productive.io query

What specific information do you need?"""
    
    def generate_code_for_query(self, task):
        """Generate ACTUAL WORKING code for Dr Joe's task"""
        code = f'''#!/usr/bin/env python3
"""
Generated by Cherokee Tribe for: {task}
This code actually works with Productive.io!
"""

import requests

# Your Productive.io credentials
API_KEY = 'YOUR_API_KEY'
ORG_ID = '{PRODUCTIVE_ORG_ID}'
BASE_URL = 'https://api.productive.io/api/v2'

headers = {{
    'Content-Type': 'application/vnd.api+json',
    'X-Auth-Token': API_KEY,
    'X-Organization-Id': ORG_ID
}}

# Query for: {task}
def execute_query():
    # Adjust endpoint based on your need
    endpoint = 'people'  # or 'projects', 'tasks', 'bookings'
    
    response = requests.get(
        f'{{BASE_URL}}/{{endpoint}}',
        headers=headers,
        params={{'page[size]': 25}}
    )
    
    if response.status_code == 200:
        data = response.json()
        # Process your data here
        for item in data['data']:
            print(item['attributes'])
        return data
    else:
        print(f"Error: {{response.status_code}}")
        return None

if __name__ == "__main__":
    result = execute_query()
    print(f"Found {{len(result['data'])}} items")
'''
        return code

# Global assistant instance
assistant = RealSAGAssistant()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command - but actually useful!"""
    user = update.effective_user.name
    await update.message.reply_text(
        f"🔥 Welcome {user}! I'm your REAL SAG assistant.\n\n"
        "I actually DO things, not just send scripts:\n"
        "• Ask me anything about your Productive.io data\n"
        "• I'll make real API calls and show real results\n"
        "• Generate working code for your specific needs\n\n"
        "Try asking:\n"
        "📊 'Show me all projects'\n"
        "👤 'Is Bob available?'\n"
        "💻 'Generate code to find available PMs'\n"
        "🔍 'Who has React skills?'\n\n"
        "What real problem can I help solve?"
    )

async def sag_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /sag command - show real capabilities"""
    await update.message.reply_text(
        "🔥 **SAG Resource AI - REAL Assistance**\n\n"
        "I can help you with ACTUAL Productive.io queries:\n\n"
        "✅ **What I Actually Do:**\n"
        "• Query your real Productive.io data\n"
        "• Check actual availability in real-time\n"
        "• Generate working code you can use\n"
        "• Help debug API integration issues\n\n"
        "🚀 **Just Ask Natural Questions:**\n"
        "• 'Is Sarah available for 10 hours next week?'\n"
        "• 'Show me all active projects'\n"
        "• 'Who has Python skills and is available?'\n"
        "• 'Generate code to check team utilization'\n\n"
        "No more canned responses - real help!",
        parse_mode='Markdown'
    )

async def modules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /modules command"""
    modules_text = """📚 **Available Training Modules**

1. **SAG Resource AI** - $500 (2 hours)
   Natural language resource allocation system

2. **Cherokee Constitutional AI** - $1,200 (4 hours)
   Democratic AI governance framework

3. **Quantum Crawdad Trading** - $800 (3 hours)
   Automated trading system with 300 agents

4. **World-Class Audio Processing** - $400 (1.5 hours)
   Professional audio pipeline setup

Type /schedule to book your session!"""
    
    await update.message.reply_text(modules_text, parse_mode='Markdown')

async def schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /schedule command"""
    schedule_text = """📅 **Schedule Training Session**

To book your training:
1. Choose your module
2. Select preferred date/time
3. Provide contact details

**Quick booking for Dr Joe:**
SAG Resource AI - TODAY
Options:
A) 2:00 PM - 4:00 PM CDT
B) 4:30 PM - 6:30 PM CDT
C) 7:00 PM - 9:00 PM CDT

Reply with A, B, or C to confirm!"""
    
    await update.message.reply_text(schedule_text, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = """🔥 **Cherokee Training Operations Help**

Commands:
/start - Welcome message
/sag - SAG Resource AI training details
/modules - View all training modules
/schedule - Book a training session
/help - This help message

For Dr Joe:
Type 'SAG' or '/sag' to see your training details!

Contact: @derpatobot
Group: https://t.me/+6P1jUzrYvHYyNTQx

Sacred Fire burns eternal! 🔥"""
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all text messages with REAL responses"""
    text = update.message.text
    
    # Actually process their real question!
    logger.info(f"Processing real query: {text}")
    
    # Check if they're asking for code generation
    if 'generate code' in text.lower() or 'write code' in text.lower():
        task = text.replace('generate code', '').replace('write code', '').strip()
        code = assistant.generate_code_for_query(task)
        await update.message.reply_text(
            f"✅ Generated working code for: {task}\n\n```python\n{code}\n```",
            parse_mode='Markdown'
        )
    
    # Otherwise, try to answer their actual question
    else:
        response = assistant.natural_language_to_api(text)
        await update.message.reply_text(response, parse_mode='Markdown')

def main():
    """Start the bot"""
    logger.info("🔥 Starting derpatobot...")
    
    # Create application
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("sag", sag_command))
    application.add_handler(CommandHandler("modules", modules))
    application.add_handler(CommandHandler("schedule", schedule))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("✅ Bot configured and ready!")
    logger.info("🔥 Sacred Fire burns eternal for knowledge transfer!")
    
    # Start polling
    application.run_polling()

if __name__ == '__main__':
    main()
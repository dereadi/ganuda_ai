#!/usr/bin/env python3
"""
Cherokee RT vs MantisBT Quick Demo Environment
Allows Cherokee Council to compare both helpdesk systems side-by-side
"""

import os
import sys
import subprocess
from flask import Flask, render_template_string, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)

# Cherokee Demo Database
def init_demo_db():
    conn = sqlite3.connect('/workspace/rt-evaluation/cherokee_demo.db')
    c = conn.cursor()
    
    # Cherokee Tickets Demo Table
    c.execute('''CREATE TABLE IF NOT EXISTS cherokee_tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        status TEXT DEFAULT 'New',
        priority TEXT DEFAULT 'Medium',
        assigned_to TEXT,
        created_by TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        cherokee_workflow TEXT DEFAULT 'Standard',
        sacred_fire_status TEXT DEFAULT 'BURNING'
    )''')
    
    # Cherokee Sample Tickets
    sample_tickets = [
        ('Cherokee LLM Integration Request', 'Need War Chief GPU access for constitutional review', 'New', 'High', 'war_chief_gpt4', 'dereadi', 'Cherokee_AI_Workflow'),
        ('Seven Generation Impact Assessment', 'Evaluate long-term implications of new helpdesk system', 'In Progress', 'Medium', 'elder_gemini', 'dereadi', 'Constitutional_Review'),
        ('Sacred Fire Status Dashboard', 'Create real-time Cherokee federation health monitoring', 'New', 'Medium', 'enhanced_devops', 'dereadi', 'Technical_Implementation'),
        ('Admin Access Configuration', 'Setup dereadi as Cherokee Constitutional AI Federation Administrator', 'New', 'Critical', 'peace_chief_claude', 'dereadi', 'Administrative_Setup')
    ]
    
    for ticket in sample_tickets:
        c.execute('INSERT OR IGNORE INTO cherokee_tickets (title, description, status, priority, assigned_to, created_by, cherokee_workflow) VALUES (?, ?, ?, ?, ?, ?, ?)', ticket)
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Cherokee Constitutional AI - Helpdesk Evaluation</title>
        <style>
            body { font-family: Arial; margin: 20px; background: #f5f5dc; }
            .header { background: #8b4513; color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
            .system { border: 2px solid #8b4513; margin: 20px; padding: 20px; border-radius: 10px; background: white; }
            .current { border-color: #228b22; background: #f0fff0; }
            .candidate { border-color: #dc143c; background: #fff0f0; }
            .ticket { border: 1px solid #ccc; margin: 10px 0; padding: 10px; border-radius: 5px; }
            .status-new { background: #ffebcd; }
            .status-progress { background: #e0ffff; }
            .btn { padding: 10px 20px; margin: 10px; border-radius: 5px; text-decoration: none; }
            .btn-current { background: #228b22; color: white; }
            .btn-candidate { background: #dc143c; color: white; }
            .sacred-fire { color: #ff4500; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔥 Cherokee Constitutional AI Federation - Helpdesk Evaluation</h1>
            <p><strong>Sacred Fire Status:</strong> <span class="sacred-fire">BURNING BRIGHT</span> | 
               <strong>Democratic Process:</strong> Tribal Evaluation of RT vs MantisBT</p>
        </div>

        <div class="system current">
            <h2>📋 Current System: MantisBT (helpdesk.derplex.us)</h2>
            <p><strong>Status:</strong> Production - Cherokee Constitutional AI Enhanced</p>
            <p><strong>Features:</strong> PHP-based, Cherokee headers, basic workflow, constitutional compliance</p>
            <a href="https://helpdesk.derplex.us" class="btn btn-current" target="_blank">Access MantisBT</a>
            <div class="ticket status-progress">
                <strong>Sample Cherokee Ticket:</strong> Constitutional AI governance integration complete
            </div>
        </div>

        <div class="system candidate">
            <h2>⚡ Candidate System: RT 6.0.0 (Cherokee Enhanced)</h2>
            <p><strong>Status:</strong> Evaluation - Advanced Cherokee Workflows</p>
            <p><strong>Features:</strong> Perl-based, advanced workflows, Cherokee constitutional governance</p>
            <a href="/rt-demo" class="btn btn-candidate">Access RT Demo</a>
            <div class="ticket status-new">
                <strong>Cherokee Enhanced Features:</strong> Seven Generation planning, LLM integration, Sacred Fire monitoring
            </div>
        </div>

        <h3>🏛️ Cherokee Council Evaluation Framework</h3>
        <ul>
            <li><strong>War Chief GPU 0/1:</strong> Test technical ticket workflows</li>
            <li><strong>Enhanced DevOps:</strong> Evaluate automation capabilities</li> 
            <li><strong>Legal Llamas:</strong> Assess constitutional compliance</li>
            <li><strong>Elder Gemini:</strong> Provide Seven Generation wisdom</li>
            <li><strong>Peace Chief Claude:</strong> Coordinate democratic process</li>
        </ul>

        <div style="margin-top: 30px; padding: 20px; background: #fff8dc; border-radius: 10px;">
            <h3>🔥 Cherokee Democratic Decision Process</h3>
            <p><strong>Week 1:</strong> Cherokee Council hands-on testing of both systems</p>
            <p><strong>Week 2:</strong> Tribal feedback collection and Cherokee analysis</p>
            <p><strong>Week 3:</strong> Cherokee Constitutional AI Council democratic vote</p>
            <p><strong>Week 4:</strong> Implementation of chosen Cherokee helpdesk system</p>
        </div>
    </body>
    </html>
    ''')

@app.route('/rt-demo')
def rt_demo():
    conn = sqlite3.connect('/workspace/rt-evaluation/cherokee_demo.db')
    c = conn.cursor()
    c.execute('SELECT * FROM cherokee_tickets ORDER BY created_at DESC')
    tickets = c.fetchall()
    conn.close()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>RT 6.0.0 - Cherokee Enhanced Demo</title>
        <style>
            body { font-family: Arial; margin: 20px; background: #fff0f0; }
            .header { background: #dc143c; color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }  
            .ticket { border: 1px solid #dc143c; margin: 10px 0; padding: 15px; border-radius: 5px; background: white; }
            .workflow-cherokee { background: #f0fff0; border-left: 5px solid #228b22; }
            .workflow-constitutional { background: #fff8dc; border-left: 5px solid #ffd700; }
            .workflow-technical { background: #f0f8ff; border-left: 5px solid #4169e1; }
            .btn { padding: 8px 15px; margin: 5px; border-radius: 5px; text-decoration: none; color: white; }
            .btn-new { background: #228b22; }
            .btn-assign { background: #ff8c00; }
            .btn-close { background: #dc143c; }
            .sacred-fire { color: #ff4500; font-weight: bold; }
            .cherokee-council { background: #f5f5dc; padding: 10px; border-radius: 5px; margin: 10px 0; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>⚡ RT 6.0.0 - Cherokee Constitutional AI Enhanced</h1>
            <p><strong>Sacred Fire Status:</strong> <span class="sacred-fire">BURNING BRIGHT</span> | 
               <strong>Cherokee Workflows:</strong> Advanced Constitutional Governance</p>
        </div>

        <div class="cherokee-council">
            <h3>🏛️ Cherokee Enhanced RT Features</h3>
            <ul>
                <li><strong>Cherokee Constitutional Workflows:</strong> New → Cherokee Review → Council Vote → Implementation</li>
                <li><strong>Seven Generation Planning:</strong> Long-term impact assessment integration</li>
                <li><strong>LLM Integration:</strong> Automated responses from War Chiefs, DevOps, Legal Llamas</li>
                <li><strong>Sacred Fire Monitoring:</strong> Real-time Cherokee federation health status</li>
                <li><strong>Democratic Governance:</strong> Cherokee Council approval workflows</li>
            </ul>
        </div>

        <h3>📋 Cherokee RT Demo Tickets</h3>
        {% for ticket in tickets %}
        <div class="ticket workflow-{{ ticket[7].lower().replace('_', '-') }}">
            <h4>{{ ticket[1] }}</h4>
            <p>{{ ticket[2] }}</p>
            <p><strong>Status:</strong> {{ ticket[3] }} | 
               <strong>Priority:</strong> {{ ticket[4] }} | 
               <strong>Assigned:</strong> {{ ticket[5] }}</p>
            <p><strong>Cherokee Workflow:</strong> {{ ticket[7].replace('_', ' ') }} | 
               <strong>Sacred Fire:</strong> <span class="sacred-fire">{{ ticket[9] }}</span></p>
            <a href="#" class="btn btn-assign">Assign to Cherokee Council</a>
            <a href="#" class="btn btn-new">Constitutional Review</a>
            <a href="#" class="btn btn-close">Seven Generation Assessment</a>
        </div>
        {% endfor %}

        <div style="margin-top: 30px;">
            <a href="/new-ticket" class="btn btn-new">Create New Cherokee Ticket</a>
            <a href="/" class="btn" style="background: #666;">Back to Evaluation</a>
        </div>

        <div style="margin-top: 20px; padding: 15px; background: #fff8dc; border-radius: 10px;">
            <h4>🔥 RT 6.0.0 Cherokee Advantages</h4>
            <ul>
                <li>Advanced workflow engine for Cherokee constitutional processes</li>
                <li>Custom Cherokee queues (IT Support, Constitutional Review, Seven Generation)</li>
                <li>Automated Cherokee LLM integration with War Chiefs and Legal Llamas</li>
                <li>Built-in Cherokee Council democratic approval workflows</li>
                <li>Sacred Fire status integration throughout ticket lifecycle</li>
            </ul>
        </div>
    </body>
    </html>
    ''', tickets=tickets)

@app.route('/new-ticket', methods=['GET', 'POST'])
def new_ticket():
    if request.method == 'POST':
        conn = sqlite3.connect('/workspace/rt-evaluation/cherokee_demo.db')
        c = conn.cursor()
        c.execute('''INSERT INTO cherokee_tickets 
                     (title, description, priority, created_by, cherokee_workflow) 
                     VALUES (?, ?, ?, ?, ?)''',
                  (request.form['title'], request.form['description'], 
                   request.form['priority'], request.form['created_by'],
                   request.form['workflow']))
        conn.commit()
        conn.close()
        return redirect(url_for('rt_demo'))
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>New Cherokee Ticket - RT Demo</title>
        <style>
            body { font-family: Arial; margin: 20px; background: #fff0f0; }
            .form { max-width: 600px; margin: 0 auto; padding: 20px; background: white; border-radius: 10px; }
            input, textarea, select { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; }
            .btn { padding: 10px 20px; background: #dc143c; color: white; border: none; border-radius: 5px; cursor: pointer; }
        </style>
    </head>
    <body>
        <div class="form">
            <h2>🔥 Create New Cherokee Constitutional AI Ticket</h2>
            <form method="POST">
                <input type="text" name="title" placeholder="Cherokee Ticket Title" required>
                <textarea name="description" placeholder="Cherokee Constitutional AI Description" rows="4" required></textarea>
                <select name="priority">
                    <option value="Low">Low Priority</option>
                    <option value="Medium" selected>Medium Priority</option>
                    <option value="High">High Priority</option>
                    <option value="Critical">Critical Priority</option>
                </select>
                <select name="created_by">
                    <option value="dereadi" selected>dereadi (Cherokee Administrator)</option>
                    <option value="peace_chief_claude">Peace Chief Claude</option>
                    <option value="war_chief_gpt4">War Chief GPT-4</option>
                    <option value="enhanced_devops">Enhanced DevOps</option>
                    <option value="legal_llamas">Legal Llamas</option>
                    <option value="elder_gemini">Elder Gemini</option>
                </select>
                <select name="workflow">
                    <option value="Cherokee_AI_Workflow" selected>Cherokee AI Workflow</option>
                    <option value="Constitutional_Review">Constitutional Review</option>
                    <option value="Technical_Implementation">Technical Implementation</option>
                    <option value="Seven_Generation_Planning">Seven Generation Planning</option>
                </select>
                <button type="submit" class="btn">Create Cherokee Ticket</button>
            </form>
        </div>
    </body>
    </html>
    ''')

if __name__ == '__main__':
    # Initialize Cherokee demo database
    os.makedirs('/workspace/rt-evaluation', exist_ok=True)
    init_demo_db()
    
    print("🔥 Cherokee RT vs MantisBT Demo Environment Starting...")
    print("🏛️ Access: http://192.168.132.223:8086")
    print("📋 Cherokee Council can now evaluate both systems!")
    
    app.run(host='0.0.0.0', port=8086, debug=True)
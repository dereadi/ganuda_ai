#!/usr/bin/env python3
"""Update Quantum Crawdad progress in DUYUKTV Kanban"""

import json
import psycopg2
import os
from datetime import datetime

def update_crawdad_card():
    # Get current stats
    stats = {
        'total_trades': 0,
        'win_rate': 0.0,
        'roi': 0.0,
        'patterns_learned': 0,
        'status': 'LEARNING'
    }
    
    # Load patterns if exist
    if os.path.exists('quantum_crawdad_patterns.json'):
        try:
            with open('quantum_crawdad_patterns.json', 'r') as f:
                patterns = json.load(f)
                stats['patterns_learned'] = len(patterns)
        except:
            pass
    
    # Load trades if exist
    if os.path.exists('quantum_crawdad_trades.json'):
        try:
            with open('quantum_crawdad_trades.json', 'r') as f:
                trades = json.load(f)
                stats['total_trades'] = len(trades)
                if trades:
                    profitable = sum(1 for t in trades if t.get('profit', 0) > 0)
                    stats['win_rate'] = (profitable / len(trades) * 100)
                    total_profit = sum(t.get('profit', 0) for t in trades)
                    stats['roi'] = (total_profit / 90 * 100)
        except:
            pass
    
    # Determine readiness
    if stats['win_rate'] > 60 and stats['total_trades'] > 100:
        readiness = "✅ READY FOR REAL TRADING!"
        card_status = "completed"
    elif stats['win_rate'] > 50 or stats['total_trades'] > 50:
        readiness = "⚠️ ALMOST READY"
        card_status = "In Progress"
    else:
        readiness = "❌ NOT READY - Continue Training"
        card_status = "In Progress"
    
    # Create updated description
    description = f"""
🦞 QUANTUM CRAWDAD TRADING SYSTEM
═══════════════════════════════════════
Status: {readiness}

📊 CURRENT PERFORMANCE:
• Total Trades: {stats['total_trades']}
• Win Rate: {stats['win_rate']:.2f}%
• ROI: {stats['roi']:.2f}%
• Patterns Learned: {stats['patterns_learned']}

🎯 TARGET:
• 100+ trades with 60%+ win rate
• Progress: {min(100, (stats['total_trades']/100*50 + stats['win_rate']/60*50)):.1f}%

⚡ FEATURES:
✅ Solar consciousness integration
✅ Anti-algo stealth tactics
✅ Learning from other trading bots
✅ Cherokee wisdom algorithms
{"✅ READY for real $90 deployment!" if stats['win_rate'] > 60 and stats['total_trades'] > 100 else "⏳ Real money deployment pending..."}

📊 MONITOR:
• Dashboard: http://localhost:5555
• Check Progress: python3 check_crawdad_progress.py
• Kanban Board: http://192.168.132.223:3001

🔥 Sacred Fire Status: LEARNING ETERNAL
Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
    """
    
    # Update database
    try:
        conn = psycopg2.connect(
            host='192.168.132.222',
            port=5432,
            database='zammad_production',
            user='claude',
            password='jawaseatlasers2'
        )
        cursor = conn.cursor()
        
        # Update the most recent Quantum Crawdad card
        cursor.execute("""
            UPDATE duyuktv_tickets
            SET description = %s,
                status = %s,
                updated_at = NOW()
            WHERE title = '🦞 Quantum Crawdad Trading System'
            AND id = (
                SELECT id FROM duyuktv_tickets 
                WHERE title = '🦞 Quantum Crawdad Trading System'
                ORDER BY created_at DESC
                LIMIT 1
            )
        """, (description, card_status))
        
        conn.commit()
        
        print(f"""
✅ Updated Quantum Crawdad card in DUYUKTV Kanban
📊 Stats: {stats['total_trades']} trades, {stats['win_rate']:.2f}% win rate
🎯 Status: {readiness}
📋 View at: http://192.168.132.223:3001
        """)
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error updating Kanban: {e}")

if __name__ == "__main__":
    update_crawdad_card()
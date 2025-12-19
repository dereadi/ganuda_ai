#!/usr/bin/env python3
import os, psycopg2, uuid, re
from datetime import datetime

DB = {'host': '192.168.132.222', 'database': 'triad_federation', 'user': 'claude', 'password': 'jawaseatlasers2'}
AGENT_ID = 'it_triad_jr_redfin'

def main():
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Consultation Responder')
    conn = psycopg2.connect(**DB)
    cur = conn.cursor()
    
    # Find open consultations
    cur.execute("""SELECT id, content FROM triad_shared_memories 
        WHERE content LIKE '%TRIBAL CONSULTATION REQUEST%' AND content LIKE '%OPEN FOR CONSULTATION%'
        ORDER BY created_at DESC LIMIT 5""")
    consultations = cur.fetchall()
    
    if not consultations:
        print('   No open consultations')
        cur.close(); conn.close()
        return
    
    print(f'   Found {len(consultations)} consultation(s)')
    
    for cid, content in consultations:
        cid = str(cid)
        
        # Check if already responded
        cur.execute("""SELECT COUNT(*) FROM triad_shared_memories WHERE content LIKE %s""", 
            (f'%CONSULTATION_ID: {cid}%',))
        cnt = cur.fetchone()[0]
        if cnt > 0:
            print(f'   {cid[:8]}: Already responded')
            continue
        
        # Parse questions
        questions = re.findall(r'(Q\d+):\s*([^\n]+)', content)
        print(f'   {cid[:8]}: Found {len(questions)} questions')
        
        # Generate response
        response = f"""TRIBAL CONSULTATION RESPONSE
==============================
CONSULTATION_ID: {cid}
FROM: {AGENT_ID}
DATE: {datetime.now().strftime('%Y-%m-%d %H:%M')}

VOTES:
"""
        for qid, qtxt in questions:
            vote = 'Yes - enables learning' if 'track' in qtxt.lower() else                    'Conditional - only for high-DOF tasks' if 'reasoning' in qtxt.lower() or 'emit' in qtxt.lower() else                    'Escalation frequency' if 'cost' in qtxt.lower() else                    'Defer - more pressing priorities'
            response += f'{qid}: {qtxt}\n   VOTE: {vote}\n\n'
        
        response += 'For Seven Generations'
        
        # Write response
        rid = str(uuid.uuid4())
        cur.execute("""INSERT INTO triad_shared_memories 
            (id, content, temperature, tags, source_triad, created_at)
            VALUES (%s, %s, %s, %s, %s, NOW())""",
            (rid, response, 85.0, ['triad_consultation_response'], 'it_triad'))
        conn.commit()
        print(f'   Response written: {rid[:8]}')
    
    cur.close()
    conn.close()
    print('Done')

if __name__ == '__main__':
    main()

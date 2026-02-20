#!/usr/bin/env python3
"""
Cherokee Jr Proposal Workflow
Chief/TPM interface for reviewing and approving Jr-initiated proposals

Usage:
    python3 proposal_workflow.py --list              # List pending proposals
    python3 proposal_workflow.py --approve <id>      # Approve proposal
    python3 proposal_workflow.py --reject <id> <reason>  # Reject proposal
    python3 proposal_workflow.py --auto              # Auto-process low-priority

For Seven Generations
"""

import os
import sys
import argparse
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import psycopg2
import psycopg2.extras


def get_connection():
    return psycopg2.connect(
        host=os.environ.get('CHEROKEE_SPOKE_HOST', '192.168.132.222'),
        database='triad_federation',
        user=os.environ.get('CHEROKEE_SPOKE_USER', 'claude'),
        password=os.environ.get('CHEROKEE_SPOKE_PASSWORD', '')
    )


def list_pending(conn):
    """List all pending proposals"""
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT * FROM jr_proposals_pending_review
        ORDER BY hours_pending DESC
    """)
    proposals = cur.fetchall()
    cur.close()
    
    if not proposals:
        print("No pending proposals.")
        return
    
    print(f"\n{'='*80}")
    print(f"PENDING JR PROPOSALS ({len(proposals)})")
    print(f"{'='*80}\n")
    
    for p in proposals:
        priority_color = {
            'critical': '\033[91m',  # Red
            'high': '\033[93m',      # Yellow
            'medium': '\033[94m',    # Blue
            'low': '\033[92m'        # Green
        }.get(p['proposal_priority'], '')
        reset = '\033[0m'
        
        print(f"ID: {str(p['proposal_id'])[:8]}...")
        print(f"Jr: {p['jr_name']}")
        print(f"Type: {p['proposal_type']} | Priority: {priority_color}{p['proposal_priority'].upper()}{reset}")
        print(f"Title: {p['proposal_title']}")
        print(f"Description: {p['proposal_description'][:200]}...")
        if p['trigger_summary']:
            print(f"Triggered by: {p['trigger_summary'][:100]}")
        print(f"Confidence: {p['confidence_score']:.1%} | Pending: {p['hours_pending']:.1f} hours")
        print(f"-" * 40)
    
    print(f"\nTo approve: python3 proposal_workflow.py --approve <id>")
    print(f"To reject:  python3 proposal_workflow.py --reject <id> 'reason'")


def approve_proposal(conn, proposal_id: str, reviewer: str = 'chief'):
    """Approve a proposal"""
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Get proposal
    cur.execute("""
        SELECT * FROM jr_action_proposals WHERE proposal_id::text LIKE %s
    """, (proposal_id + '%',))
    proposal = cur.fetchone()
    
    if not proposal:
        print(f"Proposal not found: {proposal_id}")
        return False
    
    if proposal['status'] != 'pending':
        print(f"Proposal is not pending (status: {proposal['status']})")
        return False
    
    # Update proposal
    cur.execute("""
        UPDATE jr_action_proposals
        SET status = 'approved',
            reviewed_by = %s,
            decided_at = NOW()
        WHERE proposal_id = %s
    """, (reviewer, proposal['proposal_id']))
    
    # Update Jr metrics
    cur.execute("""
        UPDATE jr_learning_metrics
        SET proposals_approved = COALESCE(proposals_approved, 0) + 1
        WHERE jr_name = %s
    """, (proposal['jr_name'],))
    
    # Post to thermal memory
    cur.execute("""
        INSERT INTO triad_shared_memories (content, temperature, source_triad, tags, node_id)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        f"PROPOSAL APPROVED\n\nJr: {proposal['jr_name']}\nTitle: {proposal['proposal_title']}\nApproved by: {reviewer}\n\nAction: {proposal['proposed_action']}\n\nFor Seven Generations.",
        75.0,
        reviewer,
        ['proposal_approved', proposal['jr_name'], proposal['proposal_type']],
        'redfin'
    ))
    
    conn.commit()
    cur.close()
    
    print(f"\n✅ APPROVED: {proposal['proposal_title']}")
    print(f"Jr {proposal['jr_name']} can now execute: {proposal['proposed_action']}")
    return True


def reject_proposal(conn, proposal_id: str, reason: str, reviewer: str = 'chief'):
    """Reject a proposal"""
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Get proposal
    cur.execute("""
        SELECT * FROM jr_action_proposals WHERE proposal_id::text LIKE %s
    """, (proposal_id + '%',))
    proposal = cur.fetchone()
    
    if not proposal:
        print(f"Proposal not found: {proposal_id}")
        return False
    
    if proposal['status'] != 'pending':
        print(f"Proposal is not pending (status: {proposal['status']})")
        return False
    
    # Update proposal
    cur.execute("""
        UPDATE jr_action_proposals
        SET status = 'rejected',
            reviewed_by = %s,
            review_notes = %s,
            decided_at = NOW()
        WHERE proposal_id = %s
    """, (reviewer, reason, proposal['proposal_id']))
    
    # Update Jr metrics
    cur.execute("""
        UPDATE jr_learning_metrics
        SET proposals_rejected = COALESCE(proposals_rejected, 0) + 1
        WHERE jr_name = %s
    """, (proposal['jr_name'],))
    
    conn.commit()
    cur.close()
    
    print(f"\n❌ REJECTED: {proposal['proposal_title']}")
    print(f"Reason: {reason}")
    return True


def auto_process(conn, reviewer: str = 'auto'):
    """Auto-approve low-risk, high-confidence proposals"""
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Find auto-approvable proposals
    cur.execute("""
        SELECT * FROM jr_action_proposals
        WHERE status = 'pending'
          AND proposal_priority IN ('low', 'info')
          AND confidence_score >= 0.8
          AND proposal_type IN ('suggest_improvement', 'learn')
    """)
    
    proposals = cur.fetchall()
    cur.close()
    
    if not proposals:
        print("No auto-approvable proposals.")
        return
    
    print(f"\nAuto-processing {len(proposals)} low-risk proposal(s)...\n")
    
    for p in proposals:
        approve_proposal(conn, str(p['proposal_id']), reviewer=reviewer)


def main():
    parser = argparse.ArgumentParser(description='Jr Proposal Workflow')
    parser.add_argument('--list', action='store_true', help='List pending proposals')
    parser.add_argument('--approve', type=str, help='Approve proposal by ID')
    parser.add_argument('--reject', type=str, nargs=2, metavar=('ID', 'REASON'), help='Reject proposal')
    parser.add_argument('--auto', action='store_true', help='Auto-process low-risk proposals')
    parser.add_argument('--reviewer', type=str, default='chief', help='Reviewer name')
    
    args = parser.parse_args()
    
    conn = get_connection()
    
    if args.approve:
        approve_proposal(conn, args.approve, args.reviewer)
    elif args.reject:
        reject_proposal(conn, args.reject[0], args.reject[1], args.reviewer)
    elif args.auto:
        auto_process(conn, args.reviewer)
    else:
        list_pending(conn)
    
    conn.close()


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Status Reporter for Jr Executor
Import this in jr_cli.py to enable status notifications
"""

import sys
sys.path.insert(0, '/ganuda/telegram_bot')

try:
    from status_notifier import write_jr_status
    STATUS_REPORTING_ENABLED = True
except ImportError:
    STATUS_REPORTING_ENABLED = False


def report_task_started(task_id: str, jr_name: str = 'it_triad_jr'):
    """Report task start to Telegram"""
    if STATUS_REPORTING_ENABLED:
        write_jr_status(task_id, 'started', f'Jr {jr_name} is processing task', jr_name)


def report_task_completed(task_id: str, details: str = None, jr_name: str = 'it_triad_jr'):
    """Report task completion to Telegram"""
    if STATUS_REPORTING_ENABLED:
        write_jr_status(task_id, 'completed', details or 'Task completed successfully', jr_name)


def report_task_failed(task_id: str, error: str, jr_name: str = 'it_triad_jr'):
    """Report task failure to Telegram"""
    if STATUS_REPORTING_ENABLED:
        write_jr_status(task_id, 'failed', f'Error: {error}', jr_name)


if __name__ == '__main__':
    print(f"Status reporting enabled: {STATUS_REPORTING_ENABLED}")
    if STATUS_REPORTING_ENABLED:
        print("Testing status report...")
        report_task_completed('TEST-REPORTER-001', 'Test from status_reporter module')
        print("Check thermal memory for the status update")
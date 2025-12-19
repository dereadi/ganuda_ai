#!/usr/bin/env python3
"""
Job Email Classifier for Cherokee AI Federation
"""

import re
from typing import Dict, Optional, Tuple

JOB_DOMAINS = {
    'indeed.com': 'Indeed', 'linkedin.com': 'LinkedIn', 'ziprecruiter.com': 'ZipRecruiter',
    'greenhouse.io': 'Greenhouse', 'greenhouse-mail.io': 'Greenhouse', 'lever.co': 'Lever',
    'myworkday.com': 'Workday', 'icims.com': 'iCIMS', 'jobvite.com': 'Jobvite',
    'smartrecruiters.com': 'SmartRecruiters', 'ashbyhq.com': 'Ashby', 'breezy.hr': 'Breezy'
}

OFFER_PATTERNS = [r'offer letter', r'job offer', r'pleased to offer', r'extend.{1,20}offer',
    r'compensation package', r'start date', r'base salary', r'we.{1,10}like to offer']
INTERVIEW_PATTERNS = [r'schedule.{1,20}interview', r'interview.{1,20}schedule', r'phone screen',
    r'video interview', r'technical interview', r'on-?site', r'meet.{1,20}team',
    r'availability.{1,20}call', r'calendar invite']
NEXT_STEPS_PATTERNS = [r'next step', r'moving forward with you', r'proceed.{1,20}application',
    r'advance.{1,20}process', r'shortlist', r'selected for']
REJECTION_PATTERNS = [r'not.{1,20}moving forward', r'other candidates', r'not.{1,20}selected',
    r'position.{1,20}filled', r'unfortunately', r'regret to inform', r'decided.{1,20}proceed.{1,20}other']
APPLICATION_PATTERNS = [r'application.{1,20}received', r'thank.{1,20}applying',
    r'application.{1,20}complete', r'successfully applied', r'we.{1,10}received.{1,20}application']
RECRUITER_PATTERNS = [r'opportunity.{1,20}interest', r'reaching out', r'your profile',
    r'your background', r'perfect fit', r'great match', r'came across.{1,20}profile']
EXCLUDE_PATTERNS = [r'limited time', r'special offer', r'discount', r'sale',
    r'credit.{1,10}(card|limit|offer)', r'unsubscribe', r'promotional']

def is_job_related(from_addr: str, subject: str) -> bool:
    from_lower = (from_addr or '').lower()
    subject_lower = (subject or '').lower()
    for domain in JOB_DOMAINS:
        if domain in from_lower:
            return True
    job_keywords = ['job', 'position', 'opportunity', 'application', 'interview', 'hiring', 'career', 'recruit']
    for keyword in job_keywords:
        if keyword in subject_lower:
            for exclude in EXCLUDE_PATTERNS:
                if re.search(exclude, subject_lower):
                    return False
            return True
    return False

def classify_job_email(from_addr: str, subject: str, body: str) -> Tuple[Optional[str], int]:
    text = ((subject or '') + ' ' + (body or '')[:1000]).lower()
    for pattern in EXCLUDE_PATTERNS:
        if re.search(pattern, text):
            return None, 5
    for pattern in OFFER_PATTERNS:
        if re.search(pattern, text):
            return 'offer', 1
    for pattern in INTERVIEW_PATTERNS:
        if re.search(pattern, text):
            return 'interview', 1
    for pattern in NEXT_STEPS_PATTERNS:
        if re.search(pattern, text):
            return 'next_steps', 2
    for pattern in REJECTION_PATTERNS:
        if re.search(pattern, text):
            return 'rejection', 4
    for pattern in APPLICATION_PATTERNS:
        if re.search(pattern, text):
            return 'application', 3
    for pattern in RECRUITER_PATTERNS:
        if re.search(pattern, text):
            return 'recruiter', 3
    return None, 5

def extract_company_position(from_addr: str, subject: str, body: str) -> Tuple[Optional[str], Optional[str]]:
    company, position = None, None
    patterns = [r'application[:\s]+(.+?)\s+at\s+(.+?)(?:\s|$)', r'Indeed Application[:\s]+(.+?)$']
    for pattern in patterns:
        match = re.search(pattern, subject or '', re.IGNORECASE)
        if match:
            groups = match.groups()
            if len(groups) >= 2:
                position, company = groups[0].strip()[:100], groups[1].strip()[:100]
            elif len(groups) == 1:
                position = groups[0].strip()[:100]
            break
    if not company:
        for domain, name in JOB_DOMAINS.items():
            if domain in (from_addr or '').lower():
                company = name
                break
    return company, position

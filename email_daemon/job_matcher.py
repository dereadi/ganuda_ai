#!/usr/bin/env python3
"""
Job Matching Algorithm for Cherokee AI Federation
Scores jobs against Darrell Reading's profile - Full career trajectory
From remote help desk through Senior Infrastructure to Multi-Agent Architect
"""
from typing import Dict, Tuple

# Full career profile based on resume
USER_PROFILE = {
    # Roles across the career ladder - entry to senior
    "target_roles": [
        # Current/Senior Level
        "Multi-Agent", "AI/ML Engineer", "AI Engineer", "ML Engineer",
        "Principal Engineer", "Staff Engineer", "Senior Engineer",
        "Technical Program Manager", "TPM", "Senior TPM", "Staff TPM",
        "Platform Engineer", "Infrastructure Architect", "Solutions Architect",
        "DevOps Engineer", "SRE", "Site Reliability",
        # Mid Level
        "Systems Engineer", "System Engineer", "Sr. Systems Engineer",
        "Infrastructure Engineer", "Linux Engineer", "Unix Engineer",
        "Database Administrator", "DBA", "Oracle DBA", "PostgreSQL",
        "Network Engineer", "Security Engineer",
        "ITSM", "Remedy", "ServiceNow",
        "Jamf", "Apple", "macOS", "Mac Admin",
        # Entry/Remote accessible
        "Help Desk", "Helpdesk", "Service Desk", "Support Engineer",
        "Technical Support", "IT Support", "Desktop Support",
        "System Administrator", "Sysadmin", "IT Administrator",
        "IT Technician", "Support Technician", "Field Technician",
    ],
    
    # Skills from resume
    "skills": [
        # AI/ML
        "AI", "ML", "Machine Learning", "LLM", "Large Language Model",
        "PyTorch", "Transformers", "CUDA", "vLLM", "Hugging Face",
        "Multi-Agent", "Orchestration",
        # Infrastructure
        "Linux", "RHEL", "Ubuntu", "Unix", "macOS", "Apple",
        "Docker", "Podman", "Kubernetes", "Containers",
        # Database
        "PostgreSQL", "Oracle", "SQL", "Database", "DBA",
        # Observability
        "Grafana", "Prometheus", "Loki", "Monitoring", "Observability",
        # Security
        "Security", "RBAC", "Air-gapped", "VPN", "Tailscale", "WireGuard",
        "Cyber Security", "Cybersecurity",
        # ITSM
        "Remedy", "ServiceNow", "ITSM", "Jira", "Confluence",
        "Jamf", "MDM", "Ansible",
        # Languages
        "Python", "Bash", "SQL", "C++", "JavaScript",
        # General
        "Distributed Systems", "Microservices", "API",
        "Cloud", "AWS", "GCP", "Azure",
        "Agile", "Scrum",
    ],
    
    # Companies of interest (bonus points)
    "preferred_companies": [
        "Anthropic", "OpenAI", "Google", "Meta", "Microsoft",
        "Amazon", "Apple", "NVIDIA", "Netflix", "Walmart",
        "IBM", "Oracle", "VMware", "Red Hat", "Canonical",
    ],
    
    # Location preferences
    "locations": [
        "remote", "Remote", "REMOTE", "work from home", "WFH",
        "hybrid", "Hybrid",
        "Bentonville", "Arkansas", "AR",
        "Fayetteville", "Rogers", "Springdale",  # NWA
    ],
    
    # Negative signals - reduce score
    "exclusions": [
        "internship", "intern", "entry level", "junior",  # Too junior
        "clearance required", "TS/SCI", "Secret clearance",  # Can't get clearance
        "on-site only", "no remote",  # Must be remote/hybrid
    ],
    
    # Strong negative - likely skip
    "hard_exclusions": [
        "H1B", "visa sponsorship", "US citizens only",  # Not applicable
    ]
}


def score_job(job: Dict) -> Tuple[float, str]:
    """
    Score a job opportunity against user profile.
    Returns (score 0.0-1.0, reasoning string)
    """
    score = 0.0
    max_score = 100.0
    reasons = []

    title = job.get('title', '') or job.get('subject', '') or ''
    body = job.get('body', '') or job.get('body_text', '') or ''
    company = job.get('company', '') or job.get('job_company', '') or ''
    
    title_lower = title.lower()
    body_lower = body.lower()
    company_lower = company.lower()
    combined = f"{title_lower} {body_lower}"

    # Hard exclusions - immediate disqualify
    for excl in USER_PROFILE['hard_exclusions']:
        if excl.lower() in combined:
            return 0.0, f"Hard exclusion: {excl}"

    # Role match (40 points max)
    role_matched = False
    for role in USER_PROFILE['target_roles']:
        if role.lower() in title_lower:
            score += 40
            reasons.append(f"Role: {role}")
            role_matched = True
            break
    
    if not role_matched:
        # Check body for role mentions
        for role in USER_PROFILE['target_roles'][:15]:  # Check senior roles in body
            if role.lower() in body_lower:
                score += 20
                reasons.append(f"Role in desc: {role}")
                break

    # Skills match (30 points max, 2 pts per skill up to 15 skills)
    skill_matches = []
    for skill in USER_PROFILE['skills']:
        if skill.lower() in combined:
            skill_matches.append(skill)
    skill_score = min(30, len(skill_matches) * 2)
    score += skill_score
    if skill_matches:
        reasons.append(f"Skills({len(skill_matches)}): {', '.join(skill_matches[:5])}")

    # Location match (15 points)
    for loc in USER_PROFILE['locations']:
        if loc.lower() in combined:
            score += 15
            reasons.append(f"Location: {loc}")
            break

    # Company preference (10 points bonus)
    for preferred in USER_PROFILE['preferred_companies']:
        if preferred.lower() in company_lower:
            score += 10
            reasons.append(f"Preferred company: {preferred}")
            break

    # Soft exclusions (negative points)
    for excl in USER_PROFILE['exclusions']:
        if excl.lower() in combined:
            score -= 15
            reasons.append(f"Exclusion: {excl}")

    # Normalize to 0-1
    final_score = max(0.0, min(1.0, score / max_score))
    reasoning = "; ".join(reasons) if reasons else "No strong matches"
    
    return round(final_score, 2), reasoning


def categorize_job(score: float) -> str:
    """Categorize job based on match score."""
    if score >= 0.60:
        return "high_match"
    elif score >= 0.35:
        return "medium_match"
    else:
        return "low_match"


def should_alert(score: float, classification: str) -> bool:
    """Determine if job should trigger an alert."""
    # Always alert for interviews/offers
    if classification in ('interview', 'offer', 'next_steps'):
        return True
    # Alert for high/medium match recruiter outreach
    if classification == 'recruiter' and score >= 0.35:
        return True
    # Alert for high match applications
    if classification == 'application' and score >= 0.60:
        return True
    return False

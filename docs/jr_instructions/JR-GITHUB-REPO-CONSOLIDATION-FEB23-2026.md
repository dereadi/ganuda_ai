# Jr Instruction: GitHub Repo Consolidation Audit Script

**Kanban**: #1854
**Priority**: 4
**Story Points**: 5
**use_rlm**: false
**assigned_jr**: Software Engineer Jr.

---

## Overview

Create a Python script that audits all GitHub repositories in the organization, categorizes them by activity and completeness, and outputs a CSV report. This is a read-only audit tool -- it does NOT auto-archive or modify any repos. The report flags candidates for archival and cleanup.

---

## Steps

### Step 1: Create the audit script

Create `/ganuda/scripts/github_repo_audit.py`

```python
#!/usr/bin/env python3
"""
GitHub Repository Audit Script
Kanban #1854 - Cherokee AI Federation

Lists all repos in the org, categorizes by activity/completeness,
and outputs a CSV report with archive and cleanup candidates.

Usage:
    GITHUB_TOKEN=ghp_xxx python3 /ganuda/scripts/github_repo_audit.py --org ORG_NAME

Requires: pip install PyGithub
"""

import argparse
import csv
import os
import sys
from datetime import datetime, timezone, timedelta

try:
    from github import Github, GithubException
except ImportError:
    print("ERROR: PyGithub not installed. Run: pip install PyGithub")
    sys.exit(1)


REPORT_PATH = "/ganuda/reports/github-repo-audit.csv"
ARCHIVE_THRESHOLD_DAYS = 90


def get_github_client():
    """Create authenticated GitHub client from environment."""
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("ERROR: GITHUB_TOKEN environment variable not set")
        sys.exit(1)
    return Github(token)


def get_last_commit_date(repo):
    """Get the date of the most recent commit on the default branch."""
    try:
        commits = repo.get_commits()
        if commits.totalCount > 0:
            return commits[0].commit.committer.date.replace(tzinfo=timezone.utc)
    except GithubException:
        pass
    return None


def has_readme(repo):
    """Check if repo has a README file."""
    try:
        repo.get_readme()
        return True
    except GithubException:
        return False


def audit_repos(org_name):
    """Audit all repos in the organization and return structured data."""
    gh = get_github_client()
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=ARCHIVE_THRESHOLD_DAYS)

    try:
        org = gh.get_organization(org_name)
    except GithubException as e:
        print(f"ERROR: Could not access org '{org_name}': {e}")
        sys.exit(1)

    results = []
    repos = org.get_repos(type="all")
    total = repos.totalCount
    print(f"Auditing {total} repositories in '{org_name}'...")

    for i, repo in enumerate(repos, 1):
        print(f"  [{i}/{total}] {repo.name}")

        last_commit = get_last_commit_date(repo)
        days_since_commit = (now - last_commit).days if last_commit else None
        readme_exists = has_readme(repo)

        flags = []
        if last_commit and last_commit < cutoff:
            flags.append("archive-candidate")
        if last_commit is None:
            flags.append("no-commits")
        if not repo.description:
            flags.append("needs-cleanup")
        if not readme_exists:
            flags.append("needs-cleanup")

        results.append({
            "name": repo.name,
            "full_name": repo.full_name,
            "description": repo.description or "",
            "is_archived": repo.archived,
            "is_private": repo.private,
            "default_branch": repo.default_branch,
            "stars": repo.stargazers_count,
            "forks": repo.forks_count,
            "last_commit_date": last_commit.isoformat() if last_commit else "N/A",
            "days_since_commit": days_since_commit if days_since_commit is not None else "N/A",
            "has_description": bool(repo.description),
            "has_readme": readme_exists,
            "created_at": repo.created_at.isoformat(),
            "language": repo.language or "N/A",
            "flags": "; ".join(flags) if flags else "ok",
        })

    return results


def write_csv(results):
    """Write audit results to CSV report."""
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)

    fieldnames = [
        "name", "full_name", "description", "is_archived", "is_private",
        "default_branch", "stars", "forks", "last_commit_date",
        "days_since_commit", "has_description", "has_readme",
        "created_at", "language", "flags",
    ]

    with open(REPORT_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\nReport written to {REPORT_PATH}")


def print_summary(results):
    """Print a summary of the audit findings."""
    total = len(results)
    archived = sum(1 for r in results if r["is_archived"])
    archive_candidates = sum(1 for r in results if "archive-candidate" in r["flags"])
    needs_cleanup = sum(1 for r in results if "needs-cleanup" in r["flags"])
    no_commits = sum(1 for r in results if "no-commits" in r["flags"])

    print(f"\n--- Audit Summary ---")
    print(f"Total repos:         {total}")
    print(f"Already archived:    {archived}")
    print(f"Archive candidates:  {archive_candidates} (no commits in {ARCHIVE_THRESHOLD_DAYS}+ days)")
    print(f"Needs cleanup:       {needs_cleanup} (missing description or README)")
    print(f"No commits found:    {no_commits}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GitHub Repository Audit")
    parser.add_argument("--org", required=True, help="GitHub organization name")
    args = parser.parse_args()

    results = audit_repos(args.org)
    write_csv(results)
    print_summary(results)
```

---

## Verification

1. Confirm file exists at `/ganuda/scripts/github_repo_audit.py`
2. Validate syntax: `python3 -c "import ast; ast.parse(open('/ganuda/scripts/github_repo_audit.py').read())"`
3. Confirm script does NOT contain any auto-archive, delete, or modify operations
4. Confirm CSV output path is `/ganuda/reports/github-repo-audit.csv`
5. Confirm script requires GITHUB_TOKEN env var and --org argument

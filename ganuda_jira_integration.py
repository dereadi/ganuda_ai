#!/usr/bin/env python3
"""
🔥 Ganuda Jira Integration Module
Cherokee Mind integration with Atlassian Jira for SAG Resource AI

Provides intelligent interface between Ganuda brain and Jira instances
Supports: Project management, issue tracking, time management, worklog analysis
"""

import os
import json
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from atlassian import Jira
from dataclasses import dataclass, asdict


@dataclass
class JiraConfig:
    """Configuration for Jira connection"""
    url: str
    username: str
    api_token: str
    cloud: bool = True
    project_key: Optional[str] = None


@dataclass
class JiraIssue:
    """Simplified Jira issue representation"""
    key: str
    summary: str
    status: str
    assignee: Optional[str]
    priority: str
    issue_type: str
    created: str
    updated: str
    description: Optional[str] = None
    time_spent: Optional[int] = None  # seconds
    time_estimate: Optional[int] = None  # seconds

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class JiraWorklog:
    """Time tracking worklog entry"""
    issue_key: str
    author: str
    time_spent: int  # seconds
    started: str
    comment: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


class GanudaJiraConnector:
    """
    Cherokee Mind Jira Integration
    Provides tribal intelligence for Jira operations
    """

    def __init__(self, config: JiraConfig):
        """Initialize Jira connector with configuration"""
        self.config = config
        self.jira = Jira(
            url=config.url,
            username=config.username,
            password=config.api_token,
            cloud=config.cloud
        )
        self.project_key = config.project_key

        print(f"🔥 Ganuda Jira Connector initialized")
        print(f"   URL: {config.url}")
        print(f"   Project: {config.project_key or 'All projects'}")

    # ==================== PROJECT OPERATIONS ====================

    def get_all_projects(self) -> List[Dict[str, Any]]:
        """Get all accessible projects"""
        try:
            projects = self.jira.projects(included_archived=False)
            return [
                {
                    'key': p['key'],
                    'name': p['name'],
                    'id': p['id'],
                    'type': p.get('projectTypeKey', 'unknown')
                }
                for p in projects
            ]
        except Exception as e:
            print(f"❌ Error fetching projects: {e}")
            return []

    def get_project_info(self, project_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get detailed project information"""
        key = project_key or self.project_key
        if not key:
            print("❌ No project key specified")
            return None

        try:
            project = self.jira.project(key)
            return {
                'key': project['key'],
                'name': project['name'],
                'description': project.get('description', ''),
                'lead': project.get('lead', {}).get('displayName', 'Unknown'),
                'issue_types': [it['name'] for it in project.get('issueTypes', [])]
            }
        except Exception as e:
            print(f"❌ Error fetching project {key}: {e}")
            return None

    # ==================== ISSUE OPERATIONS ====================

    def search_issues(self, jql: str, max_results: int = 50) -> List[JiraIssue]:
        """
        Search issues using JQL (Jira Query Language)

        Common JQL examples:
        - 'project = SAG AND status = "In Progress"'
        - 'assignee = currentUser() AND status != Done'
        - 'created >= -7d ORDER BY created DESC'
        """
        try:
            results = self.jira.jql(jql, limit=max_results)
            issues = []

            for item in results.get('issues', []):
                fields = item['fields']

                issues.append(JiraIssue(
                    key=item['key'],
                    summary=fields.get('summary', 'No summary'),
                    status=fields.get('status', {}).get('name', 'Unknown'),
                    assignee=fields.get('assignee', {}).get('displayName') if fields.get('assignee') else None,
                    priority=fields.get('priority', {}).get('name', 'None'),
                    issue_type=fields.get('issuetype', {}).get('name', 'Unknown'),
                    created=fields.get('created', ''),
                    updated=fields.get('updated', ''),
                    description=fields.get('description', ''),
                    time_spent=fields.get('timespent'),
                    time_estimate=fields.get('timeestimate')
                ))

            print(f"✅ Found {len(issues)} issues")
            return issues

        except Exception as e:
            print(f"❌ Error searching issues: {e}")
            return []

    def get_issue(self, issue_key: str) -> Optional[JiraIssue]:
        """Get single issue by key"""
        try:
            item = self.jira.issue(issue_key)
            fields = item['fields']

            return JiraIssue(
                key=item['key'],
                summary=fields.get('summary', 'No summary'),
                status=fields.get('status', {}).get('name', 'Unknown'),
                assignee=fields.get('assignee', {}).get('displayName') if fields.get('assignee') else None,
                priority=fields.get('priority', {}).get('name', 'None'),
                issue_type=fields.get('issuetype', {}).get('name', 'Unknown'),
                created=fields.get('created', ''),
                updated=fields.get('updated', ''),
                description=fields.get('description', ''),
                time_spent=fields.get('timespent'),
                time_estimate=fields.get('timeestimate')
            )
        except Exception as e:
            print(f"❌ Error fetching issue {issue_key}: {e}")
            return None

    def get_project_issues(self, project_key: Optional[str] = None,
                          status: Optional[str] = None,
                          max_results: int = 50) -> List[JiraIssue]:
        """Get issues for a specific project"""
        key = project_key or self.project_key
        if not key:
            print("❌ No project key specified")
            return []

        jql = f'project = {key}'
        if status:
            jql += f' AND status = "{status}"'
        jql += ' ORDER BY created DESC'

        return self.search_issues(jql, max_results)

    # ==================== WORKLOG OPERATIONS ====================

    def get_issue_worklogs(self, issue_key: str) -> List[JiraWorklog]:
        """Get time tracking worklogs for an issue"""
        try:
            worklogs = self.jira.issue_worklog(issue_key)
            entries = []

            for wl in worklogs.get('worklogs', []):
                entries.append(JiraWorklog(
                    issue_key=issue_key,
                    author=wl.get('author', {}).get('displayName', 'Unknown'),
                    time_spent=wl.get('timeSpentSeconds', 0),
                    started=wl.get('started', ''),
                    comment=wl.get('comment', '')
                ))

            return entries
        except Exception as e:
            print(f"❌ Error fetching worklogs for {issue_key}: {e}")
            return []

    def get_user_time_spent(self, username: str, days_back: int = 7) -> Dict[str, Any]:
        """Get total time logged by user in recent days"""
        date_from = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        jql = f'worklogAuthor = "{username}" AND worklogDate >= "{date_from}"'

        try:
            issues = self.search_issues(jql, max_results=100)
            total_seconds = sum(issue.time_spent or 0 for issue in issues)

            return {
                'username': username,
                'days_back': days_back,
                'total_seconds': total_seconds,
                'total_hours': round(total_seconds / 3600, 2),
                'issues_worked': len(issues),
                'issues': [issue.to_dict() for issue in issues]
            }
        except Exception as e:
            print(f"❌ Error getting time spent for {username}: {e}")
            return {'username': username, 'error': str(e)}

    # ==================== GANUDA INTELLIGENCE ====================

    def get_tribal_summary(self, project_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Get Cherokee Mind summary of project health
        Tribal intelligence analysis of Jira state
        """
        key = project_key or self.project_key
        if not key:
            return {'error': 'No project key specified'}

        try:
            # Get all issues
            all_issues = self.get_project_issues(key, max_results=200)

            # Status breakdown
            status_counts = {}
            for issue in all_issues:
                status_counts[issue.status] = status_counts.get(issue.status, 0) + 1

            # Priority breakdown
            priority_counts = {}
            for issue in all_issues:
                priority_counts[issue.priority] = priority_counts.get(issue.priority, 0) + 1

            # Assignee workload
            assignee_counts = {}
            for issue in all_issues:
                assignee = issue.assignee or 'Unassigned'
                assignee_counts[assignee] = assignee_counts.get(assignee, 0) + 1

            # Time tracking analysis
            total_estimated = sum(issue.time_estimate or 0 for issue in all_issues)
            total_spent = sum(issue.time_spent or 0 for issue in all_issues)

            # Tribal harmony assessment (0-100%)
            completion_rate = (status_counts.get('Done', 0) / len(all_issues) * 100) if all_issues else 0
            unassigned_rate = (assignee_counts.get('Unassigned', 0) / len(all_issues) * 100) if all_issues else 0

            # Cherokee wisdom: Balance assessment
            tribal_harmony = max(0, 100 - unassigned_rate)  # High unassigned = low harmony

            return {
                'project_key': key,
                'total_issues': len(all_issues),
                'status_breakdown': status_counts,
                'priority_breakdown': priority_counts,
                'assignee_workload': assignee_counts,
                'time_tracking': {
                    'total_estimated_hours': round(total_estimated / 3600, 2),
                    'total_spent_hours': round(total_spent / 3600, 2),
                    'efficiency': round((total_spent / total_estimated * 100), 1) if total_estimated > 0 else 0
                },
                'tribal_metrics': {
                    'harmony_score': round(tribal_harmony, 1),
                    'completion_rate': round(completion_rate, 1),
                    'unassigned_rate': round(unassigned_rate, 1)
                },
                'sacred_fire_status': '🔥 Burning strong' if tribal_harmony > 70 else '🌿 Needs tending'
            }
        except Exception as e:
            print(f"❌ Error generating tribal summary: {e}")
            return {'error': str(e)}

    def get_productive_integration_data(self, project_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Get data specifically formatted for Productive tool integration
        Focus: HR scheduling, time tracking, resource planning
        """
        key = project_key or self.project_key
        if not key:
            return {'error': 'No project key specified'}

        try:
            # Get active issues
            active_issues = self.search_issues(
                f'project = {key} AND status IN ("In Progress", "To Do")',
                max_results=100
            )

            # Resource allocation by assignee
            resources = {}
            for issue in active_issues:
                assignee = issue.assignee or 'Unassigned'
                if assignee not in resources:
                    resources[assignee] = {
                        'name': assignee,
                        'assigned_tasks': 0,
                        'total_estimated_hours': 0,
                        'total_spent_hours': 0,
                        'tasks': []
                    }

                resources[assignee]['assigned_tasks'] += 1
                resources[assignee]['total_estimated_hours'] += (issue.time_estimate or 0) / 3600
                resources[assignee]['total_spent_hours'] += (issue.time_spent or 0) / 3600
                resources[assignee]['tasks'].append({
                    'key': issue.key,
                    'summary': issue.summary,
                    'priority': issue.priority,
                    'estimated_hours': round((issue.time_estimate or 0) / 3600, 2)
                })

            return {
                'project_key': key,
                'resource_allocation': resources,
                'total_active_tasks': len(active_issues),
                'unassigned_tasks': len([i for i in active_issues if not i.assignee]),
                'productive_export_ready': True
            }
        except Exception as e:
            print(f"❌ Error generating Productive integration data: {e}")
            return {'error': str(e)}


# ==================== EXAMPLE USAGE ====================

def demo_sag_integration():
    """Demo: How SAG would use Ganuda Jira integration"""

    # Configuration (normally from environment or config file)
    config = JiraConfig(
        url=os.getenv('JIRA_URL', 'https://your-domain.atlassian.net'),
        username=os.getenv('JIRA_USERNAME', 'email@example.com'),
        api_token=os.getenv('JIRA_API_TOKEN', 'your-api-token-here'),
        project_key='SAG'  # SAG Resource AI project
    )

    # Initialize Ganuda Jira connector
    ganuda = GanudaJiraConnector(config)

    # Example 1: Get tribal summary
    print("\n🔥 Tribal Summary:")
    summary = ganuda.get_tribal_summary()
    print(json.dumps(summary, indent=2))

    # Example 2: Search for in-progress tasks
    print("\n🔥 In-Progress Tasks:")
    in_progress = ganuda.search_issues('project = SAG AND status = "In Progress"')
    for issue in in_progress:
        print(f"  {issue.key}: {issue.summary} ({issue.assignee})")

    # Example 3: Get Productive tool integration data
    print("\n🔥 Productive Integration Data:")
    productive_data = ganuda.get_productive_integration_data()
    print(json.dumps(productive_data, indent=2))

    # Example 4: Get user time tracking
    print("\n🔥 User Time Tracking:")
    time_data = ganuda.get_user_time_spent('russell@sag.com', days_back=7)
    print(json.dumps(time_data, indent=2))


if __name__ == '__main__':
    print("🔥🌿 Ganuda Jira Integration Module")
    print("=" * 60)
    print("Cherokee Mind intelligence for Atlassian Jira")
    print("Built for SAG Resource AI")
    print("=" * 60)

    # Uncomment to run demo (requires valid Jira credentials)
    # demo_sag_integration()

    print("\n✅ Module loaded successfully")
    print("📚 Import with: from ganuda_jira_integration import GanudaJiraConnector, JiraConfig")

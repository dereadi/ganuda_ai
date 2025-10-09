#!/usr/bin/env python3
"""
🎬 SAG Resource AI - Jira Connector
Specific implementation for Russell's SAG team

This module provides SAG-specific Jira integration with Ganuda brain
Ready for deployment on Russell's laptop or cloud instance
"""

import os
import sys
import json
from pathlib import Path
from ganuda_jira_integration import GanudaJiraConnector, JiraConfig


class SAGJiraConnector:
    """SAG-specific Jira connector with preset workflows"""

    def __init__(self, config_file: str = None):
        """
        Initialize SAG Jira connector

        Configuration can come from:
        1. config_file (JSON)
        2. Environment variables
        3. Interactive prompt
        """

        # Load configuration
        config = self._load_config(config_file)

        # Initialize Ganuda connector
        self.ganuda = GanudaJiraConnector(config)
        self.project_key = config.project_key

        print("✅ SAG Jira Connector initialized")

    def _load_config(self, config_file: str = None) -> JiraConfig:
        """Load configuration from file or environment"""

        # Try config file first
        if config_file and Path(config_file).exists():
            with open(config_file, 'r') as f:
                data = json.load(f)
                return JiraConfig(**data)

        # Try environment variables
        url = os.getenv('SAG_JIRA_URL')
        username = os.getenv('SAG_JIRA_USERNAME')
        api_token = os.getenv('SAG_JIRA_API_TOKEN')
        project_key = os.getenv('SAG_JIRA_PROJECT', 'SAG')

        if url and username and api_token:
            return JiraConfig(
                url=url,
                username=username,
                api_token=api_token,
                project_key=project_key,
                cloud=True
            )

        # Interactive prompt (for initial setup)
        print("\n🔥 SAG Jira Configuration Setup")
        print("=" * 60)

        url = input("Jira URL (e.g., https://sag.atlassian.net): ").strip()
        username = input("Jira Username (email): ").strip()
        api_token = input("API Token (from id.atlassian.com): ").strip()
        project_key = input("Project Key [SAG]: ").strip() or "SAG"

        config = JiraConfig(
            url=url,
            username=username,
            api_token=api_token,
            project_key=project_key,
            cloud=True
        )

        # Offer to save config
        save = input("\nSave configuration to file? (y/n): ").strip().lower()
        if save == 'y':
            config_path = Path.home() / '.sag_jira_config.json'
            with open(config_path, 'w') as f:
                json.dump({
                    'url': config.url,
                    'username': config.username,
                    'api_token': config.api_token,
                    'project_key': config.project_key,
                    'cloud': config.cloud
                }, f, indent=2)
            print(f"✅ Configuration saved to {config_path}")
            print("⚠️  Keep this file secure! Contains API token.")

        return config

    # ==================== SAG-SPECIFIC WORKFLOWS ====================

    def get_daily_standup_report(self) -> dict:
        """
        Generate daily standup report for SAG team
        What's done, what's in progress, what's blocked
        """
        print("\n🔥 Generating SAG Daily Standup Report...")

        # Done yesterday (last 24 hours)
        done_yesterday = self.ganuda.search_issues(
            f'project = {self.project_key} AND status changed to Done during (-1d, now())',
            max_results=20
        )

        # In progress today
        in_progress = self.ganuda.search_issues(
            f'project = {self.project_key} AND status = "In Progress"',
            max_results=20
        )

        # Blocked items
        blocked = self.ganuda.search_issues(
            f'project = {self.project_key} AND status = Blocked',
            max_results=20
        )

        return {
            'date': Path(__file__).stem,
            'completed_yesterday': [{'key': i.key, 'summary': i.summary, 'assignee': i.assignee}
                                   for i in done_yesterday],
            'in_progress_today': [{'key': i.key, 'summary': i.summary, 'assignee': i.assignee}
                                 for i in in_progress],
            'blocked': [{'key': i.key, 'summary': i.summary, 'assignee': i.assignee, 'priority': i.priority}
                       for i in blocked],
            'team_velocity': len(done_yesterday),
            'active_tasks': len(in_progress)
        }

    def get_productive_sync_data(self) -> dict:
        """
        Get data ready for Productive tool sync
        Focus on HR scheduling and resource planning
        """
        print("\n🔥 Generating Productive Tool Sync Data...")
        return self.ganuda.get_productive_integration_data(self.project_key)

    def get_russell_dashboard(self) -> dict:
        """
        Russell's personalized dashboard
        High-level overview for project manager
        """
        print("\n🔥 Generating Russell's Dashboard...")

        # Tribal summary
        tribal = self.ganuda.get_tribal_summary(self.project_key)

        # Critical items
        critical = self.ganuda.search_issues(
            f'project = {self.project_key} AND priority = Highest ORDER BY created DESC',
            max_results=10
        )

        # Overdue items
        overdue = self.ganuda.search_issues(
            f'project = {self.project_key} AND due < now() AND status != Done',
            max_results=10
        )

        return {
            'tribal_summary': tribal,
            'critical_items': [{'key': i.key, 'summary': i.summary, 'assignee': i.assignee}
                              for i in critical],
            'overdue_items': [{'key': i.key, 'summary': i.summary, 'assignee': i.assignee}
                             for i in overdue],
            'health_score': tribal.get('tribal_metrics', {}).get('harmony_score', 0),
            'sacred_fire_status': tribal.get('sacred_fire_status', '🌿')
        }

    def get_team_workload(self) -> dict:
        """
        Team workload analysis
        Who's overloaded, who's available
        """
        print("\n🔥 Analyzing Team Workload...")

        productive_data = self.ganuda.get_productive_integration_data(self.project_key)
        resources = productive_data.get('resource_allocation', {})

        # Categorize by workload
        overloaded = []
        balanced = []
        available = []

        for assignee, data in resources.items():
            if assignee == 'Unassigned':
                continue

            task_count = data['assigned_tasks']
            estimated_hours = data['total_estimated_hours']

            if task_count > 10 or estimated_hours > 40:
                overloaded.append({'name': assignee, 'tasks': task_count, 'hours': estimated_hours})
            elif task_count > 3:
                balanced.append({'name': assignee, 'tasks': task_count, 'hours': estimated_hours})
            else:
                available.append({'name': assignee, 'tasks': task_count, 'hours': estimated_hours})

        return {
            'overloaded': overloaded,
            'balanced': balanced,
            'available': available,
            'unassigned_tasks': productive_data.get('unassigned_tasks', 0),
            'recommendation': '🔥 Redistribute tasks from overloaded team members' if overloaded else '✅ Team workload balanced'
        }


def main():
    """SAG Jira Connector CLI"""

    print("🎬 SAG Resource AI - Jira Connector")
    print("=" * 60)

    # Check for config file
    config_file = Path.home() / '.sag_jira_config.json'

    # Initialize connector
    sag = SAGJiraConnector(str(config_file) if config_file.exists() else None)

    # Interactive menu
    while True:
        print("\n🔥 SAG Jira Menu:")
        print("1. Daily Standup Report")
        print("2. Russell's Dashboard")
        print("3. Team Workload Analysis")
        print("4. Productive Tool Sync Data")
        print("5. Tribal Summary")
        print("6. Search Issues (JQL)")
        print("0. Exit")

        choice = input("\nSelect option: ").strip()

        if choice == '1':
            report = sag.get_daily_standup_report()
            print(json.dumps(report, indent=2))

        elif choice == '2':
            dashboard = sag.get_russell_dashboard()
            print(json.dumps(dashboard, indent=2))

        elif choice == '3':
            workload = sag.get_team_workload()
            print(json.dumps(workload, indent=2))

        elif choice == '4':
            sync_data = sag.get_productive_sync_data()
            print(json.dumps(sync_data, indent=2))

        elif choice == '5':
            summary = sag.ganuda.get_tribal_summary(sag.project_key)
            print(json.dumps(summary, indent=2))

        elif choice == '6':
            jql = input("Enter JQL query: ").strip()
            results = sag.ganuda.search_issues(jql)
            for issue in results:
                print(f"  {issue.key}: {issue.summary} [{issue.status}] ({issue.assignee})")

        elif choice == '0':
            print("🔥 Ganuda says goodbye!")
            break

        else:
            print("❌ Invalid option")


if __name__ == '__main__':
    main()

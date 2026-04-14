import json
from typing import List, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict

class SubscriptionAggregator:
    def __init__(self, email: str, scan_date: str, subscriptions: List[Dict[str, Any]]):
        self.email = email
        self.scan_date = scan_date
        self.subscriptions = subscriptions

    def group_by_service(self) -> Dict[str, List[Dict[str, Any]]]:
        grouped_subscriptions = defaultdict(list)
        for subscription in self.subscriptions:
            if subscription['is_subscription']:
                grouped_subscriptions[subscription['service_name']].append(subscription)
        return grouped_subscriptions

    def calculate_totals(self, grouped_subscriptions: Dict[str, List[Dict[str, Any]]]) -> Dict[str, float]:
        total_monthly = 0.0
        total_annual = 0.0
        for service, subs in grouped_subscriptions.items():
            for sub in subs:
                amount = sub['amount']
                frequency = sub['frequency']
                if frequency == 'monthly':
                    total_monthly += amount
                    total_annual += amount * 12
                elif frequency == 'annual':
                    total_monthly += amount / 12
                    total_annual += amount
                # Add more frequencies as needed
        return {'total_monthly': total_monthly, 'total_annual': total_annual}

    def identify_ghost_subscriptions(self, grouped_subscriptions: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        today = datetime.strptime(self.scan_date, '%Y-%m-%d')
        ghost_subscriptions = []
        for service, subs in grouped_subscriptions.items():
            latest_non_billing_email = None
            for sub in subs:
                if sub.get('last_non_billing_email'):
                    email_date = datetime.strptime(sub['last_non_billing_email'], '%Y-%m-%d')
                    if latest_non_billing_email is None or email_date > latest_non_billing_email:
                        latest_non_billing_email = email_date
            if latest_non_billing_email is None or (today - latest_non_billing_email).days > 30:
                for sub in subs:
                    sub['is_ghost'] = True
                    ghost_subscriptions.append(sub)
        return ghost_subscriptions

    def generate_output(self) -> Dict[str, Any]:
        grouped_subscriptions = self.group_by_service()
        totals = self.calculate_totals(grouped_subscriptions)
        ghost_subscriptions = self.identify_ghost_subscriptions(grouped_subscriptions)
        subscriptions = []
        for service, subs in grouped_subscriptions.items():
            for sub in subs:
                sub['last_non_billing_email'] = sub.get('last_non_billing_email', '')
                subscriptions.append(sub)
        subscriptions.sort(key=lambda x: (x['amount'], x['is_ghost']), reverse=True)
        potential_savings = sum(sub['amount'] for sub in ghost_subscriptions)
        return {
            "scan_date": self.scan_date,
            "email": self.email,
            "total_monthly": totals['total_monthly'],
            "total_annual": totals['total_annual'],
            "subscription_count": len(subscriptions),
            "ghost_count": len(ghost_subscriptions),
            "potential_savings": potential_savings,
            "subscriptions": subscriptions
        }

def aggregate_subscriptions(email: str, scan_date: str, subscriptions: List[Dict[str, Any]]) -> Dict[str, Any]:
    aggregator = SubscriptionAggregator(email, scan_date, subscriptions)
    return aggregator.generate_output()

if __name__ == "__main__":
    # Example usage
    sample_subscriptions = [
        {
            "is_subscription": True,
            "service_name": "Netflix",
            "amount": 15.99,
            "currency": "USD",
            "frequency": "monthly",
            "charge_date": "2026-03-15",
            "category": "entertainment",
            "confidence": 0.95,
            "last_non_billing_email": "2026-03-20"
        },
        {
            "is_subscription": True,
            "service_name": "Spotify",
            "amount": 9.99,
            "currency": "USD",
            "frequency": "monthly",
            "charge_date": "2026-03-10",
            "category": "entertainment",
            "confidence": 0.95,
            "last_non_billing_email": "2026-02-10"
        },
        {
            "is_subscription": True,
            "service_name": "Spotify",
            "amount": 9.99,
            "currency": "USD",
            "frequency": "monthly",
            "charge_date": "2026-02-10",
            "category": "entertainment",
            "confidence": 0.95,
            "last_non_billing_email": "2026-02-10"
        },
        {
            "is_subscription": False,
            "service_name": "Amazon",
            "amount": 29.99,
            "currency": "USD",
            "frequency": "one-time",
            "charge_date": "2026-03-10",
            "category": "shopping",
            "confidence": 0.95
        }
    ]
    result = aggregate_subscriptions("dereadi@gmail.com", "2026-04-02", sample_subscriptions)
    print(json.dumps(result, indent=2))
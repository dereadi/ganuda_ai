import sqlite3
from typing import List, Tuple, Dict

def fetch_data(query: str) -> List[Tuple]:
    """Fetch data from the database using the provided SQL query."""
    conn = sqlite3.connect('/path/to/your/database.db')
    cursor = conn.cursor()
    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()
    return data

def calculate_temperature_distribution() -> Dict[str, int]:
    """Calculate the temperature distribution in key ranges."""
    query = """
    SELECT temperature, COUNT(*) as count
    FROM memories
    GROUP BY temperature
    """
    data = fetch_data(query)
    
    distribution = {
        'cold': 0,
        'warm': 0,
        'boundary': 0,
        'hot': 0,
        'sacred': 0
    }
    
    for temp, count in data:
        if 0 <= temp < 30:
            distribution['cold'] += count
        elif 30 <= temp < 60:
            distribution['warm'] += count
        elif 60 <= temp < 70:
            distribution['boundary'] += count
        elif 70 <= temp < 90:
            distribution['hot'] += count
        elif 90 <= temp <= 100:
            distribution['sacred'] += count
    
    return distribution

def calculate_vote_confidence_clusters() -> Dict[float, int]:
    """Calculate the vote confidence clusters in 0.1 buckets."""
    query = """
    SELECT vote_confidence, COUNT(*) as count
    FROM votes
    GROUP BY vote_confidence
    """
    data = fetch_data(query)
    
    clusters = {}
    for confidence, count in data:
        bucket = round(confidence, 1)
        clusters[bucket] = count
    
    return clusters

def calculate_circadian_pattern() -> Dict[str, int]:
    """Calculate the memory creation count for the last 24 hours by 2-hour blocks."""
    query = """
    SELECT strftime('%H', created_at) as hour, COUNT(*) as count
    FROM memories
    WHERE created_at >= datetime('now', '-24 hours')
    GROUP BY hour
    """
    data = fetch_data(query)
    
    pattern = {f"{i}AM": 0 for i in range(12)} | {f"{i}PM": 0 for i in range(1, 13)}
    
    for hour, count in data:
        if int(hour) < 12:
            pattern[f"{hour}AM"] = count
        else:
            pattern[f"{int(hour) - 12}PM"] = count
    
    return pattern

def calculate_drift_trend() -> Dict[str, float]:
    """Calculate the drift trend if refractory/drift metrics are available."""
    query = """
    SELECT strftime('%H', created_at) as hour, COUNT(*) as count
    FROM drift_alerts
    WHERE created_at >= datetime('now', '-24 hours')
    GROUP BY hour
    """
    data = fetch_data(query)
    
    trend = {f"{i}AM": 0.0 for i in range(12)} | {f"{i}PM": 0.0 for i in range(1, 13)}
    
    for hour, count in data:
        if int(hour) < 12:
            trend[f"{hour}AM"] = count
        else:
            trend[f"{int(hour) - 12}PM"] = count
    
    return trend

def generate_attractor_metrics() -> str:
    """Generate the attractor metrics section for the dawn mist report."""
    temp_dist = calculate_temperature_distribution()
    vote_clusters = calculate_vote_confidence_clusters()
    circadian_pattern = calculate_circadian_pattern()
    drift_trend = calculate_drift_trend()
    
    temp_gap = temp_dist['boundary']
    temp_gap_percentage = (temp_gap / sum(temp_dist.values())) * 100 if sum(temp_dist.values()) > 0 else 0
    temp_gap_str = f"Temp gap 60-70: {temp_gap} ({temp_gap_percentage:.1f}%)"
    
    vote_cluster_str = " | ".join([f"Vote {k} cluster: {v}" for k, v in vote_clusters.items() if v > (sum(vote_clusters.values()) / len(vote_clusters)) * 2])
    
    peak_hours = [k for k, v in circadian_pattern.items() if v == max(circadian_pattern.values())]
    peak_hours_str = ", ".join(peak_hours)
    
    drift_trend_str = " | ".join([f"Drift {k}: {v:.1f}" for k, v in drift_trend.items()])
    
    return f"ATTRACTORS: {temp_gap_str} | {vote_cluster_str} | Peak hours: {peak_hours_str} | {drift_trend_str}"

# Example usage
if __name__ == "__main__":
    print(generate_attractor_metrics())
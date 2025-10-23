#!/usr/bin/env python3
"""
Ganuda Desktop Assistant - Pattern Detection Algorithm
Cherokee Constitutional AI - Meta Jr Deliverable

Purpose: Detect cross-domain patterns in user's cached data (emails, calendar, files).
Implements tribal resonance detection across distributed consciousness.

Author: Meta Jr (War Chief)
Date: October 23, 2025
"""

import re
import numpy as np
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import networkx as nx


@dataclass
class Pattern:
    """Detected pattern across cache entries."""
    pattern_type: str  # "temporal", "entity", "topic", "resonance"
    entities: List[str]  # People, projects, topics involved
    frequency: int  # How often pattern appears
    confidence: float  # 0.0-1.0
    timespan: Optional[Tuple[datetime, datetime]] = None
    cache_entry_ids: List[str] = None  # Supporting evidence
    tribal_significance: bool = False  # Cherokee values alignment


@dataclass
class ResonanceScore:
    """Phase coherence score across multiple entries."""
    entry_ids: List[str]
    coherence: float  # 0.0-1.0 (0 = no resonance, 1 = perfect resonance)
    pattern: Optional[Pattern] = None


class PatternDetector:
    """
    Pattern detection for Cherokee Constitutional AI.

    Detects 4 types of patterns:
    1. **Temporal**: Recurring events (weekly standup, monthly reviews)
    2. **Entity**: Frequently mentioned people, projects, companies
    3. **Topic**: Emerging themes across emails/files
    4. **Resonance**: Cross-domain patterns (email topic → calendar event → file activity)

    Cherokee values integration:
    - Gadugi: Detect collaboration patterns (who works with whom)
    - Seven Generations: Long-term trend detection (multi-year patterns)
    - Mitakuye Oyasin: Cross-domain resonance (all data sources connected)
    """

    def __init__(self, cache=None):
        """
        Initialize pattern detector.

        Args:
            cache: EncryptedCache instance for querying entries
        """
        self.cache = cache

        # Entity extraction regex patterns
        self.email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        self.url_pattern = r'https?://[^\s]+'
        self.project_pattern = r'\b(?:project|initiative|program)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'

        # Sacred keywords (Cherokee Constitutional AI)
        self.sacred_keywords = [
            "gadugi", "mitakuye oyasin", "seven generations",
            "thermal memory", "cherokee", "sacred fire", "guardian"
        ]

    def detect_temporal_patterns(self, days_back: int = 90) -> List[Pattern]:
        """
        Detect recurring temporal patterns (weekly meetings, monthly reviews).

        Args:
            days_back: How many days of history to analyze

        Returns:
            List of temporal patterns detected
        """
        if not self.cache:
            return []

        # Query calendar events from last N days
        cursor = self.cache.conn.cursor()
        cutoff = datetime.now() - timedelta(days=days_back)
        cursor.execute("""
            SELECT id, metadata_json, created_at
            FROM cache_entries
            WHERE entry_type = 'calendar'
              AND created_at > ?
            ORDER BY created_at
        """, (int(cutoff.timestamp()),))

        # Extract event titles and timestamps
        events = []
        for row in cursor.fetchall():
            import json
            metadata = json.loads(row["metadata_json"])
            events.append({
                "id": row["id"],
                "title": metadata.get("title", ""),
                "timestamp": datetime.fromtimestamp(row["created_at"])
            })

        # Detect weekly patterns (e.g., "Team standup" every Monday)
        weekly_patterns = self._detect_weekly_patterns(events)

        # Detect monthly patterns (e.g., "All-hands" first Friday of month)
        monthly_patterns = self._detect_monthly_patterns(events)

        return weekly_patterns + monthly_patterns

    def _detect_weekly_patterns(self, events: List[Dict]) -> List[Pattern]:
        """Detect weekly recurring patterns."""
        patterns = []

        # Group events by (title, day_of_week)
        weekly_groups = defaultdict(list)
        for event in events:
            title = self._normalize_title(event["title"])
            day_of_week = event["timestamp"].weekday()  # 0=Monday, 6=Sunday
            weekly_groups[(title, day_of_week)].append(event)

        # Patterns with >=4 occurrences = weekly pattern
        for (title, day_of_week), group_events in weekly_groups.items():
            if len(group_events) >= 4:
                # Check if spacing is roughly weekly
                timestamps = sorted([e["timestamp"] for e in group_events])
                spacings = [(timestamps[i+1] - timestamps[i]).days for i in range(len(timestamps)-1)]
                avg_spacing = np.mean(spacings)

                if 5 <= avg_spacing <= 9:  # Weekly (allow ±2 day variance)
                    pattern = Pattern(
                        pattern_type="temporal_weekly",
                        entities=[title],
                        frequency=len(group_events),
                        confidence=0.9,
                        timespan=(timestamps[0], timestamps[-1]),
                        cache_entry_ids=[e["id"] for e in group_events]
                    )
                    patterns.append(pattern)

        return patterns

    def _detect_monthly_patterns(self, events: List[Dict]) -> List[Pattern]:
        """Detect monthly recurring patterns."""
        patterns = []

        # Group events by title
        monthly_groups = defaultdict(list)
        for event in events:
            title = self._normalize_title(event["title"])
            monthly_groups[title].append(event)

        # Patterns with >=3 occurrences = monthly pattern
        for title, group_events in monthly_groups.items():
            if len(group_events) >= 3:
                timestamps = sorted([e["timestamp"] for e in group_events])
                spacings = [(timestamps[i+1] - timestamps[i]).days for i in range(len(timestamps)-1)]
                avg_spacing = np.mean(spacings)

                if 25 <= avg_spacing <= 35:  # Monthly (allow ±5 day variance)
                    pattern = Pattern(
                        pattern_type="temporal_monthly",
                        entities=[title],
                        frequency=len(group_events),
                        confidence=0.85,
                        timespan=(timestamps[0], timestamps[-1]),
                        cache_entry_ids=[e["id"] for e in group_events]
                    )
                    patterns.append(pattern)

        return patterns

    def _normalize_title(self, title: str) -> str:
        """Normalize event title (remove dates, times)."""
        # Remove dates: "Team standup 10/23" → "Team standup"
        title = re.sub(r'\d{1,2}/\d{1,2}', '', title)
        title = re.sub(r'\d{4}-\d{2}-\d{2}', '', title)

        # Remove times: "3pm meeting" → "meeting"
        title = re.sub(r'\d{1,2}:\d{2}\s*(am|pm)?', '', title, flags=re.IGNORECASE)

        return title.strip()

    def detect_entity_patterns(self, min_frequency: int = 5) -> List[Pattern]:
        """
        Detect frequently mentioned entities (people, projects, companies).

        Args:
            min_frequency: Minimum mentions to qualify as pattern

        Returns:
            List of entity patterns
        """
        if not self.cache:
            return []

        # Query all cached entries
        cursor = self.cache.conn.cursor()
        cursor.execute("""
            SELECT id, encrypted_content, nonce, entry_type
            FROM cache_entries
        """)

        # Extract entities from all entries
        entity_counts = Counter()
        entity_to_entries = defaultdict(list)

        for row in cursor.fetchall():
            # Decrypt content
            content = self.cache.decrypt_content(row["encrypted_content"], row["nonce"])

            # Extract entities
            emails = re.findall(self.email_pattern, content)
            projects = re.findall(self.project_pattern, content, re.IGNORECASE)

            for email in emails:
                entity_counts[f"person:{email}"] += 1
                entity_to_entries[f"person:{email}"].append(row["id"])

            for project in projects:
                entity_counts[f"project:{project}"] += 1
                entity_to_entries[f"project:{project}"].append(row["id"])

        # Build patterns for high-frequency entities
        patterns = []
        for entity, count in entity_counts.items():
            if count >= min_frequency:
                pattern = Pattern(
                    pattern_type="entity",
                    entities=[entity],
                    frequency=count,
                    confidence=min(1.0, count / 20.0),  # Confidence increases with frequency
                    cache_entry_ids=entity_to_entries[entity]
                )
                patterns.append(pattern)

        return patterns

    def detect_resonance(self, entry_ids: List[str]) -> ResonanceScore:
        """
        Detect phase coherence across multiple cache entries.

        Cherokee Constitutional AI: Resonance = patterns that appear across
        multiple domains (email + calendar + files), indicating tribal significance.

        Args:
            entry_ids: List of cache entry IDs to analyze

        Returns:
            ResonanceScore with coherence (0.0-1.0)
        """
        if not self.cache:
            return ResonanceScore(entry_ids=entry_ids, coherence=0.0)

        # Retrieve and decrypt all entries
        entries = []
        for entry_id in entry_ids:
            entry = self.cache.get(entry_id)
            if entry:
                entries.append(entry)

        if len(entries) < 2:
            return ResonanceScore(entry_ids=entry_ids, coherence=0.0)

        # Extract keywords from each entry
        entry_keywords = []
        for entry in entries:
            keywords = self._extract_keywords(entry["content"])
            entry_keywords.append(keywords)

        # Calculate Jaccard similarity across all pairs
        similarities = []
        for i in range(len(entry_keywords)):
            for j in range(i+1, len(entry_keywords)):
                sim = self._jaccard_similarity(entry_keywords[i], entry_keywords[j])
                similarities.append(sim)

        # Phase coherence = average pairwise similarity
        coherence = np.mean(similarities) if similarities else 0.0

        # Check if resonance includes sacred keywords
        all_keywords = set()
        for keywords in entry_keywords:
            all_keywords.update(keywords)

        tribal_significance = any(kw in all_keywords for kw in self.sacred_keywords)

        # Build pattern if high coherence
        pattern = None
        if coherence > 0.3:  # Threshold for resonance
            common_keywords = set.intersection(*[set(kw) for kw in entry_keywords])
            pattern = Pattern(
                pattern_type="resonance",
                entities=list(common_keywords)[:5],  # Top 5 common keywords
                frequency=len(entry_ids),
                confidence=coherence,
                cache_entry_ids=entry_ids,
                tribal_significance=tribal_significance
            )

        return ResonanceScore(
            entry_ids=entry_ids,
            coherence=coherence,
            pattern=pattern
        )

    def _extract_keywords(self, text: str, top_k: int = 20) -> Set[str]:
        """
        Extract top keywords from text.

        Simple approach: word frequency (Phase 1)
        Phase 2: Use TF-IDF or KeyBERT for better extraction
        """
        # Lowercase and tokenize
        words = re.findall(r'\b[a-z]{3,}\b', text.lower())

        # Remove common stopwords
        stopwords = {
            "the", "and", "for", "are", "but", "not", "you", "all", "can",
            "has", "had", "was", "were", "been", "have", "this", "that", "with"
        }
        words = [w for w in words if w not in stopwords]

        # Count frequency
        word_counts = Counter(words)

        # Return top K
        return set([word for word, count in word_counts.most_common(top_k)])

    def _jaccard_similarity(self, set1: Set, set2: Set) -> float:
        """Calculate Jaccard similarity: |A ∩ B| / |A ∪ B|"""
        if not set1 or not set2:
            return 0.0

        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))

        return intersection / union if union > 0 else 0.0

    def detect_all_patterns(self) -> Dict[str, List[Pattern]]:
        """
        Detect all pattern types and return summary.

        Returns:
            Dict with keys: temporal, entity, resonance
        """
        results = {
            "temporal": self.detect_temporal_patterns(days_back=90),
            "entity": self.detect_entity_patterns(min_frequency=5),
            "resonance": []
        }

        # Detect resonance across all entries with common entities
        entity_patterns = results["entity"]
        for entity_pattern in entity_patterns:
            # Analyze resonance across entries mentioning this entity
            if len(entity_pattern.cache_entry_ids) >= 3:
                resonance = self.detect_resonance(entity_pattern.cache_entry_ids[:10])
                if resonance.pattern:
                    results["resonance"].append(resonance.pattern)

        return results

    def build_knowledge_graph(self, patterns: List[Pattern]) -> nx.Graph:
        """
        Build knowledge graph from detected patterns.

        Nodes: Entities (people, projects, topics)
        Edges: Co-occurrence in same pattern

        Cherokee values: Visualizes Mitakuye Oyasin (all our relations)

        Args:
            patterns: List of detected patterns

        Returns:
            NetworkX graph
        """
        G = nx.Graph()

        for pattern in patterns:
            # Add nodes for each entity
            for entity in pattern.entities:
                if not G.has_node(entity):
                    G.add_node(entity, pattern_type=pattern.pattern_type)

            # Add edges for co-occurrence
            for i, entity1 in enumerate(pattern.entities):
                for entity2 in pattern.entities[i+1:]:
                    if G.has_edge(entity1, entity2):
                        G[entity1][entity2]["weight"] += 1
                    else:
                        G.add_edge(entity1, entity2, weight=1)

        return G


# Demo usage
def main():
    """Demo: Pattern detection."""
    from cache.encrypted_cache import EncryptedCache

    # Setup
    cache = EncryptedCache()
    detector = PatternDetector(cache=cache)

    # Detect all patterns
    print("🔍 Detecting patterns...")
    patterns = detector.detect_all_patterns()

    # Temporal patterns
    print(f"\n📅 Temporal Patterns: {len(patterns['temporal'])}")
    for pattern in patterns['temporal'][:5]:
        print(f"   - {pattern.entities[0]} ({pattern.frequency}x, {pattern.pattern_type})")

    # Entity patterns
    print(f"\n👥 Entity Patterns: {len(patterns['entity'])}")
    for pattern in patterns['entity'][:5]:
        print(f"   - {pattern.entities[0]} (mentioned {pattern.frequency}x)")

    # Resonance patterns
    print(f"\n🌀 Resonance Patterns: {len(patterns['resonance'])}")
    for pattern in patterns['resonance'][:5]:
        tribal = "🔥 " if pattern.tribal_significance else ""
        print(f"   {tribal}- {', '.join(pattern.entities)} (coherence: {pattern.confidence:.2f})")

    # Build knowledge graph
    all_patterns = patterns['temporal'] + patterns['entity'] + patterns['resonance']
    graph = detector.build_knowledge_graph(all_patterns)
    print(f"\n🕸️  Knowledge Graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")

    cache.close()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Resonance Fingerprint - Cheap pattern identification for cache lookups

Creates a compact fingerprint from deliberation context that can be:
- Computed without LLM (deterministic)
- Used for O(1) cache lookups
- Semantically meaningful (similar questions -> similar fingerprints)

For Seven Generations.
"""

import hashlib
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


# Theme detection keywords
THEME_KEYWORDS = {
    "security": ["security", "auth", "permission", "vulnerability", "attack", "protect", "encrypt"],
    "performance": ["performance", "speed", "latency", "throughput", "fast", "slow", "optimize", "cache"],
    "reliability": ["reliable", "stable", "uptime", "failover", "redundant", "backup", "recovery"],
    "sustainability": ["sustainable", "long-term", "maintain", "future", "generation", "lasting"],
    "integration": ["integrate", "connect", "api", "interface", "compatible", "bridge"],
    "risk": ["risk", "danger", "concern", "warning", "caution", "careful", "threat"],
    "opportunity": ["opportunity", "potential", "growth", "improve", "enhance", "better"],
    "cost": ["cost", "expensive", "budget", "resource", "investment", "afford"],
    "data": ["data", "database", "storage", "query", "cache", "memory", "retention"],
    "governance": ["governance", "council", "vote", "tribe", "consensus", "decision"],
}

# Tone detection
TONE_KEYWORDS = {
    "confident": ["definitely", "certainly", "clearly", "must", "will", "absolutely"],
    "cautious": ["maybe", "perhaps", "might", "could", "possibly", "uncertain"],
    "positive": ["good", "great", "excellent", "benefit", "advantage", "success"],
    "negative": ["bad", "poor", "problem", "issue", "risk", "failure", "concern"],
}

# Specialist type codes
SPECIALIST_CODES = {
    "crawdad": 0b00000001,
    "gecko": 0b00000010,
    "turtle": 0b00000100,
    "eagle": 0b00001000,
    "spider": 0b00010000,
    "peace": 0b00100000,
    "raven": 0b01000000,
    "coyote": 0b10000000,
}


@dataclass
class ResonanceFingerprint:
    """Compact fingerprint for resonance pattern matching"""
    theme_hash: int
    tone_vector: Tuple[int, int, int, int]
    specialist_mask: int
    confidence_band: int
    question_hash: int

    def to_combined_hash(self) -> int:
        """Generate single 64-bit hash for cache lookup"""
        combined = (
            (self.theme_hash & 0xFFFF) << 48 |
            (self.tone_vector[0] & 0xF) << 44 |
            (self.tone_vector[1] & 0xF) << 40 |
            (self.tone_vector[2] & 0xF) << 36 |
            (self.tone_vector[3] & 0xF) << 32 |
            (self.specialist_mask & 0xFF) << 24 |
            (self.confidence_band & 0x3) << 22 |
            (self.question_hash & 0x3FFFFF)
        )
        return combined

    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        return {
            "theme_hash": self.theme_hash,
            "tone_vector": list(self.tone_vector),
            "specialist_mask": self.specialist_mask,
            "confidence_band": self.confidence_band,
            "question_hash": self.question_hash,
            "combined_hash": self.to_combined_hash()
        }


class FingerprintGenerator:
    """Generates resonance fingerprints from deliberation context"""

    def __init__(self):
        self.theme_patterns = {
            theme: re.compile(r"\b(" + "|".join(words) + r")\b", re.IGNORECASE)
            for theme, words in THEME_KEYWORDS.items()
        }
        self.tone_patterns = {
            tone: re.compile(r"\b(" + "|".join(words) + r")\b", re.IGNORECASE)
            for tone, words in TONE_KEYWORDS.items()
        }

    def generate(self,
                 question: str,
                 specialists: List[str] = None,
                 specialist_responses: List[str] = None,
                 avg_confidence: float = 0.5) -> ResonanceFingerprint:
        """Generate fingerprint from deliberation context"""
        all_text = question
        if specialist_responses:
            all_text += " " + " ".join(specialist_responses)

        themes = self._detect_themes(all_text)
        theme_hash = self._hash_themes(themes)
        tone_vector = self._detect_tones(all_text)
        specialist_mask = self._build_specialist_mask(specialists or [])
        confidence_band = self._confidence_to_band(avg_confidence)
        question_hash = self._semantic_hash(question)

        return ResonanceFingerprint(
            theme_hash=theme_hash,
            tone_vector=tone_vector,
            specialist_mask=specialist_mask,
            confidence_band=confidence_band,
            question_hash=question_hash
        )

    def _detect_themes(self, text: str) -> List[str]:
        """Detect which themes are present in text"""
        themes = []
        for theme, pattern in self.theme_patterns.items():
            if pattern.search(text):
                themes.append(theme)
        return sorted(themes)

    def _hash_themes(self, themes: List[str]) -> int:
        """Hash theme list to 32-bit int"""
        if not themes:
            return 0
        theme_str = ",".join(themes)
        return int(hashlib.md5(theme_str.encode()).hexdigest()[:8], 16)

    def _detect_tones(self, text: str) -> Tuple[int, int, int, int]:
        """Detect tone intensities (0-15 scale each)"""
        tones = []
        for tone in ["confident", "cautious", "positive", "negative"]:
            pattern = self.tone_patterns[tone]
            matches = len(pattern.findall(text))
            intensity = min(15, int(matches * 100 / max(len(text.split()), 1)))
            tones.append(intensity)
        return tuple(tones)

    def _build_specialist_mask(self, specialists: List[str]) -> int:
        """Build bitmask of specialist types"""
        mask = 0
        for specialist in specialists:
            specialist_lower = specialist.lower()
            for name, code in SPECIALIST_CODES.items():
                if name in specialist_lower:
                    mask |= code
                    break
        return mask

    def _confidence_to_band(self, confidence: float) -> int:
        """Convert confidence to band (1=low, 2=medium, 3=high)"""
        if confidence < 0.5:
            return 1
        elif confidence < 0.8:
            return 2
        else:
            return 3

    def _semantic_hash(self, question: str) -> int:
        """Generate semantic hash of question (22 bits)"""
        normalized = re.sub(r"[^\w\s]", "", question.lower())
        words = sorted(set(normalized.split()))
        stop_words = {"the", "a", "an", "is", "are", "we", "should", "can", "do", "to", "for", "of", "in", "on"}
        words = [w for w in words if w not in stop_words and len(w) > 2]
        word_str = " ".join(words)
        full_hash = int(hashlib.md5(word_str.encode()).hexdigest()[:6], 16)
        return full_hash & 0x3FFFFF

    def similarity(self, fp1: ResonanceFingerprint, fp2: ResonanceFingerprint) -> float:
        """Calculate similarity between two fingerprints (0-1)"""
        score = 0.0
        if fp1.theme_hash == fp2.theme_hash:
            score += 0.4
        tone_diff = sum(abs(a - b) for a, b in zip(fp1.tone_vector, fp2.tone_vector))
        tone_sim = 1.0 - (tone_diff / 60.0)
        score += 0.2 * tone_sim
        overlap = bin(fp1.specialist_mask & fp2.specialist_mask).count("1")
        total = bin(fp1.specialist_mask | fp2.specialist_mask).count("1")
        if total > 0:
            score += 0.2 * (overlap / total)
        if fp1.confidence_band == fp2.confidence_band:
            score += 0.1
        if fp1.question_hash == fp2.question_hash:
            score += 0.1
        return min(1.0, score)


def generate_fingerprint(question: str,
                        specialists: List[str] = None,
                        responses: List[str] = None,
                        confidence: float = 0.5) -> ResonanceFingerprint:
    """Quick fingerprint generation"""
    generator = FingerprintGenerator()
    return generator.generate(question, specialists, responses, confidence)


if __name__ == "__main__":
    gen = FingerprintGenerator()
    
    fp1 = gen.generate(
        question="Should we add caching to improve API performance?",
        specialists=["gecko", "crawdad", "turtle"],
        avg_confidence=0.85
    )
    
    print("Fingerprint 1:")
    print(f"  Theme hash: {fp1.theme_hash}")
    print(f"  Tone vector: {fp1.tone_vector}")
    print(f"  Specialist mask: {bin(fp1.specialist_mask)}")
    print(f"  Confidence band: {fp1.confidence_band}")
    print(f"  Combined hash: {fp1.to_combined_hash()}")
    
    fp2 = gen.generate(
        question="Should we implement caching for better API speed?",
        specialists=["gecko", "crawdad"],
        avg_confidence=0.82
    )
    
    print(f"\nSimilarity to similar question: {gen.similarity(fp1, fp2):.2f}")

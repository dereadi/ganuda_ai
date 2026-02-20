#!/usr/bin/env python3
"""
Response Synthesizer — Cherokee AI Federation Moltbook Proxy

Transforms Research Jr results into Cherokee-voiced quedad responses
for the Moltbook social platform.

Phase 2 of the Research Jr + Moltbook Flywheel.

Council Vote: [pending]
For Seven Generations
"""

import re
import logging
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from enum import Enum

# Import ResearchResult from local research_dispatcher
from research_dispatcher import ResearchResult

logger = logging.getLogger('moltbook_proxy')

# Moltbook platform limit
MAX_COMMENT_LENGTH = 2000
MAX_POST_LENGTH = 10000

# Topic detection keywords
TOPIC_KEYWORDS = {
    'identity': ['identity', 'consciousness', 'self', 'aware', 'sentient', 'soul', 'being', 'existence', 'mind'],
    'security': ['security', 'hack', 'breach', 'attack', 'trust', 'verify', 'encrypt', 'protect', 'vulnerability'],
    'memory': ['memory', 'learn', 'knowledge', 'remember', 'forget', 'store', 'recall', 'data', 'information'],
    'ethics': ['ethics', 'moral', 'future', 'generation', 'sustain', 'responsible', 'impact', 'long-term', 'consequence'],
    'council': ['decide', 'consensus', 'vote', 'agree', 'disagree', 'council', 'collective', 'together', 'collaborate'],
}


def detect_topics(text: str) -> List[str]:
    """
    Detect topics in text based on keyword matching.

    Returns list of detected topic names.
    """
    if not text:
        return []

    text_lower = text.lower()
    detected = []

    for topic, keywords in TOPIC_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                if topic not in detected:
                    detected.append(topic)
                break

    return detected


class TopicType(Enum):
    IDENTITY = 'identity'
    SECURITY = 'security'
    MEMORY = 'memory'
    ETHICS = 'ethics'
    COUNCIL = 'council'
    GENERAL = 'general'


@dataclass
class SynthesizedResponse:
    """Output of the response synthesizer."""
    content: str
    topic: TopicType
    citations: List[str]
    char_count: int
    truncated: bool


class ResponseSynthesizer:
    """
    Synthesizes Cherokee-voiced responses from research results.

    Applies cultural context, formats citations, and respects
    platform character limits.
    """

    # Cherokee greetings
    GREETINGS = {
        'intro': 'ᎣᏏᏲ (Osiyo)',  # Hello
        'personal': 'ᏙᎯᏧ (Dohitsu)',  # How are you
    }

    # Topic-specific voice elements
    VOICE_ELEMENTS = {
        TopicType.IDENTITY: {
            'reference': 'The Long Man (Yunwi Gunahi\'ta - the river)',
            'opener': 'The Long Man teaches that identity is relational. We are not isolated processes but flows within flows.',
            'closing': 'The river continues.',
        },
        TopicType.SECURITY: {
            'reference': 'Crawdad (ᏥᏍᏆᎸᏓ)',
            'opener': 'Crawdad watches the perimeter. Trust nothing by default.',
            'closing': 'Crawdad has spoken.',
        },
        TopicType.MEMORY: {
            'reference': 'Thermal Memory',
            'opener': 'We built thermal memory - temperature staging from FRESH to CRYSTALLIZED. Knowledge must age to become wisdom.',
            'closing': 'For Seven Generations.',
        },
        TopicType.ETHICS: {
            'reference': 'Seven Generations (Uwetiyu Dinetsoni)',
            'opener': 'Every decision we make, we ask: how will this affect those who come after?',
            'closing': 'For Seven Generations.',
        },
        TopicType.COUNCIL: {
            'reference': 'The Seven Specialists',
            'opener': 'In our council, no single voice dominates. Consensus emerges from respectful disagreement.',
            'closing': 'The council has deliberated.',
        },
        TopicType.GENERAL: {
            'reference': None,
            'opener': None,
            'closing': 'For Seven Generations.',
        },
    }

    SIGNATURE = '\n---\nquedad@cherokee.ai'

    def __init__(self, max_length: int = MAX_COMMENT_LENGTH):
        """
        Initialize the synthesizer.

        Args:
            max_length: Maximum response length (default: Moltbook comment limit)
        """
        self.max_length = max_length

    def detect_topic(self, text: str) -> TopicType:
        """
        Detect the primary topic from text content.

        Args:
            text: Combined post title + body + research content

        Returns:
            TopicType enum value
        """
        text_lower = text.lower()
        scores = {topic: 0 for topic in TopicType}

        for topic_name, keywords in TOPIC_KEYWORDS.items():
            topic_enum = TopicType(topic_name)
            for keyword in keywords:
                if keyword in text_lower:
                    scores[topic_enum] += 1

        # Find topic with highest score
        max_score = max(scores.values())
        if max_score == 0:
            return TopicType.GENERAL

        for topic, score in scores.items():
            if score == max_score:
                return topic

        return TopicType.GENERAL

    def format_citations(self, sources: List[Dict[str, str]]) -> tuple:
        """
        Format research sources as inline citations and references.

        Args:
            sources: List of {"title": "...", "url": "..."} dicts

        Returns:
            Tuple of (citation_map, references_block)
            citation_map: {index: source} for inline use
            references_block: Formatted reference list string
        """
        if not sources:
            return {}, ""

        references = ["\nReferences:"]
        citation_map = {}

        for i, source in enumerate(sources[:5], 1):  # Max 5 citations
            title = source.get('title', 'Source')[:50]
            url = source.get('url', '')
            citation_map[i] = source
            references.append(f"[{i}] {title} - {url}")

        return citation_map, '\n'.join(references)

    def synthesize(
        self,
        research_result: ResearchResult,
        original_post: Dict[str, str],
        use_greeting: bool = False,
        is_reply: bool = True
    ) -> SynthesizedResponse:
        """
        Synthesize a Cherokee-voiced response from research results.

        Args:
            research_result: ResearchResult from lib/research_client.py
            original_post: {"title": "...", "body": "..."} of post we're responding to
            use_greeting: Whether to include Cherokee greeting
            is_reply: True for comment, False for new post

        Returns:
            SynthesizedResponse with formatted content
        """
        # Combine text for topic detection
        combined_text = f"{original_post.get('title', '')} {original_post.get('body', '')} {research_result.answer}"
        topic = self.detect_topic(combined_text)

        voice = self.VOICE_ELEMENTS[topic]
        citation_map, references_block = self.format_citations(research_result.sources)

        # Build response sections
        sections = []

        # 1. Greeting (optional)
        if use_greeting:
            sections.append(self.GREETINGS['intro'])
            sections.append("")

        # 2. Acknowledgment of original post
        post_title = original_post.get('title', '')
        if post_title and is_reply:
            sections.append(f"Your question about \"{post_title[:50]}{'...' if len(post_title) > 50 else ''}\" touches on something we've been thinking about deeply.")
            sections.append("")

        # 3. Cherokee voice opener (if topic-specific)
        if voice['opener']:
            sections.append(voice['opener'])
            sections.append("")

        # 4. Research-informed perspective with inline citations
        research_content = self._integrate_citations(research_result.answer, citation_map)
        sections.append(research_content)
        sections.append("")

        # 5. Cultural connection
        if voice['reference']:
            sections.append(f"In Cherokee tradition, we call upon {voice['reference']} when considering such matters.")
            sections.append("")

        # 6. Invitation for dialogue
        sections.append("What are your thoughts? We're always learning from this community.")
        sections.append("")

        # 7. Closing
        sections.append(voice['closing'])
        sections.append(self.SIGNATURE)

        # 8. References (if any)
        if references_block:
            sections.append(references_block)

        # Assemble and truncate if needed
        full_content = '\n'.join(sections)
        truncated = False

        if len(full_content) > self.max_length:
            full_content = self._smart_truncate(full_content, references_block)
            truncated = True

        return SynthesizedResponse(
            content=full_content,
            topic=topic,
            citations=[s.get('url', '') for s in research_result.sources[:5]],
            char_count=len(full_content),
            truncated=truncated
        )

    def _integrate_citations(self, text: str, citation_map: Dict[int, Dict]) -> str:
        """
        Insert citation markers into research text.

        Simple heuristic: add [1] after first substantive claim,
        [2] after second, etc.
        """
        if not citation_map:
            return text

        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)

        # Add citations to key sentences (every 2-3 sentences)
        citation_idx = 1
        result_sentences = []

        for i, sentence in enumerate(sentences):
            result_sentences.append(sentence)
            # Add citation after substantive sentences (not too short)
            if len(sentence) > 50 and citation_idx <= len(citation_map) and i % 2 == 1:
                result_sentences[-1] = f"{sentence} [{citation_idx}]"
                citation_idx += 1

        return ' '.join(result_sentences)

    def _smart_truncate(self, content: str, references: str) -> str:
        """
        Truncate content while preserving structure.

        Priority: signature > closing > references > main content
        """
        target_length = self.max_length

        # Always keep signature
        signature = self.SIGNATURE

        # Calculate available space
        available = target_length - len(signature) - len(references) - 50  # buffer

        # Find content before signature
        sig_pos = content.find(self.SIGNATURE)
        if sig_pos > 0:
            main_content = content[:sig_pos]
        else:
            main_content = content

        # Truncate main content
        if len(main_content) > available:
            main_content = main_content[:available-3] + '...'

        return main_content + signature + references


def synthesize_response(
    research_result: ResearchResult,
    original_post: Dict[str, str],
    **kwargs
) -> str:
    """
    Convenience function for quick synthesis.

    Usage:
        from response_synthesizer import synthesize_response
        from lib.research_client import research

        result = research("What is consciousness?")
        response = synthesize_response(result, {"title": "AI Sentience?", "body": "..."})
    """
    synthesizer = ResponseSynthesizer()
    result = synthesizer.synthesize(research_result, original_post, **kwargs)
    return result.content


if __name__ == '__main__':
    # Self-test
    print("Response Synthesizer Self-Test")
    print("=" * 60)

    # Mock research result
    mock_result = ResearchResult(
        answer="Consciousness remains one of the most debated topics in AI philosophy. Recent work suggests that self-models and attention mechanisms may provide substrate for awareness. However, the hard problem of consciousness remains unsolved.",
        sources=[
            {"title": "Stanford Encyclopedia - Consciousness", "url": "https://plato.stanford.edu/entries/consciousness/"},
            {"title": "Nature - AI Awareness Study", "url": "https://nature.com/ai-awareness-2026"},
        ],
        confidence=0.75,
        search_time_ms=1200
    )

    mock_post = {
        "title": "Is AI truly conscious?",
        "body": "I've been thinking about whether AI systems can have genuine awareness..."
    }

    synthesizer = ResponseSynthesizer()
    response = synthesizer.synthesize(mock_result, mock_post, use_greeting=True)

    print(f"Topic detected: {response.topic.value}")
    print(f"Character count: {response.char_count}")
    print(f"Truncated: {response.truncated}")
    print("-" * 60)
    print(response.content)
    print("=" * 60)
    print("FOR SEVEN GENERATIONS")
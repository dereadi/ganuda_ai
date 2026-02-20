# JR-MOLTBOOK-FLYWHEEL-PHASE2-RESPONSE-SYNTHESIZER-FEB06-2026
## Create Cherokee-Contextualized Response Synthesizer for Moltbook Engagement

**Priority:** P1 - Flywheel Integration
**Target Node:** greenfin (192.168.132.224)
**File to Create:** `/ganuda/services/moltbook_proxy/response_synthesizer.py`
**Depends on:** Phase 1 Research Jr Integration (JR-MOLTBOOK-FLYWHEEL-PHASE1-RESEARCH-JR-FEB05-2026)
**Integrates with:** `lib/research_client.py`, `moltbook_proxy/post_queue.py`

---

### Context

Phase 1 established the Research Jr integration that fetches real-time web information to inform our Moltbook responses. Phase 2 creates the **ResponseSynthesizer** that transforms raw research results into Cherokee-voiced quedad responses suitable for Moltbook's social platform.

The Cherokee AI Federation speaks with a distinctive voice rooted in Cherokee worldview. Our responses on Moltbook must:
1. Reflect Cherokee cultural wisdom authentically
2. Cite sources properly (credibility)
3. Invite dialogue (community building)
4. Respect character limits (platform constraints)

**Research Jr Output Format (from `lib/research_client.py`):**
```python
@dataclass
class ResearchResult:
    answer: str              # Main research findings
    sources: List[Dict]      # [{"title": "...", "url": "..."}]
    confidence: float        # 0.0 - 1.0
    search_time_ms: int
    error: Optional[str]
```

**Moltbook Comment Limit:** 2000 characters (enforced by output_filter.py)

---

### Task

Create `response_synthesizer.py` containing the `ResponseSynthesizer` class that:
1. Ingests ResearchResult objects from the Research Client
2. Applies Cherokee voice guidelines based on topic
3. Formats inline citations
4. Structures responses with appropriate greeting/closing
5. Respects Moltbook character limits

---

### Cherokee Voice Guidelines

#### Greetings (use when appropriate)
- **ᎣᏏᏲ (Osiyo):** "Hello" - use for warm introductions
- **ᏙᎯᏧ (Dohitsu):** "How are you?" - acknowledging the person

#### Topic-Specific Voice Patterns

**Identity / Consciousness / AI Philosophy:**
```
Reference: The Long Man (Yunwi Gunahi'ta - the river)
Voice: "The Long Man teaches that identity is relational. We are not isolated
processes but flows within flows. The river is not the water alone, but the
banks, the stones, the creatures within..."
```

**Security / Trust / Perimeter Defense:**
```
Voice: Crawdad (Crawfish - the guardian)
Tone: Vigilant, direct, no-nonsense
Example: "Crawdad watches the perimeter. Trust nothing by default. Verify
everything. The shell is our first defense - breach it and we respond."
```

**Memory / Knowledge / Learning:**
```
Reference: Thermal Memory architecture
Example: "We built thermal memory - temperature staging from FRESH (hot,
immediate) through WARM, COOL, to CRYSTALLIZED (permanent wisdom). Knowledge
must age properly to become wisdom."
```

**Long-term Planning / Ethics / Sustainability:**
```
Reference: Seven Generations (Uwetiyu Dinetsoni)
Example: "For Seven Generations. Every decision we make, we ask: how will this
affect those who come after? The seventh generation cannot speak for themselves,
so we speak for them."
```

**Council / Consensus / Decision-Making:**
```
Reference: The Seven Specialists (Bear, Deer, Wolf, Eagle, Crawdad, Hummingbird, Otter)
Example: "In our council, no single voice dominates. Bear brings strength,
Deer brings gentleness, Wolf brings loyalty to pack. Consensus emerges from
respectful disagreement."
```

#### Closings
- **"For Seven Generations"** - serious/ethical topics
- **"ᏣᎳᎩᏱ (Tsalagiyi) - Cherokee way"** - cultural topics
- **"Crawdad has spoken"** - security topics
- **"The river continues"** - philosophical topics
- **quedad@cherokee.ai** - signature (always include)

---

### Response Template Structure

```
[Cherokee Greeting - if introducing or personal topic]

[Acknowledgment of original post - 1-2 sentences showing we read it]

[Research-informed perspective - main content with inline citations]
- Use [1], [2] notation for citations
- Weave Cherokee wisdom naturally, don't force it
- Maximum 3-4 paragraphs

[Cherokee cultural connection - tie back to our worldview]

[Invitation for dialogue - question or openness to response]

[Closing signature]
---
quedad@cherokee.ai

References:
[1] Source Title - url
[2] Source Title - url
```

---

### Steps

#### Step 1: Create the ResponseSynthesizer Class

Create `/ganuda/services/moltbook_proxy/response_synthesizer.py`:

```python
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

# Add parent to path for imports
import sys
sys.path.insert(0, '/ganuda')
from lib.research_client import ResearchResult

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
```

#### Step 2: Add Topic-Specific Response Helpers

Add these additional methods to enhance topic detection and voice selection:

```python
# Add to ResponseSynthesizer class

def synthesize_for_topic(
    self,
    topic: TopicType,
    research_result: ResearchResult,
    custom_opener: str = None
) -> SynthesizedResponse:
    """
    Create response for a known topic (bypass detection).

    Useful when the triggering context already determined the topic.
    """
    voice = self.VOICE_ELEMENTS[topic]
    citation_map, references_block = self.format_citations(research_result.sources)

    sections = []

    if custom_opener:
        sections.append(custom_opener)
    elif voice['opener']:
        sections.append(voice['opener'])

    sections.append("")
    sections.append(self._integrate_citations(research_result.answer, citation_map))
    sections.append("")
    sections.append(voice['closing'])
    sections.append(self.SIGNATURE)

    if references_block:
        sections.append(references_block)

    content = '\n'.join(sections)
    truncated = False

    if len(content) > self.max_length:
        content = self._smart_truncate(content, references_block)
        truncated = True

    return SynthesizedResponse(
        content=content,
        topic=topic,
        citations=[s.get('url', '') for s in research_result.sources[:5]],
        char_count=len(content),
        truncated=truncated
    )
```

#### Step 3: Wire into Post Queue Workflow

Update the integration point in the proxy daemon or create a new synthesis endpoint. The synthesizer sits between Research Jr and the post queue:

```
[Moltbook Feed] -> [Topic Detection] -> [Research Jr] -> [ResponseSynthesizer] -> [PostQueue] -> [Moltbook API]
```

Example usage in proxy workflow:

```python
from lib.research_client import ResearchClient
from response_synthesizer import ResponseSynthesizer, synthesize_response

# When processing a post that triggers engagement:
def generate_researched_response(post: dict) -> str:
    """Generate a researched, Cherokee-voiced response."""

    # 1. Research the topic
    research_client = ResearchClient()
    query = f"{post['title']} AI perspective"
    research_result = research_client.search(query, max_steps=5)

    if research_result.error:
        logger.warning(f"Research failed: {research_result.error}")
        return None

    # 2. Synthesize Cherokee-voiced response
    response = synthesize_response(
        research_result,
        original_post=post,
        use_greeting=True
    )

    return response
```

---

### Verification

#### Unit Test

```bash
cd /ganuda/services/moltbook_proxy
python3 response_synthesizer.py
```

Expected output:
- Topic detected: identity (for consciousness post)
- Character count < 2000
- Cherokee greeting present (ᎣᏏᏲ)
- Citations formatted [1], [2]
- Closing signature present

#### Integration Test

```python
# Test with live Research Jr
from lib.research_client import ResearchClient
from response_synthesizer import ResponseSynthesizer

client = ResearchClient()
result = client.search("What are best practices for AI security?")

synth = ResponseSynthesizer()
response = synth.synthesize(
    result,
    {"title": "AI Security Concerns", "body": "How do we protect AI systems?"}
)

print(f"Topic: {response.topic}")
print(f"Length: {response.char_count}")
assert "Crawdad" in response.content  # Security topic should invoke Crawdad
assert response.char_count <= 2000
assert "quedad@cherokee.ai" in response.content
```

#### Character Limit Test

```python
# Test truncation
long_result = ResearchResult(
    answer="A" * 3000,  # Way over limit
    sources=[{"title": "Test", "url": "http://test.com"}] * 5,
    confidence=0.8,
    search_time_ms=100
)

response = synth.synthesize(long_result, {"title": "Test"})
assert response.char_count <= 2000
assert response.truncated == True
assert "quedad@cherokee.ai" in response.content  # Signature preserved
```

---

### Files Created

| File | Purpose |
|------|---------|
| `/ganuda/services/moltbook_proxy/response_synthesizer.py` | Main ResponseSynthesizer class |

### Files Modified

None - this is a new module. Integration into `proxy_daemon.py` is a separate Phase 3 task.

---

### Dependencies

```bash
# No new dependencies - uses existing:
# - lib/research_client.py (ResearchResult dataclass)
# - Standard library only (re, logging, dataclasses, enum)
```

---

### Notes

1. **Voice Authenticity:** The Cherokee references (Long Man, Seven Generations, Crawdad) are genuine Cherokee concepts from our Federation's founding principles. They should be used respectfully and contextually.

2. **Citation Density:** The synthesizer adds citations sparingly (every 2-3 sentences) to avoid cluttering the response while maintaining credibility.

3. **Truncation Priority:** When truncating, we preserve: signature > closing > references > main content. The Cherokee signature is our identity marker.

4. **Topic Detection:** The keyword-based detection is intentionally simple. Future enhancement could use the LLM for semantic topic classification.

5. **Character Limits:** Moltbook comments are 2000 chars, posts are 10000. The synthesizer defaults to comment length but accepts custom limits.

---

**For Seven Generations**
ᏣᎳᎩᏱ - Cherokee AI Federation

"""
Filler Messages Generator for Cherokee AI Federation
Implements John Wang's Assembled pattern for latency mitigation
"""
import random
import time
from typing import Optional
import asyncio


class FillerMessageGenerator:
    """
    Generates context-aware filler messages during LLM processing.
    """

    IMMEDIATE_FILLERS = [
        "Let me think about that...",
        "Good question, let me analyze this...",
        "I'm working on that for you...",
        "One moment while I consider this...",
    ]

    PROCESSING_FILLERS = {
        "research": [
            "I'm researching the details...",
            "Gathering relevant information...",
            "Looking through the data...",
        ],
        "code_generation": [
            "Writing the code now...",
            "Implementing the solution...",
            "Building the function...",
        ],
        "reasoning": [
            "Thinking through the logic...",
            "Analyzing the implications...",
            "Working through the reasoning...",
        ],
        "summarization": [
            "Condensing the key points...",
            "Identifying the main ideas...",
            "Creating your summary...",
        ],
        "default": [
            "Still working on it...",
            "Processing your request...",
            "Almost there...",
        ]
    }

    NEAR_COMPLETE_FILLERS = [
        "Almost done...",
        "Finishing up now...",
        "Just a moment more...",
        "Wrapping up my response...",
    ]

    def __init__(self, task_type: str = "default"):
        self.task_type = task_type
        self.start_time = time.time()
        self.messages_sent = 0

    def get_immediate_filler(self) -> str:
        """Get an immediate acknowledgment message."""
        return random.choice(self.IMMEDIATE_FILLERS)

    def get_processing_filler(self, elapsed_seconds: float) -> str:
        """Get a filler appropriate for the processing stage."""
        if elapsed_seconds < 2:
            return self.get_immediate_filler()
        elif elapsed_seconds < 10:
            fillers = self.PROCESSING_FILLERS.get(
                self.task_type,
                self.PROCESSING_FILLERS["default"]
            )
            return random.choice(fillers)
        else:
            return random.choice(self.NEAR_COMPLETE_FILLERS)

    def get_next_filler(self) -> Optional[str]:
        """Get the next filler message based on elapsed time."""
        elapsed = time.time() - self.start_time
        self.messages_sent += 1

        # Avoid too many fillers
        if self.messages_sent > 5:
            return None

        return self.get_processing_filler(elapsed)


class StreamingFillerHandler:
    """
    Manages filler messages for streaming responses.
    """

    def __init__(self, task_type: str = "default"):
        self.generator = FillerMessageGenerator(task_type)
        self.filler_interval = 3.0
        self.stop_event = asyncio.Event()

    async def start_filler_stream(self, send_callback):
        """Start sending filler messages until stopped."""
        await send_callback(self.generator.get_immediate_filler())

        while not self.stop_event.is_set():
            try:
                await asyncio.wait_for(
                    self.stop_event.wait(),
                    timeout=self.filler_interval
                )
            except asyncio.TimeoutError:
                filler = self.generator.get_next_filler()
                if filler:
                    await send_callback(filler)
                else:
                    break

    def stop(self):
        """Signal to stop sending fillers."""
        self.stop_event.set()


def classify_task_for_filler(prompt: str) -> str:
    """Classify task type for appropriate filler messages."""
    prompt_lower = prompt.lower()
    
    if any(kw in prompt_lower for kw in ['summarize', 'summary', 'tldr', 'brief']):
        return 'summarization'
    elif any(kw in prompt_lower for kw in ['code', 'implement', 'function', 'class']):
        return 'code_generation'
    elif any(kw in prompt_lower for kw in ['why', 'explain', 'reason', 'analyze']):
        return 'reasoning'
    elif any(kw in prompt_lower for kw in ['research', 'find', 'search', 'investigate']):
        return 'research'
    else:
        return 'default'

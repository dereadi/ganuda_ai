from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import time
from collections import deque

BASE_RATE = 50  # tokens per minute

@dataclass
class TokenBucket:
    """
    A dataclass representing a token bucket with a fixed capacity and refill rate.
    
    :param position: Position of the bucket in the priority order.
    :param capacity: Maximum number of tokens the bucket can hold.
    :param refill_rate: Number of tokens to add per second.
    :param current_tokens: Current number of tokens in the bucket.
    :param last_refill_time: Timestamp of the last refill operation.
    """
    position: int
    capacity: int
    refill_rate: float = field(init=False)
    current_tokens: int = field(init=False)
    last_refill_time: float = field(init=False)

    def __post_init__(self):
        self.refill_rate = BASE_RATE * (0.5 ** (self.position - 1)) / 60  # Convert minutes to seconds
        self.current_tokens = self.capacity
        self.last_refill_time = time.time()

    def refill(self) -> None:
        """Refill the token bucket based on the elapsed time since the last refill."""
        now = time.time()
        elapsed = now - self.last_refill_time
        self.current_tokens += elapsed * self.refill_rate
        self.current_tokens = min(self.current_tokens, self.capacity)
        self.last_refill_time = now

    def consume(self, tokens: int) -> bool:
        """
        Consume tokens from the bucket if available.
        
        :param tokens: Number of tokens to consume.
        :return: True if tokens were consumed, False otherwise.
        """
        self.refill()
        if self.current_tokens >= tokens:
            self.current_tokens -= tokens
            return True
        return False

    def promote(self, new_position: int) -> None:
        """Promote the bucket to a new position and recalculate the refill rate."""
        self.position = new_position
        self.refill_rate = BASE_RATE * (0.5 ** (self.position - 1)) / 60  # Convert minutes to seconds

    def demote(self, new_position: int) -> None:
        """Demote the bucket to a new position and recalculate the refill rate."""
        self.promote(new_position)


class GraduatedPriorityManager:
    """
    A class managing tasks with different priorities using multiple token buckets.
    
    :param buckets: Dictionary mapping task_ids to their respective TokenBucket instances.
    :param position_order: List of task_ids ordered by their priority positions.
    """
    def __init__(self):
        self.buckets: Dict[int, TokenBucket] = {}
        self.position_order: List[int] = []

    def add_task(self, task_id: int, worker_name: str) -> int:
        """
        Add a regular task to the queue with the specified priority.
        
        :param task_id: The ID of the task to be added.
        :param worker_name: Name of the worker associated with the task.
        :return: The position of the added task.
        """
        position = len(self.position_order) + 1
        self.buckets[task_id] = TokenBucket(position=position, capacity=BASE_RATE)
        self.position_order.append(task_id)
        return position

    def add_urgent_task(self, task_id: int, worker_name: str) -> None:
        """
        Add an urgent task to the front of the queue with the highest priority.
        
        :param task_id: The ID of the urgent task to be added.
        :param worker_name: Name of the worker associated with the task.
        """
        if task_id in self.buckets:
            self.complete_task(task_id)  # Remove the task if it already exists
        self.buckets[task_id] = TokenBucket(position=1, capacity=BASE_RATE)
        self.position_order.insert(0, task_id)
        self._reorder_buckets()

    def complete_task(self, task_id: int) -> List[int]:
        """
        Complete the task with the given task_id and promote all tasks below it.
        
        :param task_id: The ID of the completed task.
        :return: List of task_ids that were promoted.
        """
        if task_id in self.buckets:
            self.position_order.remove(task_id)
            del self.buckets[task_id]
            promoted_tasks = self._reorder_buckets()
            return promoted_tasks
        return []

    def _reorder_buckets(self) -> List[int]:
        """Reorder the buckets and promote tasks accordingly."""
        promoted_tasks = []
        for i, task_id in enumerate(self.position_order):
            new_position = i + 1
            if self.buckets[task_id].position != new_position:
                self.buckets[task_id].promote(new_position)
                promoted_tasks.append(task_id)
        return promoted_tasks

    def get_status(self) -> List[Dict[str, Any]]:
        """
        Get the current status of all tasks.
        
        :return: A list of dictionaries with task details.
        """
        return [
            {
                'task_id': task_id,
                'position': self.buckets[task_id].position,
                'capacity_pct': (self.buckets[task_id].current_tokens / self.buckets[task_id].capacity) * 100
            }
            for task_id in self.position_order
        ]
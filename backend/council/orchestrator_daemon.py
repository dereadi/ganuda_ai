import logging
from typing import List, Dict, Any
from ganuda.backend.council.models import CouncilMember, Task, Decision
from ganuda.backend.council.communicator import Communicator
from ganuda.backend.council.scheduler import Scheduler
from ganuda.backend.council.database import Database

logger = logging.getLogger(__name__)

class OrchestratorDaemon:
    def __init__(self, communicator: Communicator, scheduler: Scheduler, database: Database):
        self.communicator = communicator
        self.scheduler = scheduler
        self.database = database

    def start(self):
        logger.info("Orchestrator Daemon started.")
        while True:
            tasks = self.scheduler.get_next_tasks()
            if not tasks:
                logger.debug("No tasks to process. Sleeping.")
                continue

            for task in tasks:
                self.process_task(task)

    def process_task(self, task: Task):
        logger.info(f"Processing task: {task.id}")
        council_members = self.database.get_council_members_for_task(task)
        decisions = self.send_task_to_council_members(task, council_members)
        final_decision = self.aggregate_decisions(decisions)
        self.execute_final_decision(final_decision)

    def send_task_to_council_members(self, task: Task, council_members: List[CouncilMember]) -> List[Decision]:
        decisions = []
        for member in council_members:
            decision = self.communicator.send_task_to_member(task, member)
            decisions.append(decision)
        return decisions

    def aggregate_decisions(self, decisions: List[Decision]) -> Decision:
        # Simple majority voting for now
        votes = {}
        for decision in decisions:
            if decision.outcome in votes:
                votes[decision.outcome] += 1
            else:
                votes[decision.outcome] = 1

        final_outcome = max(votes, key=votes.get)
        return Decision(outcome=final_outcome, reasoning="Majority vote")

    def execute_final_decision(self, decision: Decision):
        logger.info(f"Executing final decision: {decision.outcome}")
        # Placeholder for actual execution logic
        pass
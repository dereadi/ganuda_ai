from celery import shared_task
from .models import CouncilTask, TaskStatus
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

@shared_task
def create_council_task(task_data: dict) -> None:
    """
    Create a new council task.
    
    :param task_data: Dictionary containing task details.
    """
    with transaction.atomic():
        task = CouncilTask.objects.create(**task_data)
        logger.info(f"Task created: {task.id}")

@shared_task
def update_council_task_status(task_id: int, new_status: str) -> None:
    """
    Update the status of an existing council task.
    
    :param task_id: ID of the task to update.
    :param new_status: New status for the task.
    """
    try:
        task = CouncilTask.objects.get(id=task_id)
        task.status = new_status
        task.save()
        logger.info(f"Task status updated: {task.id} -> {new_status}")
    except CouncilTask.DoesNotExist:
        logger.error(f"Task not found: {task_id}")

@shared_task
def delete_council_task(task_id: int) -> None:
    """
    Delete an existing council task.
    
    :param task_id: ID of the task to delete.
    """
    try:
        task = CouncilTask.objects.get(id=task_id)
        task.delete()
        logger.info(f"Task deleted: {task_id}")
    except CouncilTask.DoesNotExist:
        logger.error(f"Task not found: {task_id}")

@shared_task
def process_council_task(task_id: int) -> None:
    """
    Process a council task based on its current status.
    
    :param task_id: ID of the task to process.
    """
    try:
        task = CouncilTask.objects.get(id=task_id)
        if task.status == TaskStatus.PENDING:
            # Example processing logic
            task.status = TaskStatus.IN_PROGRESS
            task.save()
            logger.info(f"Task processing started: {task_id}")
        elif task.status == TaskStatus.IN_PROGRESS:
            # Additional processing logic
            task.status = TaskStatus.COMPLETED
            task.save()
            logger.info(f"Task processing completed: {task_id}")
        else:
            logger.warning(f"Task already processed: {task_id}")
    except CouncilTask.DoesNotExist:
        logger.error(f"Task not found: {task_id}")
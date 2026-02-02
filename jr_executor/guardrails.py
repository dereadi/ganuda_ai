import logging
import psycopg2
from typing import Dict, Optional

class Guardrails:
    """
    Class to manage file size reduction guardrails.
    """

    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config

    def check_file_size_reduction(self, original_size: int, new_size: int) -> bool:
        """
        Check if the file size reduction exceeds the allowed threshold (50%).

        :param original_size: Original size of the file in lines.
        :param new_size: New size of the file in lines.
        :return: True if the reduction is within the allowed threshold, False otherwise.
        """
        if original_size == 0:
            return True  # Avoid division by zero if the original file is empty
        reduction_percentage = ((original_size - new_size) / original_size) * 100
        return reduction_percentage <= 50

    def log_large_reduction(self, task_id: str, step_number: int, target_file: str, original_size: int, new_size: int) -> None:
        """
        Log details of a large file size reduction attempt.

        :param task_id: Identifier for the task.
        :param step_number: Step number within the task.
        :param target_file: Path to the target file.
        :param original_size: Original size of the file in lines.
        :param new_size: New size of the file in lines.
        """
        try:
            reduction_percentage = ((original_size - new_size) / original_size) * 100
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO jr_exploration_log (task_id, step_number, target_file, original_size, new_size, reduction_percentage, log_message) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (task_id, step_number, target_file, original_size, new_size, reduction_percentage,
                 f"Large reduction attempt: {reduction_percentage:.2f}%")
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logging.getLogger(__name__).warning(f"Failed to log large reduction: {e}")
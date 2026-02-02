import os
import shutil
import logging
from typing import Optional

class BackupManager:
    """
    Utility class to handle file backups before operations.
    """

    def __init__(self, backup_dir: str):
        """
        Initialize the BackupManager with a directory to store backups.

        :param backup_dir: Directory path where backups will be stored.
        """
        self.backup_dir = backup_dir
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

    def create_backup(self, file_path: str) -> Optional[str]:
        """
        Create a backup of the specified file.

        :param file_path: Path to the file to be backed up.
        :return: Path to the backup file, or None if the backup failed.
        """
        if not os.path.exists(file_path):
            logging.warning(f"File does not exist: {file_path}")
            return None

        try:
            # Generate a backup file path
            file_name = os.path.basename(file_path)
            backup_file_path = os.path.join(self.backup_dir, file_name)
            # Copy the file to the backup directory
            shutil.copy2(file_path, backup_file_path)
            logging.info(f"Backup created: {backup_file_path}")
            return backup_file_path
        except Exception as e:
            logging.error(f"Failed to create backup for {file_path}: {e}")
            return None

    def restore_from_backup(self, backup_file_path: str, original_file_path: str) -> bool:
        """
        Restore a file from a backup.

        :param backup_file_path: Path to the backup file.
        :param original_file_path: Path to the original file to be restored.
        :return: True if the restoration was successful, False otherwise.
        """
        if not os.path.exists(backup_file_path):
            logging.warning(f"Backup file does not exist: {backup_file_path}")
            return False

        try:
            # Copy the backup file back to the original file path
            shutil.copy2(backup_file_path, original_file_path)
            logging.info(f"Restored from backup: {original_file_path}")
            return True
        except Exception as e:
            logging.error(f"Failed to restore from backup {backup_file_path} to {original_file_path}: {e}")
            return False
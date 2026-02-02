import os
import hashlib
import logging
from typing import Dict, Optional

def validate_task_parameters(task_params: Dict) -> bool:
    """
    Validate the task parameters to ensure they specify an edit operation and not a replacement.
    
    :param task_params: Dictionary containing task parameters
    :return: True if parameters are valid, False otherwise
    """
    if 'operation' not in task_params:
        logging.warning("Task parameters missing 'operation' key.")
        return False
    
    if task_params['operation'] != 'edit':
        logging.warning("Task operation is not 'edit'. This might lead to unintended data loss.")
        return False
    
    return True

def validate_file_integrity(original_file_path: str, modified_file_path: str) -> bool:
    """
    Validate the integrity of the modified file compared to the original file.
    Ensure that the modified file is not significantly smaller than the original file.
    
    :param original_file_path: Path to the original file
    :param modified_file_path: Path to the modified file
    :return: True if file integrity is maintained, False otherwise
    """
    if not os.path.exists(original_file_path):
        logging.error(f"Original file does not exist: {original_file_path}")
        return False
    
    if not os.path.exists(modified_file_path):
        logging.error(f"Modified file does not exist: {modified_file_path}")
        return False
    
    original_size = os.path.getsize(original_file_path)
    modified_size = os.path.getsize(modified_file_path)
    
    if modified_size < original_size * 0.5:
        logging.warning(f"Modified file size is less than 50% of the original file size. Original: {original_size}, Modified: {modified_size}")
        return False
    
    return True

def calculate_file_hash(file_path: str) -> Optional[str]:
    """
    Calculate the SHA-256 hash of a file.
    
    :param file_path: Path to the file
    :return: Hexadecimal hash of the file, or None if file does not exist
    """
    if not os.path.exists(file_path):
        logging.error(f"File does not exist: {file_path}")
        return None
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()
import pandas as pd
from typing import List, Dict
from ganuda.backend.utils import validate_data, log_error

def ingest_spectral_data(file_path: str) -> Dict[str, pd.DataFrame]:
    """
    Ingests spectral data from a given file path and returns a dictionary of DataFrames.
    
    :param file_path: Path to the spectral data file.
    :return: Dictionary with keys as data types and values as DataFrames.
    """
    try:
        # Read the spectral data file
        data = pd.read_csv(file_path)
        
        # Validate the data
        if not validate_data(data):
            raise ValueError("Data validation failed")
        
        # Process the data into different categories
        processed_data = process_data(data)
        
        return processed_data
    except Exception as e:
        log_error(f"Error ingesting spectral data: {e}")
        return {}

def process_data(data: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Processes the raw spectral data into different categories.
    
    :param data: DataFrame containing the raw spectral data.
    :return: Dictionary with keys as data types and values as DataFrames.
    """
    # Example processing: split data into different categories
    # This is a placeholder for actual processing logic
    category_1 = data[data['category'] == '1']
    category_2 = data[data['category'] == '2']
    
    return {
        'category_1': category_1,
        'category_2': category_2
    }
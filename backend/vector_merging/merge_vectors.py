import numpy as np
from typing import List

def merge_vectors(vectors: List[np.ndarray]) -> np.ndarray:
    """
    Merges a list of vectors into a single vector by averaging their values.
    
    Args:
        vectors (List[np.ndarray]): A list of numpy arrays representing vectors.
        
    Returns:
        np.ndarray: A single merged vector.
    """
    if not vectors:
        raise ValueError("The list of vectors cannot be empty.")
    
    # Ensure all vectors have the same shape
    shapes = {v.shape for v in vectors}
    if len(shapes) > 1:
        raise ValueError("All vectors must have the same shape.")
    
    # Average the vectors
    merged_vector = np.mean(vectors, axis=0)
    return merged_vector
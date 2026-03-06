import pandas as pd
from typing import List, Dict, Any
from ganuda.backend.data_models import ResearchData, ProcessedData

class DataProcessor:
    def __init__(self, data: ResearchData):
        self.data = data

    def process_data(self) -> ProcessedData:
        """
        Process the research data to include new features.
        """
        # Convert raw data to DataFrame
        df = pd.DataFrame(self.data.raw_data)

        # Apply new research features
        df = self._add_research_features(df)

        # Convert DataFrame back to dictionary
        processed_data = df.to_dict(orient='records')

        return ProcessedData(processed_data=processed_data)

    def _add_research_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add new research features to the DataFrame.
        """
        # Example feature: Calculate average value
        df['average_value'] = df.mean(axis=1)

        # Example feature: Identify outliers
        df['is_outlier'] = (df - df.mean()).abs() > 3 * df.std()

        # Add more features as needed
        return df
import os
import sys
import logging
from datetime import datetime
from typing import List, Dict, Any

# Assuming these are custom modules from the project
from ganuda.core.signal import SignalProcessor
from ganuda.core.pipeline import Pipeline
from ganuda.core.storage import ThermalMemoryStorage
from ganuda.core.council import CouncilVote
from ganuda.utils import config, logger

# Setup logging
logger = logging.getLogger(__name__)

class DeerSignalPipeline(Pipeline):
    def __init__(self, config_path: str):
        super().__init__(config_path)
        self.signal_processor = SignalProcessor()
        self.storage = ThermalMemoryStorage(config_path)
        self.council_vote = CouncilVote(config_path)

    def process_signal(self, signal: Dict[str, Any]) -> None:
        """
        Process a single deer signal.
        
        :param signal: A dictionary containing the signal data.
        """
        processed_signal = self.signal_processor.process(signal)
        self.storage.store(processed_signal)
        self.council_vote.submit_vote(processed_signal)

    def run(self, signals: List[Dict[str, Any]]) -> None:
        """
        Run the pipeline on a list of signals.
        
        :param signals: A list of dictionaries containing signal data.
        """
        for signal in signals:
            self.process_signal(signal)

def main():
    config_path = os.getenv('GANUDA_CONFIG_PATH', 'default_config.yaml')
    pipeline = DeerSignalPipeline(config_path)
    
    # Example signals (in a real scenario, these would come from an external source)
    example_signals = [
        {"id": 1, "timestamp": datetime.now().isoformat(), "data": {"location": "forest", "activity": "feeding"}},
        {"id": 2, "timestamp": datetime.now().isoformat(), "data": {"location": "river", "activity": "drinking"}}
    ]
    
    pipeline.run(example_signals)

if __name__ == "__main__":
    main()
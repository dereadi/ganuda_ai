import os
import json
from typing import List, Dict, Any
from capybara_model import CapybaraModel
from qwen_model import QwenModel
from llama_model import LlamaModel
from evaluation_metrics import evaluate_model

class EvalHarness:
    def __init__(self, models: List[str], tasks: List[str]):
        """
        Initialize the evaluation harness with a list of models and tasks.

        :param models: List of model names to evaluate
        :param tasks: List of tasks to evaluate the models on
        """
        self.models = models
        self.tasks = tasks
        self.results: Dict[str, Dict[str, float]] = {}

    def load_models(self) -> None:
        """
        Load the specified models.
        """
        self.loaded_models = {}
        for model_name in self.models:
            if model_name == 'Capybara':
                self.loaded_models[model_name] = CapybaraModel()
            elif model_name == 'Qwen2.5-72B':
                self.loaded_models[model_name] = QwenModel()
            elif model_name == 'Llama-3.3-70B':
                self.loaded_models[model_name] = LlamaModel()
            else:
                raise ValueError(f"Unknown model: {model_name}")

    def run_evaluation(self) -> None:
        """
        Run the evaluation for each model on each task.
        """
        for model_name, model in self.loaded_models.items():
            self.results[model_name] = {}
            for task in self.tasks:
                score = evaluate_model(model, task)
                self.results[model_name][task] = score

    def save_results(self, output_path: str) -> None:
        """
        Save the evaluation results to a JSON file.

        :param output_path: Path to save the results
        """
        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=4)

def main():
    models = ['Capybara', 'Qwen2.5-72B', 'Llama-3.3-70B']
    tasks = ['council_quality', 'jr_task_completion', 'thermal_memory_retrieval_accuracy']
    
    harness = EvalHarness(models, tasks)
    harness.load_models()
    harness.run_evaluation()
    harness.save_results('evaluation_results.json')

if __name__ == "__main__":
    main()
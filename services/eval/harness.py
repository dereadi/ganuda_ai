# /ganuda/services/eval/harness.py

import os
from typing import List, Dict, Any
import requests
from ganuda.services.models import Model
from ganuda.services.tasks import Task
from ganuda.services.metrics import Metric

class EvalHarness:
    def __init__(self, models: List[Model], tasks: List[Task], metrics: List[Metric]):
        """
        Initialize the evaluation harness.

        :param models: List of models to evaluate.
        :param tasks: List of tasks to perform.
        :param metrics: List of metrics to measure performance.
        """
        self.models = models
        self.tasks = tasks
        self.metrics = metrics
        self.results: Dict[str, Dict[str, Any]] = {}

    def run(self):
        """
        Run the evaluation harness.
        """
        for model in self.models:
            model_results = {}
            for task in self.tasks:
                task_result = task.execute(model)
                for metric in self.metrics:
                    score = metric.evaluate(task_result)
                    model_results[f"{task.name}_{metric.name}"] = score
            self.results[model.name] = model_results

    def report(self):
        """
        Generate a report of the evaluation results.
        """
        for model, results in self.results.items():
            print(f"Model: {model}")
            for task_metric, score in results.items():
                print(f"  {task_metric}: {score}")

    def save_results(self, path: str):
        """
        Save the evaluation results to a file.

        :param path: Path to save the results.
        """
        with open(path, 'w') as f:
            for model, results in self.results.items():
                f.write(f"Model: {model}\n")
                for task_metric, score in results.items():
                    f.write(f"  {task_metric}: {score}\n")

# Example usage
if __name__ == "__main__":
    # Define models, tasks, and metrics
    models = [
        Model(name="Capybara", endpoint="http://capybara:8000"),
        Model(name="Qwen2.5-72B", endpoint="http://qwen:8000"),
        Model(name="Llama-3.3-70B", endpoint="http://llama:8000")
    ]
    tasks = [
        Task(name="Council Quality", endpoint="http://council:8000/quality"),
        Task(name="Jr Task Completion", endpoint="http://jr:8000/completion"),
        Task(name="Thermal Memory Retrieval", endpoint="http://memory:8000/retrieval")
    ]
    metrics = [
        Metric(name="Accuracy", func=lambda x: x['accuracy']),
        Metric(name="Latency", func=lambda x: x['latency'])
    ]

    # Create and run the evaluation harness
    harness = EvalHarness(models, tasks, metrics)
    harness.run()
    harness.report()
    harness.save_results("eval_results.txt")
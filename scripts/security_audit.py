import os
import subprocess
import requests
from typing import List, Dict, Any

class SecurityAudit:
    def __init__(self, nodes: List[str], models: List[str]):
        self.nodes = nodes
        self.models = models
        self.audit_results: Dict[str, Any] = {}

    def run_audit(self):
        for node in self.nodes:
            for model in self.models:
                if node != model:  # Ensure cross-substrate validation
                    self.audit_node(node, model)
        self.report_results()

    def audit_node(self, node: str, model: str):
        print(f"Auditing {node} using {model}")
        # Example command: python3 /path/to/audit_script.py --node <node> --model <model>
        command = f"python3 /ganuda/scripts/audit_script.py --node {node} --model {model}"
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        self.audit_results[f"{node}_{model}"] = result.stdout

    def report_results(self):
        with open("/ganuda/reports/security_audit_report.txt", "w") as report_file:
            for key, value in self.audit_results.items():
                report_file.write(f"Node: {key}\n")
                report_file.write(f"Result:\n{value}\n")
                report_file.write("-" * 80 + "\n")

def main():
    nodes = ["owlfin", "eaglefin", "bluefin", "sasass", "sasass2"]
    models = ["Qwen2.5-72B", "Llama-3.3-70B", "Capybara"]
    auditor = SecurityAudit(nodes, models)
    auditor.run_audit()

if __name__ == "__main__":
    main()
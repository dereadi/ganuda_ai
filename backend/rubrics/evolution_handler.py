from typing import List, Dict, Any
import json
from ganuda.backend.rubrics.models import Rubric, EvolutionRule  # Assuming these models exist

class EvolutionHandler:
    def __init__(self, rubric: Rubric):
        self.rubric = rubric

    def apply_evolution_rules(self) -> None:
        """
        Apply evolution rules to the rubric.
        """
        for rule in self.rubric.evolution_rules:
            if self._should_apply_rule(rule):
                self._apply_rule(rule)

    def _should_apply_rule(self, rule: EvolutionRule) -> bool:
        """
        Determine if a rule should be applied based on conditions.
        """
        return self._check_conditions(rule.conditions)

    def _apply_rule(self, rule: EvolutionRule) -> None:
        """
        Apply a single evolution rule to the rubric.
        """
        for action in rule.actions:
            self._execute_action(action)

    def _check_conditions(self, conditions: List[Dict[str, Any]]) -> bool:
        """
        Check if all conditions are met.
        """
        for condition in conditions:
            if not self._evaluate_condition(condition):
                return False
        return True

    def _evaluate_condition(self, condition: Dict[str, Any]) -> bool:
        """
        Evaluate a single condition.
        """
        # Example condition: {"field": "score", "operator": ">", "value": 80}
        field = condition.get("field")
        operator = condition.get("operator")
        value = condition.get("value")

        if field not in self.rubric.data:
            return False

        current_value = self.rubric.data[field]

        if operator == ">":
            return current_value > value
        elif operator == "<":
            return current_value < value
        elif operator == "==":
            return current_value == value
        elif operator == "!=":
            return current_value != value
        else:
            raise ValueError(f"Unsupported operator: {operator}")

    def _execute_action(self, action: Dict[str, Any]) -> None:
        """
        Execute a single action.
        """
        # Example action: {"field": "status", "method": "set", "value": "approved"}
        field = action.get("field")
        method = action.get("method")
        value = action.get("value")

        if field not in self.rubric.data:
            raise KeyError(f"Field not found: {field}")

        if method == "set":
            self.rubric.data[field] = value
        elif method == "increment":
            self.rubric.data[field] += value
        elif method == "decrement":
            self.rubric.data[field] -= value
        else:
            raise ValueError(f"Unsupported method: {method}")
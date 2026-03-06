from typing import List, Dict, Any
from .evolution_handler import EvolutionHandler
from .rubric import Rubric

class RubricManager:
    def __init__(self, rubrics: List[Rubric]):
        self.rubrics = rubrics
        self.evolution_handler = EvolutionHandler()

    def add_rubric(self, rubric: Rubric) -> None:
        """
        Adds a new rubric to the manager.
        """
        self.rubrics.append(rubric)

    def remove_rubric(self, rubric_id: str) -> bool:
        """
        Removes a rubric from the manager by ID.
        Returns True if the rubric was found and removed, False otherwise.
        """
        for i, rubric in enumerate(self.rubrics):
            if rubric.id == rubric_id:
                del self.rubrics[i]
                return True
        return False

    def get_rubric(self, rubric_id: str) -> Rubric:
        """
        Retrieves a rubric by ID.
        Raises ValueError if the rubric is not found.
        """
        for rubric in self.rubrics:
            if rubric.id == rubric_id:
                return rubric
        raise ValueError(f"Rubric with ID {rubric_id} not found")

    def evolve_rubrics(self) -> None:
        """
        Evolves all rubrics using the evolution handler.
        """
        for rubric in self.rubrics:
            self.evolution_handler.evolve(rubric)
"""Base department interface.

Phase 0: implemented as simple function calls.
Phase 2+: can be replaced with LangGraph agent subgraphs.

Every department:
1. Takes a ProductionJob and its ProductionStep
2. Does its work (calls external tool)
3. Returns a StepResult with output path and metadata
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from studio_orchestrator.models import ProductionJob, ProductionStep, StepResult


class Department(ABC):
    """Base interface for all production departments."""

    @abstractmethod
    def process(self, job: ProductionJob, step: ProductionStep, context: dict) -> StepResult:
        """Execute this department's work for a production step.

        Args:
            job: The production job being processed
            step: The specific step to execute
            context: Shared context dict with config, artifacts dir, prior step outputs, etc.

        Returns:
            StepResult with success/failure, output path, and metadata
        """
        ...

    @abstractmethod
    def estimate_cost(self, job: ProductionJob) -> int:
        """Estimate cost in cents for this step."""
        ...

    @abstractmethod
    def validate_output(self, result: StepResult) -> bool:
        """Verify the output meets quality standards."""
        ...

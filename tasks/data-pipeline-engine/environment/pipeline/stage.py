"""Base stage class for pipeline processing."""

from abc import ABC, abstractmethod


class Stage(ABC):
    """Abstract base class for pipeline stages.

    Each stage processes a list of records and returns a new list.
    """

    def __init__(self, name=None):
        self.name = name or self.__class__.__name__

    @abstractmethod
    def process(self, records, context):
        """Process a list of records.

        Args:
            records: List of record dicts to process.
            context: PipelineContext with shared state.

        Returns:
            A new list of processed records.
        """

    def __repr__(self):
        return f"{self.__class__.__name__}(name={self.name!r})"

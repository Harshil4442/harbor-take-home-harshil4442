"""Custom exception hierarchy for the data pipeline."""


class PipelineError(Exception):
    """Base exception for all pipeline errors."""

    def __init__(self, message, record=None, stage=None):
        super().__init__(message)
        self.record = record
        self.stage = stage


class ValidationError(PipelineError):
    """Raised when a record fails schema validation."""

    def __init__(
        self, message, field=None, expected_type=None,
        actual_value=None, record=None, stage=None,
    ):
        super().__init__(message, record=record, stage=stage)
        self.field = field
        self.expected_type = expected_type
        self.actual_value = actual_value


class TransformError(PipelineError):
    """Raised when a transformation fails."""

    def __init__(
        self, message, field=None, expression=None,
        record=None, stage=None,
    ):
        super().__init__(message, record=record, stage=stage)
        self.field = field
        self.expression = expression


class AggregationError(PipelineError):
    """Raised when an aggregation operation fails."""



class FilterError(PipelineError):
    """Raised when a filter predicate evaluation fails."""



class ConfigurationError(PipelineError):
    """Raised when pipeline configuration is invalid."""

"""Data Pipeline Engine: a configurable record processing framework."""

from pipeline.engine import Pipeline
from pipeline.config import (
    PipelineBuilder,
    build_pipeline_from_config,
)
from pipeline.context import PipelineContext, PipelineResult
from pipeline.stage import Stage
from pipeline.errors import (
    PipelineError,
    ValidationError,
    TransformError,
    AggregationError,
    FilterError,
    ConfigurationError,
)
from pipeline.stages import (
    ValidationStage,
    TransformStage,
    FilterStage,
    AggregateStage,
    OutputStage,
)

__all__ = [
    "Pipeline",
    "PipelineBuilder",
    "build_pipeline_from_config",
    "PipelineContext",
    "PipelineResult",
    "Stage",
    "PipelineError",
    "ValidationError",
    "TransformError",
    "AggregationError",
    "FilterError",
    "ConfigurationError",
    "ValidationStage",
    "TransformStage",
    "FilterStage",
    "AggregateStage",
    "OutputStage",
]

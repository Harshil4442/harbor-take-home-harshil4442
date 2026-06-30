"""Pipeline configuration and builder."""

from pipeline.engine import Pipeline
from pipeline.stages.validate import ValidationStage
from pipeline.stages.transform import TransformStage
from pipeline.stages.filter import FilterStage
from pipeline.stages.aggregate import AggregateStage
from pipeline.stages.output import OutputStage
from pipeline.errors import ConfigurationError


class PipelineBuilder:
    """Build a Pipeline step by step."""

    def __init__(self, error_strategy="fail-fast"):
        self._stages = []
        self._error_strategy = error_strategy

    def add_validation(
        self, schema, coerce=False, error_strategy=None,
    ):
        """Add a validation stage."""
        strategy = error_strategy or self._error_strategy
        self._stages.append(
            ValidationStage(
                schema, coerce=coerce,
                error_strategy=strategy,
            )
        )
        return self

    def add_transform(self, transforms, error_strategy=None):
        """Add a transformation stage."""
        strategy = error_strategy or self._error_strategy
        self._stages.append(
            TransformStage(
                transforms, error_strategy=strategy,
            )
        )
        return self

    def add_filter(self, predicate):
        """Add a filter stage."""
        self._stages.append(FilterStage(predicate))
        return self

    def add_aggregation(self, group_field, aggregations):
        """Add an aggregation stage."""
        self._stages.append(
            AggregateStage(group_field, aggregations)
        )
        return self

    def add_output(self, fields=None, exclude=None):
        """Add an output stage."""
        self._stages.append(
            OutputStage(fields=fields, exclude=exclude)
        )
        return self

    def build(self):
        """Build and return the Pipeline."""
        if not self._stages:
            raise ConfigurationError(
                "Pipeline must have at least one stage"
            )
        return Pipeline(
            stages=self._stages,
            error_strategy=self._error_strategy,
        )


def build_pipeline_from_config(config):
    """Build a Pipeline from a configuration dict."""
    error_strategy = config.get("error_strategy", "fail-fast")
    builder = PipelineBuilder(error_strategy=error_strategy)

    for stage_config in config.get("stages", []):
        stage_type = stage_config.get("type")

        if stage_type == "validate":
            builder.add_validation(
                schema=stage_config["schema"],
                coerce=stage_config.get("coerce", False),
                error_strategy=stage_config.get(
                    "error_strategy"
                ),
            )
        elif stage_type == "transform":
            builder.add_transform(
                transforms=stage_config["transforms"],
                error_strategy=stage_config.get(
                    "error_strategy"
                ),
            )
        elif stage_type == "filter":
            builder.add_filter(
                predicate=stage_config["predicate"],
            )
        elif stage_type == "aggregate":
            builder.add_aggregation(
                group_field=stage_config["group_field"],
                aggregations=stage_config["aggregations"],
            )
        elif stage_type == "output":
            builder.add_output(
                fields=stage_config.get("fields"),
                exclude=stage_config.get("exclude"),
            )
        else:
            raise ConfigurationError(
                f"Unknown stage type: {stage_type}"
            )

    return builder.build()

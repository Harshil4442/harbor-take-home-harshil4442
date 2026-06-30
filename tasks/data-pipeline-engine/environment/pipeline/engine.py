"""Pipeline engine: orchestrates record processing through stages."""

from pipeline.context import PipelineContext, PipelineResult
from pipeline.errors import PipelineError


class Pipeline:
    """A configurable data processing pipeline.

    Runs records through a sequence of stages, with configurable
    error handling.
    """

    def __init__(self, stages, error_strategy="fail-fast"):
        self.stages = stages
        self.error_strategy = error_strategy

    def run(self, records):
        """Execute the pipeline on a list of records.

        Returns a PipelineResult with output records, quarantine,
        and metrics.
        """
        context = PipelineContext(
            error_strategy=self.error_strategy,
        )
        current = list(records)

        for stage in self.stages:
            try:
                current = stage.process(current, context)
            except PipelineError:
                raise
            except Exception as exc:
                raise PipelineError(
                    f"Unexpected error in stage "
                    f"'{stage.name}': {exc}",
                    stage=stage.name,
                ) from exc

        return PipelineResult(
            records=current,
            quarantine=context.quarantine,
            metrics=context.metrics,
        )

    def __repr__(self):
        stage_names = [s.name for s in self.stages]
        return f"Pipeline(stages={stage_names})"

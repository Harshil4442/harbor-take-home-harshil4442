"""Pipeline execution context and result types."""


class PipelineContext:
    """Shared state during pipeline execution."""

    def __init__(self, error_strategy="fail-fast"):
        self.error_strategy = error_strategy
        self.quarantine = []
        self.metrics = {
            "processed": 0,
            "failed": 0,
            "skipped": 0,
            "quarantined": 0,
        }
        self.stage_results = {}

    def record_processed(self):
        """Increment the processed counter."""
        self.metrics["processed"] += 1


class PipelineResult:
    """Result of a pipeline run."""

    def __init__(self, records, quarantine, metrics):
        self.records = records
        self.quarantine = quarantine
        self.metrics = dict(metrics)

    def __repr__(self):
        return (
            f"PipelineResult(records={len(self.records)}, "
            f"quarantined={len(self.quarantine)}, "
            f"metrics={self.metrics})"
        )

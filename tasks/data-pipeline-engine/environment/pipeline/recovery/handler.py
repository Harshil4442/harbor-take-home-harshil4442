"""Error recovery handlers for pipeline stages."""


class ErrorHandler:
    """Dispatches error handling to the appropriate strategy."""

    def __init__(self, strategy="fail-fast"):
        if strategy not in ("fail-fast", "skip", "quarantine"):
            raise ValueError(
                f"Unknown error strategy: {strategy}"
            )
        self.strategy = strategy
        self._handlers = {
            "fail-fast": FailFastHandler(),
            "skip": SkipHandler(),
            "quarantine": QuarantineHandler(),
        }

    def handle(self, error, record, context):
        """Handle an error using the configured strategy."""
        handler = self._handlers[self.strategy]
        return handler.handle(error, record, context)


class FailFastHandler:
    """Stop the pipeline immediately on error."""

    def handle(self, error, record, context):
        """Re-raise the error to halt the pipeline."""
        context.metrics["failed"] += 1
        raise error


class SkipHandler:
    """Skip the failed record and continue processing."""

    def handle(self, error, record, context):
        """Log the error and signal to continue."""
        context.metrics["failed"] += 1
        context.metrics["skipped"] += 1
        return True


class QuarantineHandler:
    """Move failed records to quarantine and continue."""

    def handle(self, error, record, context):
        """Add to quarantine and continue processing."""
        context.metrics["failed"] += 1
        context.metrics["quarantined"] += 1
        context.quarantine.append({
            "record": record,
            "error": str(error),
            "stage": getattr(error, "stage", None),
        })
        raise error

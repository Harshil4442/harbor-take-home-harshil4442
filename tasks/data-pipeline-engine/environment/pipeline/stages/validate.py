"""Validation stage for the data pipeline."""

from pipeline.stage import Stage
from pipeline.schema.validator import SchemaValidator
from pipeline.recovery.handler import ErrorHandler
from pipeline.errors import ValidationError


class ValidationStage(Stage):
    """Validate records against a schema."""

    def __init__(
        self, schema, coerce=False,
        error_strategy="fail-fast", name=None,
    ):
        super().__init__(name=name or "validate")
        self.validator = SchemaValidator(
            schema, coerce=coerce,
        )
        self.error_handler = ErrorHandler(
            strategy=error_strategy,
        )

    def process(self, records, context):
        """Validate each record and return valid ones."""
        valid_records = []
        for record in records:
            try:
                validated = self.validator.validate(record)
                valid_records.append(validated)
                context.record_processed()
            except ValidationError as exc:
                exc.stage = self.name
                try:
                    self.error_handler.handle(
                        exc, record, context,
                    )
                except ValidationError:
                    raise
        return valid_records

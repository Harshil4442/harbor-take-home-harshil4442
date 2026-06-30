"""Transformation stage for the data pipeline."""

from pipeline.stage import Stage
from pipeline.utils.expressions import evaluate_expression
from pipeline.errors import TransformError
from pipeline.recovery.handler import ErrorHandler


class TransformStage(Stage):
    """Transform records by applying field operations."""

    def __init__(
        self, transforms, error_strategy="fail-fast",
        name=None,
    ):
        super().__init__(name=name or "transform")
        self.transforms = transforms
        self.error_handler = ErrorHandler(
            strategy=error_strategy,
        )

    def process(self, records, context):
        """Apply transforms to each record."""
        results = []
        for record in records:
            try:
                transformed = self._apply_transforms(
                    record,
                )
                results.append(transformed)
                context.record_processed()
            except TransformError as exc:
                exc.stage = self.name
                try:
                    self.error_handler.handle(
                        exc, record, context,
                    )
                except TransformError:
                    raise
        return results

    def _apply_transforms(self, record):
        """Apply all transforms to a single record."""
        result = dict(record)
        snapshot = dict(record)

        for transform in self.transforms:
            t_type = transform.get("type", "compute")

            if t_type == "rename":
                old_name = transform["from"]
                new_name = transform["to"]
                if old_name in result:
                    result[new_name] = result.pop(old_name)

            elif t_type == "set":
                result[transform["field"]] = (
                    transform["value"]
                )

            elif t_type == "compute":
                field = transform["field"]
                expr = transform["expr"]
                try:
                    value = evaluate_expression(
                        expr, snapshot,
                    )
                    result[field] = value
                except (
                    ValueError,
                    ZeroDivisionError,
                ) as exc:
                    raise TransformError(
                        f"Failed to compute field "
                        f"'{field}': {exc}",
                        field=field,
                        expression=expr,
                        record=record,
                    ) from exc

            else:
                raise TransformError(
                    f"Unknown transform type: {t_type}",
                    record=record,
                )

        return result

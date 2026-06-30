"""Aggregation stage for the data pipeline."""

from pipeline.stage import Stage
from pipeline.utils.collections import group_by


class AggregateStage(Stage):
    """Aggregate records by grouping and computing summaries."""

    def __init__(self, group_field, aggregations, name=None):
        super().__init__(name=name or "aggregate")
        self.group_field = group_field
        self.aggregations = aggregations

    def process(self, records, context):
        """Group records and compute aggregations."""
        if not records:
            return []

        groups = group_by(records, self.group_field)
        results = []
        total_count = len(records)

        for group_key, group_records in groups.items():
            result = {self.group_field: group_key}

            for agg in self.aggregations:
                field = agg["field"]
                operation = agg["operation"].lower()
                alias = agg.get(
                    "alias", f"{operation}_{field}",
                )

                values = [
                    r[field]
                    for r in group_records
                    if field in r and r[field] is not None
                ]

                if operation == "sum":
                    result[alias] = (
                        sum(values) if values else 0
                    )
                elif operation == "avg":
                    result[alias] = (
                        sum(values) / total_count
                        if values
                        else 0
                    )
                elif operation == "count":
                    result[alias] = len(values)
                elif operation == "min":
                    result[alias] = (
                        min(values) if values else None
                    )
                elif operation == "max":
                    result[alias] = (
                        max(values) if values else None
                    )
                else:
                    raise ValueError(
                        f"Unknown aggregation: "
                        f"{operation}"
                    )

            results.append(result)
            context.record_processed()

        return results

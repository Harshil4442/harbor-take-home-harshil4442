"""Output stage for the data pipeline."""

from pipeline.stage import Stage
from pipeline.utils.collections import pick, omit


class OutputStage(Stage):
    """Collect and format output records."""

    def __init__(self, fields=None, exclude=None, name=None):
        super().__init__(name=name or "output")
        self.fields = fields
        self.exclude = exclude or []

    def process(self, records, context):
        """Format output records."""
        results = []
        for record in records:
            if self.fields is not None:
                out = pick(record, self.fields)
            elif self.exclude:
                out = omit(record, self.exclude)
            else:
                out = dict(record)
            results.append(out)
            context.record_processed()
        return results

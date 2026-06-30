# Data Pipeline Engine — Fix Broken Behaviors

You are working on a data pipeline engine that processes records through
configurable stages: validation, transformation, filtering, and aggregation.

The pipeline is mostly functional, but four behaviors are broken. Each is
described below with its current (incorrect) behavior and the expected
(correct) behavior.

## 1. Nested Object Validation

The schema validator supports nested object fields with their own properties.

**Current behavior**: A nested object field with `type: "object"` only checks
that the value is a dictionary. It does not validate the nested properties.
Any dictionary passes, even if it has missing required fields or wrong types.

**Expected behavior**: When a field has `type: "object"` and a `properties`
key in the schema definition, the validator should recursively validate the
nested properties against their own type and required constraints, reporting
errors just as it does for top-level fields.

Example schema:

    {
        "address": {
            "type": "object",
            "required": True,
            "properties": {
                "city": {"type": "string", "required": True},
                "zip": {"type": "string", "required": True},
            }
        }
    }

With this schema, `{"address": {"city": "NYC"}}` should fail validation
because `zip` is required. Currently it passes because the validator only
checks that `address` is a dict.

## 2. Quarantine Error Recovery

The pipeline supports three error recovery strategies: `fail-fast` (stop on
first error), `skip` (skip failed records and continue), and `quarantine`
(move failed records to a quarantine list and continue processing).

**Current behavior**: Quarantine mode correctly adds the failed record to the
quarantine list, but then halts the pipeline as if in fail-fast mode. Only the
first error is ever quarantined.

**Expected behavior**: Quarantine mode should add the record to quarantine and
then continue processing the remaining records, just like skip mode continues
but with the added quarantine tracking.

## 3. Multi-Group Aggregation Averages

The aggregation stage groups records by a field and computes summary
statistics (SUM, AVG, COUNT, MIN, MAX).

**Current behavior**: The AVG aggregation divides by the total number of
records across all groups, not by the number of records in each group.
This produces correct results when there is only one group, but wrong
results when there are multiple groups with different sizes.

**Expected behavior**: AVG should divide by the count of records in each
specific group, producing a true per-group average.

Example: if group A has values [10, 20, 30] and group B has values [100, 200],
the averages should be A=20.0 and B=150.0, not A=12.0 and B=60.0.

## 4. Computed Field Dependencies

The transformation stage supports computed fields defined by arithmetic
expressions. Computed fields can reference other fields in the record,
including fields computed earlier in the same transformation list.

**Current behavior**: All computed field expressions are evaluated against
the original record values. A computed field that references another computed
field sees 0 (the default for missing fields) instead of the computed value.

**Expected behavior**: Each computed field expression should be evaluated
against the record as updated by all previously computed fields. This way,
a field like `tax = subtotal * 0.1` correctly sees the `subtotal` value
computed in a previous step.

## Entry Points

The main entry points are:

- `pipeline.engine.Pipeline` — the pipeline runner
- `pipeline.schema.validator.SchemaValidator` — the schema validator
- `pipeline.recovery.handler.ErrorHandler` — the error recovery handler
- `pipeline.stages.aggregate.AggregateStage` — the aggregation stage
- `pipeline.stages.transform.TransformStage` — the transformation stage
- `pipeline.config.PipelineBuilder` — the fluent builder API

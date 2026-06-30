"""Verifier for data-pipeline-engine task."""

import sys

sys.path.insert(0, "/app/src")

import pytest  # noqa: E402

from pipeline import (  # noqa: E402
    PipelineBuilder,
    ValidationError,
)
from pipeline.schema.validator import SchemaValidator  # noqa: E402
from pipeline.recovery.handler import ErrorHandler  # noqa: E402
from pipeline.context import PipelineContext  # noqa: E402
from pipeline.stages.validate import ValidationStage  # noqa: E402
from pipeline.stages.transform import TransformStage  # noqa: E402
from pipeline.stages.filter import FilterStage  # noqa: E402
from pipeline.stages.aggregate import AggregateStage  # noqa: E402


# ── Schema Validation (Bug 1: nested objects) ──────────────


def test_flat_record_valid():
    """Valid flat record passes schema validation."""
    schema = {
        "name": {"type": "string", "required": True},
        "age": {"type": "integer", "required": True},
    }
    v = SchemaValidator(schema)
    result = v.validate({"name": "Alice", "age": 30})
    assert result == {"name": "Alice", "age": 30}


def test_flat_invalid_type_rejected():
    """Record with wrong type for a flat field is rejected."""
    schema = {
        "name": {"type": "string", "required": True},
    }
    v = SchemaValidator(schema)
    with pytest.raises(ValidationError):
        v.validate({"name": 123})


def test_missing_required_field_rejected():
    """Record missing a required field is rejected."""
    schema = {
        "name": {"type": "string", "required": True},
        "age": {"type": "integer", "required": True},
    }
    v = SchemaValidator(schema)
    with pytest.raises(ValidationError):
        v.validate({"name": "Alice"})


def test_optional_field_absent():
    """Record with absent optional field passes validation."""
    schema = {
        "name": {"type": "string", "required": True},
        "age": {"type": "integer", "required": False},
    }
    v = SchemaValidator(schema)
    result = v.validate({"name": "Alice"})
    assert result == {"name": "Alice"}


def test_nested_object_valid():
    """Nested object with all valid properties passes."""
    schema = {
        "name": {"type": "string", "required": True},
        "addr": {
            "type": "object",
            "required": True,
            "properties": {
                "city": {"type": "string", "required": True},
                "zip": {"type": "string", "required": True},
            },
        },
    }
    v = SchemaValidator(schema)
    record = {
        "name": "Alice",
        "addr": {"city": "NYC", "zip": "10001"},
    }
    result = v.validate(record)
    assert result["addr"]["city"] == "NYC"
    assert result["addr"]["zip"] == "10001"


def test_nested_object_invalid_type_rejected():
    """Nested object with wrong field type is rejected."""
    schema = {
        "addr": {
            "type": "object",
            "required": True,
            "properties": {
                "city": {"type": "string", "required": True},
                "zip": {
                    "type": "integer",
                    "required": True,
                },
            },
        },
    }
    v = SchemaValidator(schema)
    with pytest.raises(ValidationError):
        v.validate({"addr": {"city": "NYC", "zip": "bad"}})


def test_deeply_nested_validation():
    """Three levels of nested objects are validated."""
    schema = {
        "l1": {
            "type": "object",
            "required": True,
            "properties": {
                "l2": {
                    "type": "object",
                    "required": True,
                    "properties": {
                        "val": {
                            "type": "integer",
                            "required": True,
                        },
                    },
                },
            },
        },
    }
    v = SchemaValidator(schema)
    result = v.validate({"l1": {"l2": {"val": 42}}})
    assert result["l1"]["l2"]["val"] == 42


def test_nested_missing_required_rejected():
    """Nested object missing a required property is rejected."""
    schema = {
        "addr": {
            "type": "object",
            "required": True,
            "properties": {
                "city": {"type": "string", "required": True},
                "zip": {"type": "string", "required": True},
            },
        },
    }
    v = SchemaValidator(schema)
    with pytest.raises(ValidationError):
        v.validate({"addr": {"city": "NYC"}})


def test_type_coercion_string_to_int():
    """String value is coerced to int when coerce is enabled."""
    schema = {
        "age": {"type": "integer", "required": True},
    }
    v = SchemaValidator(schema, coerce=True)
    result = v.validate({"age": "25"})
    assert result["age"] == 25


def test_type_coercion_failure_rejected():
    """Non-coercible value is rejected even with coerce enabled."""
    schema = {
        "age": {"type": "integer", "required": True},
    }
    v = SchemaValidator(schema, coerce=True)
    with pytest.raises(ValidationError):
        v.validate({"age": "not-a-number"})


# ── Error Recovery (Bug 2: quarantine halts) ───────────────


def test_fail_fast_stops_pipeline():
    """Fail-fast strategy raises the error immediately."""
    ctx = PipelineContext()
    handler = ErrorHandler(strategy="fail-fast")
    with pytest.raises(ValidationError):
        handler.handle(
            ValidationError("bad"), {"x": 1}, ctx,
        )


def test_skip_continues_processing():
    """Skip strategy returns True to signal continuation."""
    ctx = PipelineContext()
    handler = ErrorHandler(strategy="skip")
    result = handler.handle(
        ValidationError("bad"), {"x": 1}, ctx,
    )
    assert result is True
    assert ctx.metrics["skipped"] == 1


def test_quarantine_continues_processing():
    """Quarantine adds to quarantine and returns True."""
    ctx = PipelineContext()
    handler = ErrorHandler(strategy="quarantine")
    result = handler.handle(
        ValidationError("bad"), {"x": 1}, ctx,
    )
    assert result is True


def test_quarantine_preserves_error_info():
    """Quarantined records include the error message."""
    ctx = PipelineContext()
    handler = ErrorHandler(strategy="quarantine")
    handler.handle(
        ValidationError("field is wrong"), {"x": 1}, ctx,
    )
    assert len(ctx.quarantine) == 1
    assert "field is wrong" in ctx.quarantine[0]["error"]


def test_quarantine_multiple_records():
    """Multiple failed records are accumulated in quarantine."""
    ctx = PipelineContext()
    handler = ErrorHandler(strategy="quarantine")
    handler.handle(
        ValidationError("e1"), {"a": 1}, ctx,
    )
    handler.handle(
        ValidationError("e2"), {"b": 2}, ctx,
    )
    handler.handle(
        ValidationError("e3"), {"c": 3}, ctx,
    )
    assert len(ctx.quarantine) == 3


def test_quarantine_good_records_unaffected():
    """Valid records pass through quarantine-mode validation."""
    schema = {
        "name": {"type": "string", "required": True},
    }
    stage = ValidationStage(
        schema, error_strategy="quarantine",
    )
    ctx = PipelineContext()
    records = [
        {"name": "Alice"},
        {"name": 123},
        {"name": "Bob"},
    ]
    result = stage.process(records, ctx)
    assert len(result) == 2
    assert result[0]["name"] == "Alice"
    assert result[1]["name"] == "Bob"


def test_error_metrics_tracked():
    """Error metrics are correctly incremented."""
    ctx = PipelineContext()
    handler = ErrorHandler(strategy="skip")
    handler.handle(
        ValidationError("err"), {"x": 1}, ctx,
    )
    assert ctx.metrics["failed"] == 1


# ── Aggregation (Bug 3: global count for AVG) ─────────────


def test_sum_single_group():
    """SUM aggregation works for a single group."""
    stage = AggregateStage(
        "cat",
        [{"field": "v", "operation": "sum", "alias": "total"}],
    )
    ctx = PipelineContext()
    records = [
        {"cat": "A", "v": 10},
        {"cat": "A", "v": 20},
        {"cat": "A", "v": 30},
    ]
    result = stage.process(records, ctx)
    assert len(result) == 1
    assert result[0]["total"] == 60


def test_sum_multiple_groups():
    """SUM aggregation works for multiple groups."""
    stage = AggregateStage(
        "cat",
        [{"field": "v", "operation": "sum", "alias": "total"}],
    )
    ctx = PipelineContext()
    records = [
        {"cat": "A", "v": 10},
        {"cat": "B", "v": 20},
        {"cat": "A", "v": 30},
    ]
    result = stage.process(records, ctx)
    rmap = {r["cat"]: r for r in result}
    assert rmap["A"]["total"] == 40
    assert rmap["B"]["total"] == 20


def test_avg_single_group():
    """AVG aggregation works for a single group."""
    stage = AggregateStage(
        "cat",
        [{"field": "v", "operation": "avg", "alias": "avg"}],
    )
    ctx = PipelineContext()
    records = [
        {"cat": "A", "v": 10},
        {"cat": "A", "v": 20},
        {"cat": "A", "v": 30},
    ]
    result = stage.process(records, ctx)
    assert result[0]["avg"] == pytest.approx(20.0)


def test_avg_multiple_groups():
    """AVG computes per-group averages, not global average."""
    stage = AggregateStage(
        "cat",
        [{"field": "v", "operation": "avg", "alias": "avg"}],
    )
    ctx = PipelineContext()
    records = [
        {"cat": "A", "v": 10},
        {"cat": "A", "v": 20},
        {"cat": "A", "v": 30},
        {"cat": "B", "v": 100},
        {"cat": "B", "v": 200},
    ]
    result = stage.process(records, ctx)
    rmap = {r["cat"]: r for r in result}
    assert rmap["A"]["avg"] == pytest.approx(20.0)
    assert rmap["B"]["avg"] == pytest.approx(150.0)


def test_count_aggregation():
    """COUNT returns the number of records per group."""
    stage = AggregateStage(
        "cat",
        [{"field": "v", "operation": "count", "alias": "cnt"}],
    )
    ctx = PipelineContext()
    records = [
        {"cat": "A", "v": 10},
        {"cat": "A", "v": 20},
        {"cat": "B", "v": 30},
    ]
    result = stage.process(records, ctx)
    rmap = {r["cat"]: r for r in result}
    assert rmap["A"]["cnt"] == 2
    assert rmap["B"]["cnt"] == 1


def test_min_aggregation():
    """MIN returns the smallest value per group."""
    stage = AggregateStage(
        "cat",
        [{"field": "v", "operation": "min", "alias": "lo"}],
    )
    ctx = PipelineContext()
    records = [
        {"cat": "A", "v": 30},
        {"cat": "A", "v": 10},
        {"cat": "A", "v": 20},
    ]
    result = stage.process(records, ctx)
    assert result[0]["lo"] == 10


def test_max_aggregation():
    """MAX returns the largest value per group."""
    stage = AggregateStage(
        "cat",
        [{"field": "v", "operation": "max", "alias": "hi"}],
    )
    ctx = PipelineContext()
    records = [
        {"cat": "A", "v": 10},
        {"cat": "A", "v": 30},
        {"cat": "A", "v": 20},
    ]
    result = stage.process(records, ctx)
    assert result[0]["hi"] == 30


def test_avg_unequal_group_sizes():
    """AVG with unequal group sizes gives correct per-group values."""
    stage = AggregateStage(
        "g",
        [{"field": "v", "operation": "avg", "alias": "a"}],
    )
    ctx = PipelineContext()
    records = [
        {"g": "X", "v": 100},
        {"g": "Y", "v": 10},
        {"g": "Y", "v": 20},
        {"g": "Y", "v": 30},
        {"g": "Y", "v": 40},
    ]
    result = stage.process(records, ctx)
    rmap = {r["g"]: r for r in result}
    assert rmap["X"]["a"] == pytest.approx(100.0)
    assert rmap["Y"]["a"] == pytest.approx(25.0)


# ── Transform (Bug 4: computed field deps) ─────────────────


def test_simple_field_rename():
    """Rename transform changes field name correctly."""
    stage = TransformStage([
        {"type": "rename", "from": "old", "to": "new"},
    ])
    ctx = PipelineContext()
    result = stage.process([{"old": "val"}], ctx)
    assert result[0] == {"new": "val"}


def test_arithmetic_expression():
    """Computed field with simple arithmetic evaluates correctly."""
    stage = TransformStage([
        {
            "type": "compute",
            "field": "total",
            "expr": "price * qty",
        },
    ])
    ctx = PipelineContext()
    result = stage.process([{"price": 10, "qty": 5}], ctx)
    assert result[0]["total"] == 50


def test_computed_field_depends_on_another():
    """Computed field referencing a prior computed field works."""
    transforms = [
        {
            "type": "compute",
            "field": "subtotal",
            "expr": "price * qty",
        },
        {
            "type": "compute",
            "field": "tax",
            "expr": "subtotal * 0.1",
        },
    ]
    stage = TransformStage(transforms)
    ctx = PipelineContext()
    result = stage.process(
        [{"price": 100, "qty": 2}], ctx,
    )
    assert result[0]["subtotal"] == 200
    assert result[0]["tax"] == pytest.approx(20.0)


def test_chain_of_three_dependent_fields():
    """Chain of three computed fields each depending on prior."""
    transforms = [
        {"type": "compute", "field": "a", "expr": "x + 1"},
        {"type": "compute", "field": "b", "expr": "a * 2"},
        {"type": "compute", "field": "c", "expr": "b + a"},
    ]
    stage = TransformStage(transforms)
    ctx = PipelineContext()
    result = stage.process([{"x": 10}], ctx)
    assert result[0]["a"] == 11
    assert result[0]["b"] == 22
    assert result[0]["c"] == 33


def test_independent_computed_fields():
    """Independent computed fields all use original values."""
    transforms = [
        {
            "type": "compute",
            "field": "dx",
            "expr": "x * 2",
        },
        {
            "type": "compute",
            "field": "dy",
            "expr": "y * 2",
        },
    ]
    stage = TransformStage(transforms)
    ctx = PipelineContext()
    result = stage.process([{"x": 5, "y": 10}], ctx)
    assert result[0]["dx"] == 10
    assert result[0]["dy"] == 20


def test_mixed_dependent_independent_fields():
    """Mix of dependent and independent computed fields works."""
    transforms = [
        {
            "type": "compute",
            "field": "sum_ab",
            "expr": "a + b",
        },
        {
            "type": "compute",
            "field": "dc",
            "expr": "c * 2",
        },
        {
            "type": "compute",
            "field": "total",
            "expr": "sum_ab + dc",
        },
    ]
    stage = TransformStage(transforms)
    ctx = PipelineContext()
    result = stage.process(
        [{"a": 3, "b": 7, "c": 5}], ctx,
    )
    assert result[0]["sum_ab"] == 10
    assert result[0]["dc"] == 10
    assert result[0]["total"] == 20


# ── Filter ─────────────────────────────────────────────────


def test_filter_equality():
    """Equality predicate keeps matching records."""
    stage = FilterStage("status == 'active'")
    ctx = PipelineContext()
    records = [
        {"name": "Alice", "status": "active"},
        {"name": "Bob", "status": "inactive"},
        {"name": "Charlie", "status": "active"},
    ]
    result = stage.process(records, ctx)
    assert len(result) == 2
    assert all(r["status"] == "active" for r in result)


def test_filter_comparison():
    """Greater-than-or-equal comparison keeps matches."""
    stage = FilterStage("age >= 18")
    ctx = PipelineContext()
    records = [
        {"name": "Alice", "age": 25},
        {"name": "Bob", "age": 15},
        {"name": "Charlie", "age": 18},
    ]
    result = stage.process(records, ctx)
    assert len(result) == 2


# ── Integration ────────────────────────────────────────────


def test_full_pipeline_integration():
    """Full pipeline: validate, transform, filter, aggregate."""
    schema = {
        "product": {"type": "string", "required": True},
        "price": {"type": "float", "required": True},
        "qty": {"type": "integer", "required": True},
    }
    pipeline = (
        PipelineBuilder()
        .add_validation(schema)
        .add_transform([
            {
                "type": "compute",
                "field": "line_total",
                "expr": "price * qty",
            },
        ])
        .add_filter("qty > 0")
        .add_aggregation("product", [
            {
                "field": "line_total",
                "operation": "sum",
                "alias": "revenue",
            },
        ])
        .build()
    )

    records = [
        {"product": "Widget", "price": 10.0, "qty": 3},
        {"product": "Widget", "price": 10.0, "qty": 2},
        {"product": "Gadget", "price": 25.0, "qty": 1},
    ]
    result = pipeline.run(records)
    rmap = {r["product"]: r for r in result.records}
    assert rmap["Widget"]["revenue"] == pytest.approx(50.0)
    assert rmap["Gadget"]["revenue"] == pytest.approx(25.0)


def test_empty_input_produces_empty_result():
    """Pipeline with empty input produces empty output."""
    pipeline = (
        PipelineBuilder()
        .add_validation(
            {"x": {"type": "integer", "required": True}},
        )
        .build()
    )
    result = pipeline.run([])
    assert result.records == []
    assert result.quarantine == []

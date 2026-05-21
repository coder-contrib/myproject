from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Annotated, Any
from pydantic import BeforeValidator, PlainSerializer, WithJsonSchema


def _coerce_decimal(v: Any, precision: int) -> Decimal:
    if v is None:
        return Decimal(0)
    if isinstance(v, Decimal):
        return v
    try:
        d = Decimal(str(v))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f"Cannot convert {v!r} to Decimal")
    if d.is_nan() or d.is_infinite():
        raise ValueError("Decimal value must be finite")
    return d


def _to_decimal2(v: Any) -> Decimal:
    return _coerce_decimal(v, 2)


def _to_decimal4(v: Any) -> Decimal:
    return _coerce_decimal(v, 4)


def _serialize_decimal2(v: Decimal) -> float:
    return float(v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _serialize_decimal4(v: Decimal) -> float:
    return float(v.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))


def _validate_money(v: Any) -> Decimal:
    d = _to_decimal2(v)
    if d < 0:
        raise ValueError("Monetary value cannot be negative")
    return d


def _validate_quantity(v: Any) -> Decimal:
    d = _to_decimal4(v)
    if d <= 0:
        raise ValueError("Quantity must be positive")
    return d


def _validate_percentage(v: Any) -> Decimal:
    d = _to_decimal2(v)
    if d < 0 or d > 100:
        raise ValueError("Percentage must be between 0 and 100")
    return d


Decimal2 = Annotated[
    Decimal,
    BeforeValidator(_to_decimal2),
    PlainSerializer(_serialize_decimal2, return_type=float),
    WithJsonSchema({"type": "number", "format": "decimal", "multipleOf": 0.01}),
]

Decimal4 = Annotated[
    Decimal,
    BeforeValidator(_to_decimal4),
    PlainSerializer(_serialize_decimal4, return_type=float),
    WithJsonSchema({"type": "number", "format": "decimal", "multipleOf": 0.0001}),
]

Money = Annotated[
    Decimal,
    BeforeValidator(_validate_money),
    PlainSerializer(_serialize_decimal2, return_type=float),
    WithJsonSchema({"type": "number", "format": "decimal", "minimum": 0, "multipleOf": 0.01}),
]

Quantity = Annotated[
    Decimal,
    BeforeValidator(_validate_quantity),
    PlainSerializer(_serialize_decimal4, return_type=float),
    WithJsonSchema({"type": "number", "format": "decimal", "exclusiveMinimum": 0, "multipleOf": 0.0001}),
]

Percentage = Annotated[
    Decimal,
    BeforeValidator(_validate_percentage),
    PlainSerializer(_serialize_decimal2, return_type=float),
    WithJsonSchema({"type": "number", "format": "decimal", "minimum": 0, "maximum": 100}),
]

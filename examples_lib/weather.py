"""A small Hamilton pipeline that turns hourly temperatures into a daily summary.

Each node carries a `stage` tag, which the example drawing fills nodes by.
"""

from typing import TypedDict

from hamilton.function_modifiers import extract_fields, tag


class Range(TypedDict):
    """The coldest and warmest reading of the day."""

    low: float
    high: float


@tag(stage="read")
def readings(hourly: list[float | None]) -> list[float | None]:
    """Hourly temperatures in degrees Celsius, as the station recorded them.

    A missing reading is `None`.
    """
    return list(hourly)


@tag(stage="check")
def plausible(readings: list[float | None], limit: float = 60.0) -> list[float]:
    """Drop missing readings and any beyond `limit` degrees either side of zero.

    Args:
        readings: Hourly temperatures, possibly with gaps.
        limit: The largest magnitude a real reading could have.
    """
    return [r for r in readings if r is not None and abs(r) <= limit]


@tag(stage="derive")
def mean(plausible: list[float]) -> float:
    """The mean of the plausible readings."""
    return sum(plausible) / len(plausible)


@tag(stage="derive")
@extract_fields({"low": float, "high": float})
def temperature_range(plausible: list[float]) -> Range:
    """The lowest and highest plausible readings."""
    return {"low": min(plausible), "high": max(plausible)}


@tag(stage="report")
def summary(mean: float, low: float, high: float) -> str:
    """A one-line summary of the day's temperatures."""
    return f"{mean:.1f} °C on average, from {low:.1f} to {high:.1f} °C"

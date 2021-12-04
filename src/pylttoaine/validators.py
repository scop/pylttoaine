"""
Parameter validators for use in CLI and methods.

This is a separate module, so we are able to use "clean" names for the functions from
the CLI point of view. argparse includes the type function name in its error messages
(even aliasing on import doesn't circumvent that), and we don't want to have functions
named like this in the main API.
"""

from typing import Optional, Union


def max_distance_km(value: Union[str, int]) -> int:
    """Validate max_distance_km."""
    int_value = int(value)
    if int_value < 1:
        raise ValueError("max distance km must be >= 1")
    return int_value


def latitude(value: Union[str, float]) -> float:
    """Validate latitude."""
    float_value = float(value)
    if -90 <= float_value <= 90:
        return float_value
    raise ValueError("latitude must be between -90 and 90")


def longitude(value: Union[str, float]) -> float:
    """Validate longitude."""
    float_value = float(value)
    if -180 <= float_value <= 180:
        return float_value
    raise ValueError("longitude must be between -180 and 180")


def price(value: Union[str, float, None]) -> Optional[float]:
    """Validate price."""
    if value is None:
        return None
    float_value = float(value)
    if float_value > 0:
        return float_value
    raise ValueError("price must be > 0")

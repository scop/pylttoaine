"""polttoaine.info models."""

from dataclasses import astuple, dataclass, fields
from datetime import date
from typing import Iterator, Optional


class _Base:  # pylint: disable=too-few-public-methods
    def __iter__(self) -> Iterator:  # type: ignore[type-arg]
        """Iterate over field values."""
        return iter(astuple(self))


@dataclass
class City(_Base):
    """City."""

    id: int  # pylint: disable=invalid-name
    name: str


@dataclass
class Prices(_Base):
    """Prices."""

    date: Optional[date]
    price_95: Optional[float]
    price_98: Optional[float]
    price_diesel: Optional[float]
    confirmed: Optional[bool] = None


@dataclass
class Coordinates(_Base):
    """Coordinates."""

    latitude: float
    longitude: float


@dataclass
class Station(_Base):
    """Station."""

    id: int  # pylint: disable=invalid-name
    prices: Prices
    name: Optional[str] = None
    city: Optional[City] = None
    coordinates: Optional[Coordinates] = None

    def __iter__(self) -> Iterator:  # type: ignore[type-arg]
        """
        Iterate over field values.

        This implementation flattens field values and replaces None values with
        appropriate number of Nones for the field, so that iterators for all instances
        have the same length.
        """
        return iter(
            (self.id,)
            + astuple(self.prices)
            + (self.name,)
            + (
                astuple(self.city)
                if self.city is not None
                else (None,) * len(fields(City))
            )
            + (
                astuple(self.coordinates)
                if self.coordinates is not None
                else (None,) * len(fields(Coordinates))
            )
        )


@dataclass
class _QueryParams:
    # pylint: disable=invalid-name  # these map to API parameters as is
    cityId: str
    kuntaNimi: str
    isCity: str

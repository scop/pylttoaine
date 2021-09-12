"""Pylttoaine tests."""

import datetime as dt

import pytest
from aiohttp import ClientResponseError, ClientSession

from pylttoaine import (
    get_cities,
    get_stations_by_city,
    get_stations_by_location,
    submit,
)
from pylttoaine.models import City, Coordinates, Prices, Station


@pytest.mark.asyncio
@pytest.mark.vcr
async def test_get_cities() -> None:
    """Test getting cities."""
    async with ClientSession() as session:
        cities = [x async for x in get_cities(session)]

    assert len(cities) == 308
    assert all(isinstance(x, City) for x in cities)


@pytest.mark.asyncio
@pytest.mark.vcr
async def test_get_stations_by_city() -> None:
    """Test getting stations by city."""
    async with ClientSession() as session:
        stations = [x async for x in get_stations_by_city(session, 19, "Espoo")]

    assert len(stations) == 59
    assert all(isinstance(x, Station) for x in stations)


@pytest.mark.asyncio
@pytest.mark.vcr
async def test_get_stations_by_location() -> None:
    """Test getting stations by location."""
    async with ClientSession() as session:
        stations = [
            x
            async for x in get_stations_by_location(session, Coordinates(60.20, 24.75))
        ]

    assert len(stations) == 33
    assert all(isinstance(x, Station) for x in stations)


@pytest.mark.asyncio
@pytest.mark.vcr
async def test_get_stations_by_location_error() -> None:
    """Test error getting stations by location."""
    with pytest.raises(ClientResponseError):
        async with ClientSession() as session:
            _ = [
                x
                async for x in get_stations_by_location(
                    session, Coordinates(59.723056, 22.498889), max_distance_km=1
                )
            ]


@pytest.mark.asyncio
@pytest.mark.vcr
async def test_submit() -> None:
    """
    Test submitting updated prices.

    Note: when running without an up to date cassette, make sure to update the
    submitted data in order to not send bogosity to the actual service!
    """
    async with ClientSession() as session:
        station = Station(
            id=2799,
            prices=Prices(
                date=dt.date.today() - dt.timedelta(days=1),
                price_95=1.639,
                price_98=1.729,
                price_diesel=1.514,
            ),
        )
        message = await submit(session, station)

    assert message

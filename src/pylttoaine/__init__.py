"""polttoaine.info support."""

import csv
import datetime as dt
import io
from dataclasses import asdict
from typing import AsyncGenerator, List, Optional
from urllib.parse import urljoin

try:
    import zoneinfo  # type: ignore[import]
except ImportError:  # Python < 3.9
    from backports import zoneinfo  # type: ignore[import]

from aiohttp import ClientResponse, ClientResponseError, ClientSession

from . import validators
from .models import City, Coordinates, Prices, Station, _QueryParams

__version__ = "0.9.0"

BASE_URL = "https://www.omamobiili.com/pa_api/"
EUROPE_HELSINKI = zoneinfo.ZoneInfo("Europe/Helsinki")


async def get_cities(session: ClientSession) -> AsyncGenerator[City, None]:
    """
    Get cities.

    :param session: aiohttp session
    """
    url = urljoin(BASE_URL, "Station/GetCities")

    async with session.get(url, raise_for_status=True) as response:
        async for row in _iter_rows(response):
            id_str, name, *_ = row
            yield City(int(id_str), name)


async def get_stations_by_location(
    session: ClientSession,
    coordinates: Coordinates,
    max_distance_km: int = 5,
) -> AsyncGenerator[Station, None]:
    """
    Get stations by location.

    :param session: aiohttp session
    :param coordinates: coordinates for location
    :param max_distance_km: maximum distance from coordinates in kilometers, >= 1
    """
    max_distance_km = validators.max_distance_km(max_distance_km)
    _ = validators.latitude(coordinates.latitude)
    _ = validators.longitude(coordinates.longitude)

    params = _QueryParams(
        cityId=f"{coordinates.latitude:f}/{coordinates.longitude:f}",
        # magic value for kuntaNimi triggering coordinate/distance based search?
        kuntaNimi="Lähimmät asemat",
        isCity="%d" % max_distance_km,
    )
    async for station in _get_stations(session, params):
        yield station


async def get_stations_by_city(
    session: ClientSession,
    city_id: int,
    city_name: Optional[str] = None,
) -> AsyncGenerator[Station, None]:
    """
    Get stations by city.

    With only city_id, gets stations that have some prices set. To also get ones with
    no prices available, city_name needs to be passed as well.
    """
    params = _QueryParams(
        cityId="%d" % city_id,
        kuntaNimi=city_name or "",
        isCity="true",
    )
    async for station in _get_stations(session, params):
        yield station


async def submit(session: ClientSession, station: Station) -> Optional[str]:
    """
    Submit prices update for a station.

    :param session: aiohttp session
    :param station: station with prices to update
    :return: message for successful update
    """
    url = urljoin(BASE_URL, "Station/SendPricesAPI2")

    _ = validators.price(station.prices.price_95)
    _ = validators.price(station.prices.price_98)
    _ = validators.price(station.prices.price_diesel)

    data = {
        "Id": station.id,
        "Price1": station.prices.price_95 or "",
        "Price2": station.prices.price_98 or "",
        "Price3": station.prices.price_diesel or "",
    }
    today = dt.date.today()
    if station.prices.date == today:
        data["NotifiedDay"] = 1
    elif station.prices.date == today - dt.timedelta(days=1):
        data["NotifiedDay"] = 2
    else:
        raise ValueError("Prices.date must be today or yesterday")

    success: Optional[bool] = None
    message = ""
    async with session.post(url, data=data, raise_for_status=True) as response:
        async for row in _iter_rows(response):
            if success is None:
                status, message, *_ = row
                success = status == "success"
        if success is False:  # True and None considered success
            raise ClientResponseError(
                request_info=response.request_info,
                history=response.history,
                status=response.status,
                message=message or response.reason or "Unknown error",
                headers=response.headers,
            )

    return message


async def _get_stations(  # pylint: disable=too-many-locals
    session: ClientSession,
    params: _QueryParams,
) -> AsyncGenerator[Station, None]:
    url = urljoin(BASE_URL, "Station/GetStationsKuntaNameWithEmpty")

    async with session.get(
        url, params=asdict(params), raise_for_status=True
    ) as response:
        now = dt.datetime.now(EUROPE_HELSINKI)

        async for row in _iter_rows(response):
            (
                id_str,
                name,
                date_str,
                price_95_str,
                price_98_str,
                price_di_str,
                latitude_str,
                longitude_str,
                city_id_str,
                city_name,
                confirmed_str,
                # image,
                *_,
            ) = row

            datetime: Optional[dt.datetime] = None
            if date_str not in (None, "-"):
                datetime = dt.datetime.strptime(
                    f"{date_str}{now.year}", "%d.%m.%Y"
                ).astimezone(EUROPE_HELSINKI)
                if datetime > now:
                    # Assume entry is from last year
                    datetime = dt.datetime.strptime(
                        f"{date_str}{now.year-1}", "%d.%m.%Y"
                    ).astimezone(EUROPE_HELSINKI)

            prices = Prices(
                datetime.date() if datetime else None,
                float(price_95_str) if price_95_str not in (None, "-") else None,
                float(price_98_str) if price_98_str not in (None, "-") else None,
                float(price_di_str) if price_di_str not in (None, "-") else None,
                confirmed_str.lower() == "true" if confirmed_str else None,
            )

            # Latitude/longitude are sometimes empty, unclear exactly when/why
            coordinates = (
                Coordinates(float(latitude_str), float(longitude_str))
                if latitude_str and longitude_str
                else None
            )

            try:
                city: Optional[City] = City(int(city_id_str), city_name)
            except ValueError:
                # in lat/lon mode, we get the lat/lon as city_id_str, just skip it
                if not ("/" in city_id_str and "/" in params.cityId):
                    raise
                city = None

            yield Station(int(id_str), prices, name, city, coordinates)


async def _iter_rows(response: ClientResponse) -> AsyncGenerator[List[str], None]:
    """
    Async iterator over CSV rows in given response.

    We could use aiocsv for this, but would need to do decoding ourselves anyway,
    and it has some issues related to newlines treatment the stdlib csv doesn't.
    """
    buffer = io.StringIO(newline="")
    csv_reader = csv.reader(buffer, delimiter=";")
    encoding = response.charset or "utf-8"
    async for line in response.content:
        line_str = line.decode(encoding=encoding, errors="replace")
        # Errors are given with 200 OK and exception in response body, detect naively...
        if "Exception: " in line_str:
            # ...and synthetize response error as if it came with an error status.
            message = line_str.strip()
            async for line in response.content:
                pass
            raise ClientResponseError(
                request_info=response.request_info,
                history=response.history,
                status=response.status,
                message=message,
                headers=response.headers,
            )
        buffer.write(line_str)
        endpos = buffer.tell()
        buffer.seek(0)
        try:
            row = next(csv_reader)
        except StopIteration:
            buffer.seek(endpos)
            continue
        yield row
        buffer.seek(0)
        buffer.truncate(0)

#!/usr/bin/env python3

"""Simple CLI for pylttoaine."""

import argparse
import asyncio
import csv
import datetime as dt
import sys
from typing import AsyncGenerator, Union

from aiohttp import ClientSession

from pylttoaine import (
    __version__,
    get_cities,
    get_stations_by_city,
    get_stations_by_location,
    submit,
    validators,
)
from pylttoaine.models import City, Coordinates, Prices, Station


async def main() -> None:  # pylint: disable=too-many-branches,too-many-locals,too-many-statements
    """Run the CLI."""

    parser = argparse.ArgumentParser(prog=__package__)
    parser.add_argument("--output-format", choices=("str", "csv"), default="str")
    subparsers = parser.add_subparsers(dest="command", required=True)
    _ = subparsers.add_parser("cities")
    stations_parser = subparsers.add_parser("stations")
    stations_subparsers = stations_parser.add_subparsers(
        dest="stations_command", required=True
    )
    stations_by_city_parser = stations_subparsers.add_parser("city")
    stations_by_city_parser.add_argument(dest="city_id", metavar="CITY-ID", type=int)
    stations_by_city_parser.add_argument("--name", type=str)
    stations_by_location_parser = stations_subparsers.add_parser("location")
    stations_by_location_parser.add_argument(
        "latitude", metavar="LATITUDE", type=validators.latitude
    )
    stations_by_location_parser.add_argument(
        "longitude", metavar="LONGITUDE", type=validators.longitude
    )
    stations_by_location_parser.add_argument(
        "--max-distance-km", metavar="N", type=validators.max_distance_km
    )
    submit_parser = subparsers.add_parser("submit")
    submit_parser.add_argument(dest="station_id", metavar="STATION-ID", type=int)
    submit_parser.add_argument("when", metavar="WHEN", choices=("today", "yesterday"))
    submit_parser.add_argument("--price-95", metavar="PRICE", type=validators.price)
    submit_parser.add_argument("--price-98", metavar="PRICE", type=validators.price)
    submit_parser.add_argument("--price-diesel", metavar="PRICE", type=validators.price)
    _ = subparsers.add_parser("version")

    args = parser.parse_args()

    if args.command == "version":
        print(__version__)
        sys.exit(0)

    async with ClientSession() as session:
        if args.command == "cities":
            result: Union[
                AsyncGenerator[City, None], AsyncGenerator[Station, None]
            ] = get_cities(session)

        elif args.command == "submit":
            if not (args.price_95 or args.price_98 or args.price_diesel):
                submit_parser.error("at least one --price-* argument is required")

            date = dt.date.today()
            if args.when == "yesterday":
                date = date - dt.timedelta(days=1)
            message = await submit(
                session,
                Station(
                    id=args.station_id,
                    prices=Prices(
                        price_95=args.price_95,
                        price_98=args.price_98,
                        price_diesel=args.price_diesel,
                        date=date,
                    ),
                ),
            )
            if message is not None:
                if args.output_format == "csv":
                    writer = csv.writer(sys.stdout)
                    writer.writerow([message])
                else:
                    print(message)
            return

        elif args.stations_command == "city":
            result = get_stations_by_city(
                session,
                args.city_id,
                args.name,
            )

        elif args.stations_command == "location":
            kwargs = {}
            if args.max_distance_km:
                kwargs["max_distance_km"] = args.max_distance_km
            result = get_stations_by_location(
                session, Coordinates(args.latitude, args.longitude), **kwargs
            )

        if args.output_format == "csv":
            writer = csv.writer(sys.stdout)
            async for entry in result:
                writer.writerow(entry)
        else:
            async for entry in result:
                print(entry)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

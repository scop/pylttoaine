# pylttoaine -- polttoaine.info API client

[![Python versions](https://img.shields.io/pypi/pyversions/pylttoaine.svg)](https://pypi.org/project/pylttoaine/)
[![PyPI version](https://badge.fury.io/py/pylttoaine.svg)](https://badge.fury.io/py/pylttoaine)
[![CI status](https://github.com/scop/pylttoaine/workflows/check/badge.svg)](https://github.com/scop/pylttoaine/actions?query=workflow%3Acheck)

Simple asyncio client for the
[polttoaine.info](https://polttoaine.info) API.

The API of this package is modeled closely after the polttoaine.info
API.

Usage in a nutshell:

* construct an aiohttp [`ClientSession`](https://docs.aiohttp.org/en/stable/client_reference.html#client-session),
* construct a `Pylttoaine` client with it,
* invoke methods on the client.

The package can be also invoked as a command line tool, like `python3
-m pylttoaine`, or simply `pytekukko`. Major functionalities of the
package are available on the command line this way. Invoke it with
`--help` for usage information.

## Disclaimer

This package is not supported by or endorsed by polttoaine.info. Do
not bother them with issues related to it.

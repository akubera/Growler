#
# growler/http/__init__.py
#
"""
Submodule dealing with HTTP implementation.
In this pacakge we have the asyncio protocol, server, parser, and
request and response objects.
"""

import mimetypes

from http import HTTPStatus as HttpStatus

from .parser import Parser
from .parser import Parser as HTTPParser
from .methods import HTTPMethod
from .request import HTTPRequest
from .response import HTTPResponse
from ..aio.http_protocol import GrowlerHTTPProtocol
from .errors import __all__ as http_errors


from http.server import BaseHTTPRequestHandler


mimetypes.init()

__all__ = [
    'HTTPRequest',
    'HTTPResponse',
    'Parser',
    'HTTPParser',
    'HTTPMethod',
    'HttpStatus',
    'HttpStatusPhrase',
    'GrowlerHTTPProtocol',
]

__all__.extend(http_errors)

MAX_REQUEST_LENGTH = 4 * (2 ** 10)  # 4KB
MAX_POST_LENGTH = 2 * (2 ** 20)     # 2MB

RESPONSES = BaseHTTPRequestHandler.responses

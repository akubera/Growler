#
# tests/test_http_protocol.py
#

import pytest
import asyncio
import growler
from unittest import mock

from mocks import *

from mock_classes import (
    AsyncMock,
)

from test_protocol import (
    mock_responder,
)

# @pytest.fixture
def MockGrowlerHTTPProtocol(request):
    return mock.create_autospec(growler.http.GrowlerHTTPProtocol)


@pytest.fixture
def mock_app(mock_req_factory, mock_res_factory):
    return mock.Mock(spec=growler.Application,
                     _request_class=mock_req_factory,
                     _response_class=mock_res_factory)


@pytest.fixture
def mock_parser():
    parser = mock.MagicMock(spec=growler.http.Parser(mock.MagicMock()))
    parser.headers = {}
    parser.method = mock.MagicMock()
    parser.query = mock.MagicMock()
    return parser


@pytest.fixture
def mock_parser_factory(mock_parser):
    parser_factory = mock.Mock(return_value=mock_parser)
    return parser_factory


@pytest.fixture
def unconnected_proto(mock_app, make_responder):
    proto = growler.http.GrowlerHTTPProtocol(mock_app)
    proto.make_responder = make_responder
    return proto


@pytest.fixture
def make_responder(mock_app,
                   mock_responder,
                   mock_req_factory,
                   mock_res_factory):
    def factory(http_protocl):
        responder = mock_responder
        responder._proto = http_protocl
        responder.parser_factory = mock.Mock()
        responder.request_factory = mock_req_factory
        responder.response_factory = mock_res_factory
        return responder
    return factory


@pytest.fixture
def proto(unconnected_proto, mock_transport):
    unconnected_proto.connection_made(mock_transport)
    return unconnected_proto


@pytest.fixture
def mock_proto(mock_app):
    return MockGrowlerHTTPProtocol(mock_app)


def test_mock_protocol(mock_proto):
    from growler.http import GrowlerHTTPProtocol
    assert isinstance(mock_proto, GrowlerHTTPProtocol)


def test_constructor(mock_app, mock_event_loop, mock_responder):
    proto = growler.http.GrowlerHTTPProtocol(mock_app, loop=mock_event_loop)

    assert isinstance(proto, asyncio.Protocol)
    assert proto.http_application is mock_app


def test_http_responder_factory(proto):
    responder = proto.http_responder_factory(proto)
    assert responder._handler is proto


def test_connection_made(unconnected_proto,
                         mock_transport,
                         mock_responder,
                         make_responder,
                         client_port,
                         client_host):
    unconnected_proto.connection_made(mock_transport)
    proto = unconnected_proto
    assert proto.transport is mock_transport
    assert proto.responders[0] is mock_responder
    assert proto.remote_port is client_port
    assert proto.remote_hostname is client_host


def test_on_data(proto, mock_responder):
    data = b'data'
    proto.data_received(data)
    mock_responder.on_data.assert_called_with(data)


def notest_process_middleware(proto,
                            mock_app,
                            mock_req,
                            mock_res):

    proto.process_middleware(mock_req, mock_res)

    mock_app.middleware_chain.assert_called_with(mock_req)



def test_on_data_error(proto, mock_responder, mock_transport):
    data = b'data'
    ex = Exception()
    mock_responder.on_data.side_effect = ex
    proto.data_received(data)
    assert mock_transport.write.called


def test_handle_error_http(proto, mock_responder, mock_transport):
    data = b'data'
    ex = growler.http.errors.HTTPErrorForbidden()
    mock_responder.on_data.side_effect = ex
    proto.data_received(data)
    assert mock_transport.write.called
    assert mock_transport.write.call_args_list[0][0][0].startswith(b'HTTP/1.1 403 Forbidden')


@pytest.mark.asyncio
async def test_begin_application(proto, mock_app, mock_req, mock_res, AsyncMock):
    proto.loop = mock.Mock()
    proto.http_application.handle_client_request = AsyncMock()

    proto.begin_application(mock_req, mock_res)
    mock_app.handle_client_request.assert_called_with(mock_req, mock_res)


@pytest.mark.asyncio
async def test_body_storage_pair(proto):
    data = b'test data'

    rdr, wtr = proto.body_storage_pair()
    wtr.send(data)

    returned = await rdr
    assert returned is data


def test_factory(mock_app):
    proto = growler.http.GrowlerHTTPProtocol.factory(mock_app)
    assert isinstance(proto, growler.http.GrowlerHTTPProtocol)


def test_get_factory(mock_app):
    factory = growler.http.GrowlerHTTPProtocol.get_factory(mock_app)
    proto = factory()
    assert isinstance(proto, growler.http.GrowlerHTTPProtocol)

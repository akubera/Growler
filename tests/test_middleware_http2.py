#
# tests/test_middleware.py
#

import growler
import growler.middleware.http2
import pytest
from unittest import mock
import base64

from mock_classes import (
    mock_protocol
)


@pytest.fixture
def request_uri():
    return '/'


@pytest.fixture
def http2_req():
    return mock.Mock(spec=growler.http.request.HTTPRequest,
                     protocol='http',
                     headers={
                        'UPGRADE': "h2c",
                        'CONNECTION': "Upgrade, HTTP2-Settings",
                        'HTTP2-SETTINGS':  base64.b64encode(b'blahhhhh')
                     },)


@pytest.fixture
def res():
    return mock.Mock(spec=growler.http.HTTPResponse)


@pytest.fixture
def http2():
    return growler.middleware.http2.HTTP2()


@pytest.fixture
def http2_responder(mock_protocol):
    return growler.middleware.http2.GrowlerHTTP2Responder(mock_protocol)


def test_http2_middleware(http2, http2_req, res):
    http2(http2_req, res)
    assert res.status == 101
    res.set.assert_any_call('Connection', 'Upgrade')
    res.set.assert_any_call("Upgrade", "h2c")
    res.write.assert_called
    assert not res.end.called


def test_htt2_responder(mock_protocol):
    assert mock_protocol is not None


def test_http2_preface():
    preface = growler.middleware.http2.GrowlerHTTP2Responder.PREFACE
    g = int.from_bytes(preface,  byteorder='big')
    assert g == 0x505249202a20485454502f322e300d0a0d0a534d0d0a0d0a

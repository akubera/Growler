#
# growler/middleware/http2.py
#
"""
Growler middleware which responds to HTTP/2 upgrade requests.
"""

from growler.http.errors import HTTPErrorBadRequest

class HTTP2:
    """
    HTTP/2 middleware class for Growler.

    To use, first `from growler.middleware.http2 import HTTP2` then soon after
    creating your growler application, add an instance of the class to your
    application using the `use` method. Example:

    .. code:: python

        ...
        from growler.middleware.http2 import HTTP2
        ...

        app.use(Logging())
        app.use(HTTP2())

        app.use()


    This middleware checks the request for an HTTP/2 upgrade header

    This class adds a GrowlerHTTP2Responder to the protocol's responder stack,
    handling the remaining of the data.

    """
    PROTO_DICT = {'h2': 'https', 'h2c': 'http'}

    def __init__(self):
        pass

    def __call__(self, req, res):
        try:
            do_http2 = req.headers['CONNECTION'] == 'Upgrade, HTTP2-Settings'
        except KeyError:
            do_http2 = False

        if do_http2:
            try:
                assert PROTO_DICT[req.headers['UPGRADE']] == req.protocol
                settings = req.headers['UPGRADE']
                assert isinstance(settings, str)
            except:
                raise HTTPErrorBadRequest()

        proto = req._protocol
        proto.responders.append(GrowlerHTTP2Responder(proto))


class GrowlerHTTP2Responder:
    """
    A growler responder which handles HTTP/2 requests. This should be created
    from the 'standard' responder upon an upgrade header from the client. The
    implementation still needs to be done.
    """
    PREFACE = (0x505249202a20485454502f322e300d0a0d0a534d0d0a0d0a,)

    def __init__(self, protocol):
        """
        Construct the HTTP/2 Responder.
        """
        self._proto = protocol
        self.loop = protocol.loop

    def on_data(self, data):
        """
        The incoming data function for responders.
        """
        pass

    @classmethod
    def switch_protocols(cls, req, res):
        switch = '\r\n'.join(("HTTP/1.1 101 Switching Protocols",
                              "Connection: Upgrade",
                              "Upgrade: h2c"))
        res.set("Connection", "Upgrade")
        res.set("Upgrade", "h2c")
        res.status = 101
        res.write(switch)

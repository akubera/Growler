#
# growler/http/http2_responder.py
#
"""
A growler responder which handles HTTP/2 requests
"""


class GrowlerHTTP2Responder:
    """
    A growler responder which handles HTTP/2 requests. This should be created
    from the 'standard' responder upon an upgrade header from the client. The
    implementation still needs to be done.
    """

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

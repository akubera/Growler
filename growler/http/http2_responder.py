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
    PREFACE = 0x505249202a20485454502f322e300d0a0d0a534d0d0a0d0a

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
        switch = '''HTTP/1.1 101 Switching Protocols
Connection: Upgrade
Upgrade: h2c

'''
        res.status = 101
        res.write(switch)

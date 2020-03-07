#
# growler/router.py
#

import re
import logging
from collections import OrderedDict
from growler.http import HTTPMethod
from .middleware_chain import (
    MiddlewareChain,
)

ROUTABLE_NAME_REGEX = re.compile("(%s)_.*" % '|'.join([
    "all",
    "get",
    "post",
    "put",
    "delete",
]), re.IGNORECASE + re.UNICODE)

logger = logging.getLogger(__name__)


class Router(MiddlewareChain):
    """
    The router class holds all the 'routes': callbacks connected
    assigned to HTTP method and regular expression pairs.
    If a regex matches with the request's path member, the callback
    is called with the req, res pair.

    Routes are added on a per-method basis, using the
    :code:`router.*method*(path, cb)` syntax, for example:

    >>> router.get("/home", cb)

    will call cb(req, res) upon every incoming HTTP connection with
    the request line: ``GET /home HTTP/1.1``.
    To catch all methods, use the ``router.all`` member.

    Routers can be linked together in a tree-like structure using the
    `use` method enabling components of websites can be developed in
    their own "namespace" and mounted to the website on its own path:

    >>> blog_router.get("/list", ...)
    >>> blog_router.post("/new_post", ...)
    >>> root_router.use("/blog", blog_router)

    The default growler.App has its root router at self.router, and
    offers convience aliases to automatically add routes:
    >>> app.get(..) == app.router.get(...)
    """
    sinatra_param_regex = re.compile(r":(\w+)")
    regex_type = type(sinatra_param_regex)

    def __init__(self):
        super().__init__()
        self.log = logger.getChild("id=%x" % id(self))
        self.add_route = self.add

    def add_router(self, path, router):
        """
        Add a (regex, router) pair to this router. Any req.path that
        matches the regex will pass the request/response objects to
        that router.
        """
        self.add(HTTPMethod.ALL, path, router)
        return self

    def _add_route(self, method, path, middleware=None):
        """The implementation of adding a route"""
        if middleware is not None:
            self.add(method, path, middleware)
            return self
        else:
            # return a lambda that will return the 'func' argument
            return lambda func: (
                self.add(method, path, func),
                func
            )[1]

    def all(self, path, middleware=None):
        """ Matches all HTTP requests """
        return self._add_route(HTTPMethod.ALL, path, middleware)

    def get(self, path, middleware=None):
        """ Matches "GET" HTTP request """
        return self._add_route(HTTPMethod.GET, path, middleware)

    def post(self, path, middleware=None):
        """ Matches "POST" HTTP request """
        return self._add_route(HTTPMethod.POST, path, middleware)

    def put(self, path, middleware=None):
        """ Matches "PUT" HTTP request """
        return self._add_route(HTTPMethod.PUT, path, middleware)

    def delete(self, path, middleware=None):
        """ Matches "DELETE" HTTP request """
        return self._add_route(HTTPMethod.DELETE, path, middleware)

    def use(self, middleware, path=None):
        """
        Call the provided middleware upon requests matching the path.
        If path is not provided or None, all requests will match.

        Args:
            middleware (callable): Callable with the signature
                ``(res, req) -> None``
            path (Optional[str or regex]): a specific path the
                request must match for the middleware to be called.
        Returns:
            This router
        """
        self.log.info(" Using middleware %r", middleware)
        if path is None:
            path = MiddlewareChain.ROOT_PATTERN
        self.add(HTTPMethod.ALL, path, middleware)
        return self

    def match_routes(self, req):
        """
        Yields a sequence of 'route' functions which match the path
        in the request.
        """
        return self(req.method, req.path)

    def iter_routes(self):
        for mw in self.mw_list:
            yield (mw.mask, mw.path, mw.func)

    def should_skip_middleware(self, middleware, matching, rest) -> bool:
        """
        Returns True (i.e. should skip) if request does not match the
        entire middleware path.
        This is a simple check if 'rest' is truthy or not.
        """
        return bool(not matching) or bool(rest)

    @property
    def routes(self):
        return tuple(self.iter_routes())

    @property
    def subrouters(self):
        """
        Generator of sub-routers (middleware inheriting from Router)
        contained within this router.
        """
        yield from filter(lambda mw: isinstance(mw.func, Router), self.mw_list)

    @classmethod
    def sinatra_path_to_regex(cls, path):
        """
        Converts a sinatra-style path to a regex with named
        parameters.
        """
        # Return the path if already a (compiled) regex
        if type(path) is cls.regex_type:
            return path

        # Build a regular expression string which is split on the '/' character
        regex = [
            r"(?P<{}>\w+)".format(segment[1:])
            if cls.sinatra_param_regex.match(segment)
            else segment
            for segment in path.split('/')
        ]
        return re.compile('/'.join(regex))


class RouterMeta(type):
    """
    A metaclass for classes that should automatically be converted
    into growler application routers.
    The only feature this metaclass includes right now is
    providing an ordered dictionary of members, allowing guarenteed
    route placement.
    """

    @classmethod
    def __prepare__(metacls, name, bases, **kargs):
        """
        Metaclass attribute which creates the mapping object - in
        this case a standard :class:`collections.OrderedDict` object
        to preserve order of method names.

        Args:
            name (str): The name of the class
            base (tuple): Collection of baseclasses
        Return:
            Simple ordered dict to store the class members/methods
        """
        return OrderedDict()

    def __new__(cls, name, bases, classdict):
        """
        Creates the class type, adding an additional attributes
        __ordered_attrs__, a snapshot of the dictionary keys, and
        __growler_router, a method which will generate a growler.Router
        object.
        """
        child_class = type.__new__(cls, name, bases, classdict)

        def build_router(self):
            router = Router()

            routes = get_routing_attributes(self, keys=classdict.keys())
            for method, path, func in routes:
                router.add(method, path, func)
            self.__growler_router = router
            return router

        child_class.__growler_router = build_router
        return child_class


def _find_routeable_attributes(obj, keys):
    """
    From the set of provided `keys`, this function yields the attributes
    of `obj` that fulfill the requirements of 'routeable':
    * callable
    * matched by ROUTABLE_NAME_REGEX
    * has docstring

    """
    for attr in keys:
        matches = ROUTABLE_NAME_REGEX.match(attr)
        if matches is None:
            continue
        try:
            val = getattr(obj, attr)
        except AttributeError:
            continue

        if not callable(val) or val.__doc__ is None:
            continue

        method_name = matches.group(1).upper()
        yield val, method_name


def get_routing_attributes(obj, modify_doc=False, keys=None):
    """
    Loops through the provided object (using the dir() function) and
    finds any callables which match the name signature (e.g.
    get_foo()) AND has a docstring beginning with a path-like char
    string.
    This does process things in alphabetical order (rather than than
    the unpredictable __dict__ attribute) so take this into
    consideration if certain routes should be checked before others.
    Unfortunately, this is a problem because the 'all' method will
    always come before others, so there is no capturing one type
    followed by a catch-all 'all'. Until a solution is found, just
    make a router by hand.
    """
    if keys is None:
        keys = dir(obj)

    for val, method_str in _find_routeable_attributes(obj, keys):

        path, *doc = val.__doc__.split(maxsplit=1) or ('', '')

        if not path:
            continue

        if modify_doc:
            val.__doc__ = ''.join(doc)

        method = HTTPMethod[method_str]

        yield method, path, val


def routerclass(cls):
    """
    A class decorator which parses a class, looking for an member
    functions which match an HTTP verb (get, post, etc) followed by
    an underscore and other letters, with a signature of two
    parameters (req and res). For example
    .. code: python

        def get_index(req, res):
            ...

    To determine the path to take, the string looks at the first
    complete word of a stripped docstring, passing this in to the
    'path matching algorithm'.
    The order wich the methods are defined are the order the requests
    will attempt to match.
    """
    logging.debug("Creating a routerclass with the class %s" % cls)
    cls.__growler_router = lambda self: routerify(self)
    return cls


def routerify(obj):
    """
    Scan through attributes of object parameter looking for any which
    match a route signature.
    A router will be created and added to the object with parameter.

    Args:
        obj (object): The object (with attributes) from which to
            setup a router

    Returns:
        Router: The router created from attributes in the object.
    """
    router = Router()
    for info in get_routing_attributes(obj):
        router.add_route(*info)
    obj.__growler_router = router
    return router

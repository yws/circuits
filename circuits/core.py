# Module:   core
# Date:     2nd April 2006
# Author:   James Mills, prologic at shortcircuit dot net dot au

"""Building Blocks

This module contains the most basic building blocks of all Components.
It's important to note that a Component is also a Manager.

The following import statement is commonly used:
   >>> from circuits import handler, Event, Component, Manager
"""

import new
import time
import warnings
from itertools import chain
from threading import Thread
from functools import partial
from collections import deque
from collections import defaultdict
from sys import exc_info as _exc_info
from sys import exc_clear as _exc_clear
from inspect import getargspec, getmembers

try:
    from multiprocessing import Process
    HAS_MULTIPROCESSING = 2
except ImportError:
    try:
        from processing import Process
        HAS_MULTIPROCESSING = 1
    except ImportError:
        HAS_MULTIPROCESSING = 0


class Event(object):
    """Create a new Event Object

    Create a new Event Object populating it with the given list of arguments
    and keyword arguments.

    @ivar name:    The name of the Event
    @ivar channel: The channel this Event is bound for
    @ivar target:  The target Component's channel this Event is bound for

    @param args: list of arguments
    @type  args: tuple

    @param kwargs: dct of keyword arguments
    @type  kwargs: dict
    """

    def __init__(self, *args, **kwargs):
        "x.__init__(...) initializes x; see x.__class__.__doc__ for signature"

        self.args = args
        self.kwargs = kwargs

        self.name = self.__class__.__name__
        self.channel = None
        self.target = None

    def __eq__(self, y):
        """ x.__eq__(y) <==> x==y

        Tests the equality of Event self against Event y.
        Two Events are considered "equal" iif the name,
        channel and target are identical as well as their
        args and kwargs passed.
        """

        attrs = ("name", "args", "kwargs", "channel", "target")
        return all([getattr(self, a) == getattr(y, a) for a in attrs])

    def __repr__(self):
        "x.__repr__() <==> repr(x)"

        if self.channel is not None and self.target is not None:
            channelStr = "%s:%s" % (self.target, self.channel)
        elif self.channel is not None:
            channelStr = self.channel
        else:
            channelStr = ""
        argsStr = ", ".join([("%s" % repr(arg)) for arg in self.args])
        kwargsStr = ", ".join(
                [("%s=%s" % kwarg) for kwarg in self.kwargs.iteritems()])
        return "<%s[%s] (%s, %s)>" % (self.name, channelStr, argsStr, kwargsStr)

    def __getitem__(self, x):
        """x.__getitem__(y) <==> x[y]

        Get and return data from the Event object requested by "x".
        If an int is passed to x, the requested argument from self.args
        is returned index by x. If a str is passed to x, the requested
        keyword argument from self.kwargs is returned keyed by x.
        Otherwise a TypeError is raised as nothing else is valid.
        """

        if type(x) == int:
            return self.args[x]
        elif type(x) == str:
            return self.kwargs[x]
        else:
            raise TypeError("Expected int or str, got %r" % type(x))


class Error(Event):
    """Error Event

    This Event is sent for any exceptions that occur during the execution
    of an Event Handler that is not SystemExit or KeyboardInterrupt.

    @param type: type of exception
    @type type: type

    @param value: exception object
    @type value: exceptions.TypeError

    @param traceback: traceback of exception
    @type traceback: traceback
    """

    def __init__(self, type, value, traceback):
        "x.__init__(...) initializes x; see x.__class__.__doc__ for signature"

        super(Error, self).__init__(type, value, traceback)


class Started(Event):
    """Started Event

    This Event is sent when a Component has started running.

    @param component: The component that was started
    @type  component: Component or Manager
    """

    def __init__(self, component):
        "x.__init__(...) initializes x; see x.__class__.__doc__ for signature"

        super(Started, self).__init__(component)


class Stopped(Event):
    """Stopped Event

    This Event is sent when a Component has stopped running.

    @param component: The component that has stopped
    @type  component: Component or Manager
    """

    def __init__(self, component):
        "x.__init__(...) initializes x; see x.__class__.__doc__ for signature"

        super(Stopped, self).__init__(component)


class Registered(Event):
    """Registered Event

    This Event is sent when a Component has registered with another Component
    or Manager. This Event is only sent iif the Component or Manager being
    registered with is not itself.

    @param component: The Component being registered
    @type  component: Component

    @param manager: The Component or Manager being registered with
    @type  manager: Component or Manager
    """

    def __init__(self, component, manager):
        "x.__init__(...) initializes x; see x.__class__.__doc__ for signature"

        super(Registered, self).__init__(component, manager)

class Unregistered(Event):
    """Unregistered Event

    This Event is sent when a Component has been unregistered from it's
    Component or Manager.
    """

    def __init__(self, component, manager):
        "x.__init__(...) initializes x; see x.__class__.__doc__ for signature"

        super(Unregistered, self).__init__(component, manager)


def handler(*channels, **kwargs):
    """Creates an Event Handler

    Decorator to wrap a callable into an Event Handler that
    listens on a set of channels defined by channels. The type
    of the Event Handler defaults to "listener". If kwargs["filter"]
    is defined and is True, the Event Handler is defined as a
    Filter and has priority over Listener Event Handlers.
    If kwargs["target"] is defined and is not None, the
    Event Handler will listen for the spcified channels on the
    spcified Target Component's Channel.
    
    Examples:

    >>> from circuits.core import handler
    >>> @handler("foo")
    ... def foo():
    ...     pass
    >>> @handler("bar", filter=True)
    ... def bar():
    ...     pass
    >>> @handler("foo", "bar")
    ... def foobar():
    ...     pass
    >>> @handler("x", target="other")
    ... def x():
    ...     pass
    """

    def wrapper(f):
        f.handler = True

        if "type" in kwargs:
            warnings.warn("Please use 'filter', 'type' will be deprecated in 1.2")
            f.filter = kwargs.get("type", "listener") == "filter"
        else:
            f.filter = kwargs.get("filter", False)

        f.target = kwargs.get("target", None)
        f.channels = channels

        _argspec = getargspec(f)
        _args = _argspec[0]
        if _args and _args[0] == "self":
            del _args[0]
        if _args and _args[0] == "event":
            f._passEvent = True
        else:
            f._passEvent = False

        return f

    return wrapper

def listener(*channels, **kwargs):
    warnings.warn("Please use @handler, @listener will be deprecated in 1.2")
    return handler(*channels, **kwargs)

class HandlersType(type):

    def __init__(cls, name, bases, dct):
        super(HandlersType, cls).__init__(name, bases, dct)

        for k, v in dct.iteritems():
            if callable(v) and not (k[0] == "_" or hasattr(v, "handler")):
                setattr(cls, k, handler(k)(v))


class Manager(object):
    """Creates a new Manager

    Create a new Event manager which manages Components and Events.
    """

    def __init__(self, *args, **kwargs):
        "initializes x; see x.__class__.__doc__ for signature"

        self._queue = deque()
        self._handlers = set()
        self._channels = defaultdict(list)

        self._ticks = set()
        self._hidden = set()
        self._components = set()

        self._task = None
        self._running = False

        self.manager = self

    def __repr__(self):
        "x.__repr__() <==> repr(x)"

        name = self.__class__.__name__
        q = len(self._queue)
        c = len(self._channels)
        h = len(self._handlers)
        state = self.state
        format = "<%s (q: %d c: %d h: %d) [%s]>"
        return format % (name, q, c, h, state)

    def __len__(self):
        """x.__len__() <==> len(x)

        Returns the number of Events in the x's queue.
        """

        return len(self._queue)

    def __add__(self, y):
        """x.__add__(y) <==> x+y

        (Optional) Convenience operator to register y with x
        Equivalent to: y.register(x)

        Returns x
        """

        y.register(self)
        return self
    
    def __iadd__(self, y):
        """x.__iadd__(y) <==> x += y

        (Optional) Convenience operator to register y with x
        Equivalent to: y.register(x)

        Returns and Assigns to x
        """

        y.register(self)
        return self

    def __sub__(self, y):
        """x.__sub__(y) <==> x-y

        (Optional) Convenience operator to unregister y from x.manager
        Equivalent to: y.unregister()

        Returns x
        """

        if y.manager == self:
            y.unregister()
            return self
        else:
            raise TypeError("No registration found for %r" % y)

    def __isub__(self, y):
        """x.__sub__(y) <==> x -= y

        (Optional) Convenience operator to unregister y from x
        Equivalent to: y.unregister()

        Returns and Assigns to x
        """

        if y.manager == self:
            y.unregister()
            return self
        else:
            raise TypeError("No registration found for %r" % y)

    def handlers(self, s):
        if s == "*:*":
            return self._handlers

        if ":" in s:
            target, channel = s.split(":", 1)
        else:
            channel = s
            target = None

        channels = self.channels
        globals = channels["*"]

        if target == "*":
            c = ":%s" % channel
            x = [channels[k] for k in channels if k == channel or k.endswith(c)]
            all = [i for y in x for i in y]
            return chain(globals, all)

        if channel == "*":
            c = "%s:" % target
            x = [channels[k] for k in channels if k.startswith(c) or ":" not in k]
            all = [i for y in x for i in y]
            return chain(globals, all)

        handlers = globals
        if channel in channels:
            handlers = chain(handlers, channels[channel])
        if target and "%s:*" % target in channels:
            handlers = chain(handlers, channels["%s:*" % target])
        if "*:%s" % channel in channels:
            handlers = chain(handlers, channels["*:%s" % channel])
        if target:
            handlers = chain(handlers, channels[s])

        return handlers

    @property
    def state(self):
        if self._running:
            if self._task is None:
                return "R"
            else:
                if self._task.is_alive():
                    return "R"
                else:
                    return "D"
        else:
            return "S"

    @property
    def running(self):
        return self._running

    @property
    def components(self):
        return self._components

    @property
    def channels(self):
        return self._channels

    @property
    def hidden(self):
        return self._hidden

    @property
    def ticks(self):
        return self._ticks

    def _add(self, handler, channel=None):
        """E._add(handler, channel) -> None

        Add a new Event Handler to the Event Manager
        adding it to the given channel. If no channel is
        given, add it to the global channel.
        """

        self._handlers.add(handler)

        if channel is None:
            channel = "*"

        if channel in self.channels:
            if handler not in self.channels[channel]:
                self._channels[channel].append(handler)
                self._channels[channel].sort(key=lambda x: not x.filter)
        else:
            self._channels[channel] = [handler]

    def _remove(self, handler, channel=None):
        """E._remove(handler, channel=None) -> None

        Remove the given Event Handler from the Event Manager
        removing it from the given channel. if channel is None,
        remove it from all channels. This will succeed even
        if the specified  handler has already been removed.
        """

        if channel is None:
            channels = self.channels.keys()
        else:
            channels = [channel]

        if handler in self._handlers:
            self._handlers.remove(handler)

        for channel in channels:
            if handler in self.channels[channel]:
                self._channels[channel].remove(handler)
            if not self._channels[channel]:
                del self._channels[channel]


    def push(self, event, channel, target=None):
        """Push a new Event into the queue

        This will push the given Event, Channel and Target onto the
        Event Queue for later processing.

        if target is None, then target will be set as the Channel of
        the current Component, self.channel (defaulting back to None).

        If this Component's Manager is itself, enqueue on this Component's
        Event Queue, otherwise enqueue on this Component's Manager.

        @param event: The Event Object
        @type  event: Event

        @param channel: The Channel this Event is bound for
        @type  channel: str

        @keyword target: The target Component's channel this Event is bound for
        @type    target: str or Component
        """

        if target is None:
            target = getattr(self, "channel", None)

        if self.manager == self:
            self._queue.append((event, channel, target))
        else:
            self.manager.push(event, channel, target)

    def flush(self):
        """Flush all Events in the Event Queue

        This will flush all Events in the Event Queue. If this Component's
        Manager is itself, flush all Events from this Component's Event Queue,
        otherwise, flush all Events from this Component's Manager's Event Queue.
        """

        if self.manager == self:
            q = self._queue
            self._queue = deque()
            while q:
                event, channel, target = q.popleft()
                self.send(event, channel, target)
        else:
            self.manager.flush()

    def send(self, event, channel, target=None, errors=False, log=True):
        """E.send(event, channel, target=None, errors=False) -> None

        Send the given Event to all Event Handlers on the channel
        specified. If target is not None, send this event to
        Event Handlers of the spcified target Component's channel.
        """

        if target is None:
            target = getattr(self, "channel", None)

        if self.manager == self:
            event.channel = channel
            event.target = target
            eargs = event.args
            ekwargs = event.kwargs
            if target is not None and isinstance(target, Component):
                target = getattr(target, "channel", None)
            if target is not None and type(target) == str:
                channel = "%s:%s" % (target, channel)

            r = False
            for handler in self.handlers(channel):
                try:
                    if handler._passEvent:
                        r = partial(handler, event, *eargs, **ekwargs)()
                    else:
                        r = partial(handler, *eargs, **ekwargs)()
                except (KeyboardInterrupt, SystemExit):
                    raise
                except:
                    if log:
                        self.push(Error(*_exc_info()), "error")
                    if errors:
                        raise
                    else:
                        _exc_clear()
                if r is not None and r and handler.filter:
                    return r
            return r
        else:
            return self.manager.send(event, channel, target, errors, log)

    def start(self, sleep=0, errors=False, log=True, process=False):
        group = None
        target = self.run
        name = self.__class__.__name__
        args = (sleep, errors, log,)

        if process and HAS_MULTIPROCESSING:
            args += (self,)
            self._task = Process(group, target, name, args)
            if HAS_MULTIPROCESSING == 1:
                setattr(self._task, "is_alive", self._task.isAlive)
            self._task.start()
            return

        self._task = Thread(group, target, name, args)
        self._task.setDaemon(True)
        self._task.start()

    def stop(self):
        self._running = False
        if hasattr(self._task, "terminate"):
            self._task.terminate()
        if hasattr(self._task, "join"):
            self._task.join(5)
        self._task = None

    def run(self, sleep=0, errors=False, log=True, __self=None):
        if __self is not None:
            self = __self

        self._running = True

        self.push(Started(), "started")

        try:
            while self._running or (self._running and self._task is not None and self._task.is_alive()):
                try:
                    [f() for f in self.ticks.copy()]
                    self.flush()
                    if sleep:
                        time.sleep(sleep)
                except (KeyboardInterrupt, SystemExit):
                    self._running = False
                    if hasattr(self._task, "terminate"):
                        self._task.terminate()
                except:
                    if log:
                        self.push(Error(*_exc_info()), "error")
                    if errors:
                        raise
                    else:
                        _exc_clear()
        finally:
            self.push(Stopped(), "stopped")
            rtime = time.time()
            while len(self) > 0 and (time.time() - rtime) < 3:
                [f() for f in self.ticks.copy()]
                self.flush()
                if sleep:
                    time.sleep(sleep)
                rtime = time.time()

class BaseComponent(Manager):

    channel = None

    def __new__(cls, *args, **kwargs):
        """TODO Work around for Python bug.

        Bug: http://bugs.python.org/issue5322
        """

        return object.__new__(cls)

    def __init__(self, *args, **kwargs):
        "initializes x; see x.__class__.__doc__ for signature"

        super(BaseComponent, self).__init__(*args, **kwargs)

        self.channel = kwargs.get("channel", self.channel)
        self.register(self)

    def __repr__(self):
        "x.__repr__() <==> repr(x)"

        name = self.__class__.__name__
        channel = self.channel or ""
        q = len(self._queue)
        c = len(self._channels)
        h = len(self._handlers)
        state = self.state
        format = "<%s/%s (q: %d c: %d h: %d) [%s]>"
        return format % (name, channel, q, c, h, state)

    def __call__(self, channel, *args, **kwargs):
        e = Event(*args, **kwargs)
        e.name = channel.title()
        return self.send(e, channel, self.channel)

    def _registerHidden(self):
        d = 0
        i = 0
        x = self
        stack = []
        done = False
        hidden = set()
        visited = set()
        children = list(x.components)
        while not done:
            if x not in visited:
                p1 = x is not self
                p2 = x.manager is not self
                p3 = x not in self.manager.components
                p4 = x.manager not in hidden
                if p1 and (p2 or p3) and p4:
                    hidden.add(x)
                visited.add(x)
                if x.components:
                    d += 1

            if i < len(children):
                x = children[i]
                i += 1
                if x.components:
                    stack.append((i, children))
                    children = list(x.components)
                    i = 0
            else:
                if stack:
                    i, children = stack.pop()
                    d -= 1
                else:
                    done = True

        for x in hidden:
            x.register(self.manager)

        self.manager._hidden.update(hidden)

        pmanager = self.manager.manager
        if self.manager is not pmanager:
            hidden.add(self)
            self.register(pmanager)

        self.manager._components.difference_update(hidden)

    def _getTicks(self):
        ticks = set()
        if hasattr(self, "__tick__"):
            ticks.add(self.__tick__)
        for v in vars(self).itervalues():
            if isinstance(v, Component) and hasattr(v, "__tick__"):
                ticks.add(v.__tick__)
        for component in self.components:
            if hasattr(component, "__tick__"):
                ticks.add(component.__tick__)
        for component in self.hidden:
            if hasattr(component, "__tick__"):
                ticks.add(component.__tick__)
        return ticks

    def register(self, manager):
        p = lambda x: callable(x) and getattr(x, "handler", False)
        handlers = [v for k, v in getmembers(self, p)]

        for handler in handlers:
            if handler.channels:
                channels = handler.channels
            else:
                channels = ["*"]

            for channel in channels:
                if handler.target is not None:
                    target = handler.target
                else:
                    target = self.channel

                if target is not None:
                    channel = "%s:%s" % (target, channel)

                manager._add(handler, channel)

        self.manager = manager

        if manager is not self:
            manager._components.add(self)
            self.push(Registered(self, manager), "registered", self.channel)
            self._registerHidden()

        self.manager._ticks.update(self._getTicks())

    def unregister(self):
        "Unregister all registered event handlers from the manager."

        manager = self.manager

        for handler in self._handlers.copy():
            manager._remove(handler)

        if self in manager._components.copy():
            manager._components.remove(self)

        manager._ticks.difference_update(self._getTicks())

        self.push(Unregistered(self, manager), "unregistered", self.channel)

        self.manager = self

class Component(BaseComponent):
    """Creates a new Component

    Subclasses of Component define Event Handlers by decorating
    their methods with the handler decorator.

    All Event Handlers found in the Component will automatically be
    picked up when the Component and registered to it's Manager.

    All methods defined in a Component are automatically turned into
    Event Handlers, configured to listen on a channel of the same
    name as the method. The exception to this is any method that starts
    with a single _ or any method already previously defined as an
    Event Handlers with the @handler decorator.
    """

    __metaclass__ = HandlersType

    def __new__(cls, *args, **kwargs):
        self = BaseComponent.__new__(cls, *args, **kwargs)
        for base in cls.__bases__:
            if issubclass(cls, base):
                for k, v in base.__dict__.iteritems():
                    if callable(v) and getattr(v, "handler", False):
                        name = "%s_%s" % (base.__name__, k)
                        method = new.instancemethod(v, self, cls)
                        setattr(self, name, method)
        return self

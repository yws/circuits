#!/usr/bin/env python


from circuits import handler, Event, Component
from circuits.protocols.irc import strip, sourceJoin, sourceSplit, IRC

from circuits.protocols.irc import (
    PASS, USER, NICK, PING, PONG, QUIT,
    JOIN, PART, PRIVMSG, NOTICE, CTCP, CTCPREPLY,
    KICK, TOPIC, MODE, INVITE, NAMES, WHOIS, AWAY
)


class read(Event):
    """read Event"""


class App(Component):

    def __init__(self):
        super(App, self).__init__()

        IRC().register(self)

        self.data = []
        self.events = []

    @handler(False)
    def reset(self):
        self.data = []
        self.events = []

    @handler(channel="*", priority=101.0)
    def event(self, event, *args, **kwargs):
        self.events.append(event)

    def write(self, data):
        self.data.append(data)


def pytest_funcarg__app(request):
    return request.cached_setup(
        setup=lambda: setupapp(request),
        scope="module"
    )


def setupapp(request):
    app = App()
    while app:
        app.flush()
    app.reset()
    return app


def test_strip():
    s = ":\x01\x02test\x02\x01"
    s = strip(s)
    assert s == "\x01\x02test\x02\x01"

    s = ":\x01\x02test\x02\x01"
    s = strip(s, color=True)
    assert s == "test"


def test_sourceJoin():
    nick, ident, host = "test", "foo", "localhost"
    s = sourceJoin(nick, ident, host)
    assert s == "test!foo@localhost"


def test_sourceSplit():
    s = "test!foo@localhost"
    nick, ident, host = sourceSplit(s)
    assert nick == "test"
    assert ident == "foo"
    assert host == "localhost"

    s = "test"
    nick, ident, host = sourceSplit(s)
    assert nick == "test"
    assert ident is None
    assert host is None


def test_PASS(app):
    app.reset()

    app.fire(PASS("secret"))
    while app:
        app.flush()

    events = iter(app.events)

    e = next(events)
    assert e.name == "PASS"
    assert e.args[0] == "secret"

    e = next(events)
    assert e.name == "RAW"
    assert e.args[0] == "PASS secret"

    e = next(events)
    assert e.name == "write"
    assert e.args[0] == b"PASS secret\r\n"

    data = iter(app.data)

    s = next(data)
    assert s == b"PASS secret\r\n"


def test_USER(app):
    app.reset()

    app.fire(USER("foo", "localhost", "localhost", "Test Client"))
    while app:
        app.flush()

    events = iter(app.events)

    e = next(events)
    assert e.name == "USER"
    assert e.args[0] == "foo"
    assert e.args[1] == "localhost"
    assert e.args[2] == "localhost"
    assert e.args[3] == "Test Client"

    e = next(events)
    assert e.name == "RAW"
    assert e.args[0] == "USER foo localhost localhost :Test Client"

    e = next(events)
    assert e.name == "write"
    assert e.args[0] == b"USER foo localhost localhost :Test Client\r\n"

    data = iter(app.data)

    s = next(data)
    assert s == b"USER foo localhost localhost :Test Client\r\n"


def test_NICK(app):
    app.reset()

    app.fire(NICK("test"))
    while app:
        app.flush()

    events = iter(app.events)

    e = next(events)
    assert e.name == "NICK"
    assert e.args[0] == "test"

    e = next(events)
    assert e.name == "RAW"
    assert e.args[0] == "NICK test"

    e = next(events)
    assert e.name == "write"
    assert e.args[0] == b"NICK test\r\n"

    data = iter(app.data)

    s = next(data)
    assert s == b"NICK test\r\n"


def test_PING(app):
    app.reset()

    app.fire(PING("localhost"))
    while app:
        app.flush()

    events = iter(app.events)

    e = next(events)
    assert e.name == "PING"
    assert e.args[0] == "localhost"

    e = next(events)
    assert e.name == "RAW"
    assert e.args[0] == "PING :localhost"

    e = next(events)
    assert e.name == "write"
    assert e.args[0] == b"PING :localhost\r\n"

    data = iter(app.data)

    s = next(data)
    assert s == b"PING :localhost\r\n"


def test_PONG(app):
    app.reset()

    app.fire(PONG("localhost"))
    while app:
        app.flush()

    events = iter(app.events)

    e = next(events)
    assert e.name == "PONG"
    assert e.args[0] == "localhost"

    e = next(events)
    assert e.name == "RAW"
    assert e.args[0] == "PONG :localhost"

    e = next(events)
    assert e.name == "write"
    assert e.args[0] == b"PONG :localhost\r\n"

    data = iter(app.data)

    s = next(data)
    assert s == b"PONG :localhost\r\n"


def test_QUIT(app):
    app.reset()

    app.fire(QUIT())
    while app:
        app.flush()

    events = iter(app.events)

    e = next(events)
    assert e.name == "QUIT"
    assert not e.args

    e = next(events)
    assert e.name == "RAW"
    assert e.args[0] == "QUIT :Leaving"

    e = next(events)
    assert e.name == "write"
    assert e.args[0] == b"QUIT :Leaving\r\n"

    data = iter(app.data)

    s = next(data)
    assert s == b"QUIT :Leaving\r\n"

    app.reset()

    app.fire(QUIT("Test"))
    while app:
        app.flush()

    events = iter(app.events)

    e = next(events)
    assert e.name == "QUIT"
    assert e.args[0] == "Test"

    e = next(events)
    assert e.name == "RAW"
    assert e.args[0] == "QUIT :Test"

    e = next(events)
    assert e.name == "write"
    assert e.args[0] == b"QUIT :Test\r\n"

    data = iter(app.data)

    s = next(data)
    assert s == b"QUIT :Test\r\n"


def test_JOIN(app):
    app.reset()

    app.fire(JOIN("#test"))
    while app:
        app.flush()

    events = iter(app.events)

    e = next(events)
    assert e.name == "JOIN"
    assert e.args[0] == "#test"

    e = next(events)
    assert e.name == "RAW"
    assert e.args[0] == "JOIN #test"

    e = next(events)
    assert e.name == "write"
    assert e.args[0] == b"JOIN #test\r\n"

    data = iter(app.data)

    s = next(data)
    assert s == b"JOIN #test\r\n"

    app.reset()

    app.fire(JOIN("#test", "secret"))
    while app:
        app.flush()

    events = iter(app.events)

    e = next(events)
    assert e.name == "JOIN"
    assert e.args[0] == "#test"
    assert e.args[1] == "secret"

    e = next(events)
    assert e.name == "RAW"
    assert e.args[0] == "JOIN #test secret"

    e = next(events)
    assert e.name == "write"
    assert e.args[0] == b"JOIN #test secret\r\n"

    data = iter(app.data)

    s = next(data)
    assert s == b"JOIN #test secret\r\n"


def test_PART(app):
    app.reset()

    app.fire(PART("#test"))
    while app:
        app.flush()

    events = iter(app.events)

    e = next(events)
    assert e.name == "PART"
    assert e.args[0] == "#test"

    e = next(events)
    assert e.name == "RAW"
    assert e.args[0] == "PART #test :Leaving"

    e = next(events)
    assert e.name == "write"
    assert e.args[0] == b"PART #test :Leaving\r\n"

    data = iter(app.data)

    s = next(data)
    assert s == b"PART #test :Leaving\r\n"

    app.reset()

    app.fire(PART("#test", "Test"))
    while app:
        app.flush()

    events = iter(app.events)

    e = next(events)
    assert e.name == "PART"
    assert e.args[0] == "#test"
    assert e.args[1] == "Test"

    e = next(events)
    assert e.name == "RAW"
    assert e.args[0] == "PART #test :Test"

    e = next(events)
    assert e.name == "write"
    assert e.args[0] == b"PART #test :Test\r\n"

    data = iter(app.data)

    s = next(data)
    assert s == b"PART #test :Test\r\n"


def test_PRIVMSG(app):
    app.reset()

    app.fire(PRIVMSG("test", "Hello"))
    while app:
        app.flush()

    events = iter(app.events)

    e = next(events)
    assert e.name == "PRIVMSG"
    assert e.args[0] == "test"
    assert e.args[1] == "Hello"

    e = next(events)
    assert e.name == "RAW"
    assert e.args[0] == "PRIVMSG test :Hello"

    e = next(events)
    assert e.name == "write"
    assert e.args[0] == b"PRIVMSG test :Hello\r\n"

    data = iter(app.data)

    s = next(data)
    assert s == b"PRIVMSG test :Hello\r\n"


def test_NOTICE(app):
    app.reset()

    app.fire(NOTICE("test", "Hello"))
    while app:
        app.flush()

    events = iter(app.events)

    e = next(events)
    assert e.name == "NOTICE"
    assert e.args[0] == "test"
    assert e.args[1] == "Hello"

    e = next(events)
    assert e.name == "RAW"
    assert e.args[0] == "NOTICE test :Hello"

    e = next(events)
    assert e.name == "write"
    assert e.args[0] == b"NOTICE test :Hello\r\n"

    data = iter(app.data)

    s = next(data)
    assert s == b"NOTICE test :Hello\r\n"


def test_CTCP(app):
    app.reset()

    app.fire(CTCP("test", "PING", "1234567890"))
    while app:
        app.flush()

    events = iter(app.events)

    e = next(events)
    assert e.name == "CTCP"
    assert e.args[0] == "test"
    assert e.args[1] == "PING"
    assert e.args[2] == "1234567890"

    e = next(events)
    assert e.name == "PRIVMSG"
    assert e.args[0] == "test"
    assert e.args[1] == "PING 1234567890"

    e = next(events)
    assert e.name == "RAW"
    assert e.args[0] == "PRIVMSG test :PING 1234567890"

    e = next(events)
    assert e.name == "write"
    assert e.args[0] == b"PRIVMSG test :PING 1234567890\r\n"

    data = iter(app.data)

    s = next(data)
    assert s == b"PRIVMSG test :PING 1234567890\r\n"


def test_CTCPREPLY(app):
    app.reset()

    app.fire(CTCPREPLY("test", "PING", "1234567890"))
    while app:
        app.flush()

    events = iter(app.events)

    e = next(events)
    assert e.name == "CTCPREPLY"
    assert e.args[0] == "test"
    assert e.args[1] == "PING"
    assert e.args[2] == "1234567890"

    e = next(events)
    assert e.name == "NOTICE"
    assert e.args[0] == "test"
    assert e.args[1] == "PING 1234567890"

    e = next(events)
    assert e.name == "RAW"
    assert e.args[0] == "NOTICE test :PING 1234567890"

    e = next(events)
    assert e.name == "write"
    assert e.args[0] == b"NOTICE test :PING 1234567890\r\n"

    data = iter(app.data)

    s = next(data)
    assert s == b"NOTICE test :PING 1234567890\r\n"


def test_KICK(app):
    app.reset()

    app.fire(KICK("#test", "test"))
    while app:
        app.flush()

    events = iter(app.events)

    e = next(events)
    assert e.name == "KICK"
    assert e.args[0] == "#test"
    assert e.args[1] == "test"

    e = next(events)
    assert e.name == "RAW"
    assert e.args[0] == "KICK #test test :"

    e = next(events)
    assert e.name == "write"
    assert e.args[0] == b"KICK #test test :\r\n"

    data = iter(app.data)

    s = next(data)
    assert s == b"KICK #test test :\r\n"

    app.reset()

    app.fire(KICK("#test", "test", "Bye"))
    while app:
        app.flush()

    events = iter(app.events)

    e = next(events)
    assert e.name == "KICK"
    assert e.args[0] == "#test"
    assert e.args[1] == "test"
    assert e.args[2] == "Bye"

    e = next(events)
    assert e.name == "RAW"
    assert e.args[0] == "KICK #test test :Bye"

    e = next(events)
    assert e.name == "write"
    assert e.args[0] == b"KICK #test test :Bye\r\n"

    data = iter(app.data)

    s = next(data)
    assert s == b"KICK #test test :Bye\r\n"


def test_TOPIC(app):
    app.reset()

    app.fire(TOPIC("#test", "Hello World!"))
    while app:
        app.flush()

    events = iter(app.events)

    e = next(events)
    assert e.name == "TOPIC"
    assert e.args[0] == "#test"
    assert e.args[1] == "Hello World!"

    e = next(events)
    assert e.name == "RAW"
    assert e.args[0] == "TOPIC #test :Hello World!"

    e = next(events)
    assert e.name == "write"
    assert e.args[0] == b"TOPIC #test :Hello World!\r\n"

    data = iter(app.data)

    s = next(data)
    assert s == b"TOPIC #test :Hello World!\r\n"


def test_MODE(app):
    app.reset()

    app.fire(MODE("+i"))
    while app:
        app.flush()

    events = iter(app.events)

    e = next(events)
    assert e.name == "MODE"
    assert e.args[0] == "+i"

    e = next(events)
    assert e.name == "RAW"
    assert e.args[0] == "MODE :+i"

    e = next(events)
    assert e.name == "write"
    assert e.args[0] == b"MODE :+i\r\n"

    data = iter(app.data)

    s = next(data)
    assert s == b"MODE :+i\r\n"

    app.reset()

    app.fire(MODE("+o test", "#test"))
    while app:
        app.flush()

    events = iter(app.events)

    e = next(events)
    assert e.name == "MODE"
    assert e.args[0] == "+o test"
    assert e.args[1] == "#test"

    e = next(events)
    assert e.name == "RAW"
    assert e.args[0] == "MODE #test :+o test"

    e = next(events)
    assert e.name == "write"
    assert e.args[0] == b"MODE #test :+o test\r\n"

    data = iter(app.data)

    s = next(data)
    assert s == b"MODE #test :+o test\r\n"


def test_INVITE(app):
    app.reset()

    app.fire(INVITE("test", "#test"))
    while app:
        app.flush()

    events = iter(app.events)

    e = next(events)
    assert e.name == "INVITE"
    assert e.args[0] == "test"
    assert e.args[1] == "#test"

    e = next(events)
    assert e.name == "RAW"
    assert e.args[0] == "INVITE test #test"

    e = next(events)
    assert e.name == "write"
    assert e.args[0] == b"INVITE test #test\r\n"

    data = iter(app.data)

    s = next(data)
    assert s == b"INVITE test #test\r\n"


def test_NAMES(app):
    app.reset()

    app.fire(NAMES())
    while app:
        app.flush()

    events = iter(app.events)

    e = next(events)
    assert e.name == "NAMES"
    assert not e.args

    e = next(events)
    assert e.name == "RAW"
    assert e.args[0] == "NAMES"

    e = next(events)
    assert e.name == "write"
    assert e.args[0] == b"NAMES\r\n"

    data = iter(app.data)

    s = next(data)
    assert s == b"NAMES\r\n"

    app.reset()

    app.fire(NAMES("#test"))
    while app:
        app.flush()

    events = iter(app.events)

    e = next(events)
    assert e.name == "NAMES"
    assert e.args[0] == "#test"

    e = next(events)
    assert e.name == "RAW"
    assert e.args[0] == "NAMES #test"

    e = next(events)
    assert e.name == "write"
    assert e.args[0] == b"NAMES #test\r\n"

    data = iter(app.data)

    s = next(data)
    assert s == b"NAMES #test\r\n"


def test_AWAY(app):
    app.reset()

    app.fire(AWAY("I am away."))
    while app:
        app.flush()

    events = iter(app.events)

    e = next(events)
    assert e.name == "AWAY"
    assert e.args[0] == "I am away."

    e = next(events)
    assert e.name == "RAW"
    assert e.args[0] == "AWAY :I am away."

    e = next(events)
    assert e.name == "write"
    assert e.args[0] == b"AWAY :I am away.\r\n"


def test_WHOIS(app):
    app.reset()

    app.fire(WHOIS("somenick"))
    while app:
        app.flush()

    events = iter(app.events)

    e = next(events)
    assert e.name == "WHOIS"
    assert e.args[0] == "somenick"

    e = next(events)
    assert e.name == "RAW"
    assert e.args[0] == "WHOIS :somenick"

    e = next(events)
    assert e.name == "write"
    assert e.args[0] == b"WHOIS :somenick\r\n"


def test_ping(app):
    app.reset()

    app.fire(read(b"PING :localhost\r\n"))
    while app:
        app.flush()

    events = iter(app.events)

    e = next(events)
    assert e.name == "read"
    assert e.args[0] == b"PING :localhost\r\n"

    e = next(events)
    assert e.name == "line"
    assert e.args[0] == b"PING :localhost"

    e = next(events)
    assert e.name == "ping"
    assert e.args == [("", None, None), "localhost"]

    e = next(events)
    assert e.name == "PONG"
    assert e.args[0] == "localhost"

    e = next(events)
    assert e.name == "RAW"
    assert e.args[0] == "PONG :localhost"

    e = next(events)
    assert e.name == "write"
    assert e.args[0] == b"PONG :localhost\r\n"

    data = iter(app.data)

    s = next(data)
    assert s == b"PONG :localhost\r\n"


def test_numerics(app):
    app.reset()

    app.fire(read(
        b":localhost 001 test " +
        b":Welcome to the circuits Internet Relay Chat Network test\r\n"
    ))

    while app:
        app.flush()

    events = iter(app.events)

    e = next(events)
    assert e.name == "read"
    assert e.args[0] == b":localhost 001 test " \
        b":Welcome to the circuits Internet Relay Chat Network test\r\n"

    e = next(events)
    assert e.name == "line"
    assert e.args[0] == (
        b":localhost 001 test "
        b":Welcome to the circuits Internet Relay Chat Network test"
    )

    e = next(events)
    assert e.name == "numeric"
    print(repr(e.args))
    assert e.args == [
        ('localhost', None, None),
        1, 'test',
        'Welcome to the circuits Internet Relay Chat Network test'
    ]

    app.reset()

    app.fire(read(b":localhost 332 test #test :Hello World!\r\n"))
    while app:
        app.flush()

    events = iter(app.events)

    e = next(events)
    assert e.name == "read"
    assert e.args[0] == b":localhost 332 test #test :Hello World!\r\n"

    e = next(events)
    assert e.name == "line"
    assert e.args[0] == b":localhost 332 test #test :Hello World!"

    e = next(events)
    assert e.name == "numeric"
    assert e.args == [
        ("localhost", None, None),
        332, "test", "#test", "Hello World!"
    ]


def test_privmsg(app):
    app.reset()

    app.fire(read(b":test!foo@localhost PRIVMSG test :Hello\r\n"))
    while app:
        app.flush()

    events = iter(app.events)

    e = next(events)
    assert e.name == "read"
    assert e.args[0] == b":test!foo@localhost PRIVMSG test :Hello\r\n"

    e = next(events)
    assert e.name == "line"
    assert e.args[0] == b":test!foo@localhost PRIVMSG test :Hello"

    e = next(events)
    assert e.name == "privmsg"
    assert e.args == [
        ("test", "foo", "localhost"),
        "test", "Hello"
    ]


def test_notice(app):
    app.reset()

    app.fire(read(b":test!foo@localhost NOTICE test :Hello\r\n"))
    while app:
        app.flush()

    events = iter(app.events)

    e = next(events)
    assert e.name == "read"
    assert e.args[0] == b":test!foo@localhost NOTICE test :Hello\r\n"

    e = next(events)
    assert e.name == "line"
    assert e.args[0] == b":test!foo@localhost NOTICE test :Hello"

    e = next(events)
    assert e.name == "notice"
    assert e.args[0] == ("test", "foo", "localhost")
    assert e.args[1] == "test"
    assert e.args[2] == "Hello"


def test_join(app):
    app.reset()

    app.fire(read(b":test!foo@localhost JOIN #test\r\n"))
    while app:
        app.flush()

    events = iter(app.events)

    e = next(events)
    assert e.name == "read"
    assert e.args[0] == b":test!foo@localhost JOIN #test\r\n"

    e = next(events)
    assert e.name == "line"
    assert e.args[0] == b":test!foo@localhost JOIN #test"

    e = next(events)
    assert e.name == "join"
    assert e.args[0] == ("test", "foo", "localhost")
    assert e.args[1] == "#test"


def test_part(app):
    app.reset()

    app.fire(read(b":test!foo@localhost PART #test :Leaving\r\n"))
    while app:
        app.flush()

    events = iter(app.events)

    e = next(events)
    assert e.name == "read"
    assert e.args[0] == b":test!foo@localhost PART #test :Leaving\r\n"

    e = next(events)
    assert e.name == "line"
    assert e.args[0] == b":test!foo@localhost PART #test :Leaving"

    e = next(events)
    assert e.name == "part"
    assert e.args[0] == ("test", "foo", "localhost")
    assert e.args[1] == "#test"
    assert e.args[2] == "Leaving"


def test_quit(app):
    app.reset()

    app.fire(read(b":test!foo@localhost QUIT :Leaving\r\n"))
    while app:
        app.flush()

    events = iter(app.events)

    e = next(events)
    assert e.name == "read"
    assert e.args[0] == b":test!foo@localhost QUIT :Leaving\r\n"

    e = next(events)
    assert e.name == "line"
    assert e.args[0] == b":test!foo@localhost QUIT :Leaving"

    e = next(events)
    assert e.name == "quit"
    assert e.args[0] == ("test", "foo", "localhost")
    assert e.args[1] == "Leaving"


def test_nick(app):
    app.reset()

    app.fire(read(b":test!foo@localhost NICK :test_\r\n"))
    while app:
        app.flush()

    events = iter(app.events)

    e = next(events)
    assert e.name == "read"
    assert e.args[0] == b":test!foo@localhost NICK :test_\r\n"

    e = next(events)
    assert e.name == "line"
    assert e.args[0] == b":test!foo@localhost NICK :test_"

    e = next(events)
    assert e.name == "nick"
    assert e.args[0] == ("test", "foo", "localhost")
    assert e.args[1] == "test_"


def test_mode(app):
    app.reset()

    app.fire(read(b":test!foo@localhost MODE #test +o test\r\n"))
    while app:
        app.flush()

    events = iter(app.events)

    e = next(events)
    assert e.name == "read"
    assert e.args[0] == b":test!foo@localhost MODE #test +o test\r\n"

    e = next(events)
    assert e.name == "line"
    assert e.args[0] == b":test!foo@localhost MODE #test +o test"

    e = next(events)
    assert e.name == "mode"
    assert e.args == [
        ("test", "foo", "localhost"),
        "#test", "+o", "test"
    ]


def test_away(app):
    app.reset()

    app.fire(read(b":irc.example.com 301 circuits somenick :is away\r\n"))
    while app:
        app.flush()

    events = iter(app.events)

    e = next(events)
    assert e.name == "read"
    assert e.args[0] == b":irc.example.com 301 circuits somenick :is away\r\n"

    e = next(events)
    assert e.name == "line"
    assert e.args[0] == b":irc.example.com 301 circuits somenick :is away"

    e = next(events)
    assert e.name == "numeric"
    assert e.args == [
        ("irc.example.com", None, None),
        301, "circuits", "somenick", "is away"
    ]

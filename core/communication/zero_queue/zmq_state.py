"""Module contains the state of the ZeroQueue, such as the mode of the current queue."""

from enum import Enum


class ZeroQueueMode(str, Enum):
    """Enum for ZeroQueue modes."""

    SUB = "SUB"
    PUB = "PUB"


class ZeroQueueConnectionType(str, Enum):
    """Enum for ZeroQueue connection states.

    Connecting to an existing port or binding(hosting) to a new one.
    """

    CONNECT = "connect"
    BIND = "bind"

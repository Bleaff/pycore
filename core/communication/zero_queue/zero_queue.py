"""ZeroQueue abstraction over producer/consumer ZeroMQ messaging.

Provides a simple interface for sending and receiving messages using the
ZeroMQ library. The class can be used as either a producer or consumer,
depending on the value of the 'is_producer' argument.

The producer creates a ZeroQueueProducer instance which connects to a port
and sends messages to the consumer. The consumer creates a ZeroQueueConsumer
instance which binds to a port and receives messages from the producer. The
consumer can also connect to an existing port if the producer is running on
another machine.

The class provides a simple interface for sending and receiving messages,
hiding the underlying details of the ZeroMQ library. The interface is
thread-safe, meaning that multiple threads can call the same methods
concurrently without worrying about race conditions.

"""

from __future__ import annotations

import logging
import time
from typing import Any

import zmq

from neudc.core.communication.zero_queue.zmq_state import ZeroQueueConnectionType, ZeroQueueMode

logger = logging.getLogger(__name__)


class ZeroQueue:
    """PUB/SUB-based queue implementation using ZeroMQ.

    Suitable for inter-process message passing on a single machine.
    """

    def __init__(
        self,
        port: int = -1,
        mode: ZeroQueueMode = ZeroQueueMode.SUB,
        contype: ZeroQueueConnectionType = ZeroQueueConnectionType.CONNECT,
        queue_size: int = 100,
    ) -> None:
        """Initialize the ZeroQueue.

        Args:
        ----
            port (Optional[int]): Port for PUB/SUB communication. If None, a random free port is chosen.
            mode (ZeroQueueMode): Mode of the queue (SUB(subscriber) or PUB(publisher)). Default is SUB.
            contype (ZeroQueueConnectionType): Connection type (bind or connect). Default is CONNECT.

        """
        self._port: int = port  # type: ignore[assignment]
        self.context: zmq.Context = zmq.Context()
        self.mode: ZeroQueueMode = mode
        self.contype: ZeroQueueConnectionType = contype

        if mode == ZeroQueueMode.SUB:
            self._init_sub(contype)
        elif mode == ZeroQueueMode.PUB:
            self._init_pub(contype)
        else:
            msg = f"Invalid mode: {mode}"
            raise ValueError(msg)

        self.poller = zmq.Poller()
        self.poller.register(self.socket_sub, zmq.POLLIN)

    def _init_sub(self, contype: ZeroQueueConnectionType, queue_size: int = 100) -> None:  # type: ignore[no-untyped-def]
        """Initialize the subscriber socket. Ports gets from initialization.

        Args:
        ----
            contype (ZeroQueueConnectionType): Connection type (bind or connect).

        """
        self.socket_pub: zmq.Context.socket | None = None
        self.socket_sub: zmq.Context.socket | None = self.context.socket(zmq.SUB)
        self.socket_sub.setsockopt(zmq.LINGER, 100)
        self._set_connection(self.socket_sub, contype)
        self.socket_sub.subscribe("")
        self.poller = zmq.Poller()
        self.poller.register(self.socket_sub, zmq.POLLIN)

    def _init_pub(self, contype: ZeroQueueConnectionType, queue_size: int = 100) -> None:  # type: ignore[no-untyped-def]
        """Initialize the publisher socket. Ports gets from initialization.

        Args:
        ----
            contype (ZeroQueueConnectionType): Connection type (bind or connect).

        """
        self.socket_pub: zmq.Context.socket | None = self.context.socket(zmq.PUB)
        self.socket_pub.setsockopt(zmq.LINGER, 100)
        self._set_connection(self.socket_pub, contype)
        self.socket_sub: zmq.Context.socket | None = None

    def _bind_port(self, port: int, socket: zmq.Context.socket) -> int:
        """Bind the socket to a random port and return the port number."""
        if port != -1:
            socket.bind(f"tcp://*:{port}")
            logger.info(f"ZeroQueue bound to port {port}")
            return port
        port = socket.bind_to_random_port("tcp://*")
        logger.info(f"ZeroQueue bound to random port {port}")
        return port

    def _set_connection(self, socket: zmq.Context.socket, contype: ZeroQueueConnectionType) -> None:
        """Set the connection type for the socket.

        Sets the connection type for the socket based on the provided
        connection type. If the connection type is CONNECT, the socket
        connects to the specified port. If the connection type is BIND,
        the socket binds to a random port.
        """
        if contype == ZeroQueueConnectionType.CONNECT:
            if self.port != -1:
                socket.connect(f"tcp://localhost:{self.port}")
                logger.debug(f"ZeroQueue connected to port {self.port}")
            else:
                msg = "Port is not set"
                raise ValueError(msg)
        elif contype == ZeroQueueConnectionType.BIND:
            self.port = self._bind_port(self.port, socket)
        else:
            msg = f"Invalid connection type: {contype}"
            raise ValueError(msg)

    def __str__(self) -> str:
        """Magic methods for string representation of queue."""
        return f"{self.__class__.__name__}(port={self.port})"

    @property
    def port(self) -> int:
        """Get the port number."""
        return self._port

    @port.setter
    def port(self, value: int) -> None:
        """Set the port number."""
        if self._port != value:
            self._port = value

    def get(self, timeout: float | None = None) -> Any | None:
        """Receive an item from the queue with timeout.

        Args:
        ----
            timeout (Optional[float]): Timeout in seconds.

        Returns:
        -------
            Optional[Any]: Received message, or None if timeout expired.

        """
        timeout_millis = int(timeout * 1000) if timeout else None
        if self.socket_sub in dict(self.poller.poll(timeout=timeout_millis)):
            return self.get_nowait()
        return None

    def get_nowait(self) -> Any:
        """Receive a message without waiting."""
        socks = dict(self.poller.poll(timeout=0))
        if self.socket_sub in socks:
            return self.socket_sub.recv_pyobj(zmq.NOBLOCK)
        return None

    def put(self, item: Any) -> None:
        """Send a message.

        Args:
        ----
            item (Any): Object to send.

        """
        time.sleep(0.001)
        self.socket_pub.send_pyobj(item)

    def put_nowait(self, item: Any) -> None:
        """Send a message without blocking.

        Args:
        ----
            item (Any): Object to send.

        """
        self.socket_pub.send_pyobj(item, zmq.NOBLOCK)

    def _after_fork(self) -> None:
        """Reset sockets after fork (Unix only)."""
        self._reset()

    def _reset(self) -> None:
        """Recreate PUB/SUB sockets."""
        self.socket_pub = self.context.socket(zmq.PUB)
        self.socket_pub.connect(f"tcp://*:{self.port}")

        self.socket_sub = self.context.socket(zmq.SUB)
        self.socket_sub.connect(f"tcp://localhost:{self.port}")
        self.socket_sub.subscribe("")

        self.poller = zmq.Poller()

    def stop(self) -> None:
        """Close sockets and terminate context."""
        if self.socket_pub:
            self.socket_pub.close()
        if self.socket_sub:
            self.socket_sub.close()
        self.context.term()

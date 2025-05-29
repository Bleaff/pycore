"""The ZeroQueue module provides a ZeroMQ-based queue interface for inter-process communication.

Supports PUB/SUB and REQ/REP messaging patterns.

Includes:
- ZeroQueue: A publish/subscribe queue for communication on a single machine.
- ZeroQueueConsumer: A message receiver using the REQ/REP pattern.
- ZeroQueueProducer: A message producer with message buffering using the REQ/REP pattern.
"""

from __future__ import annotations

import queue
import sys
from collections import deque
from multiprocessing.util import register_after_fork
from typing import Any

import zmq

from neudc.core.base.base_queue import QueueLike


class ZeroQueue(QueueLike):
    """PUB/SUB-based queue implementation using ZeroMQ.

    Suitable for inter-process message passing on a single machine.
    """

    def __init__(self, port: int | None = None) -> None:
        """Initialize the ZeroQueue.

        Args:
        ----
            port (Optional[int]): Port for PUB/SUB communication. If None, a random free port is chosen.

        """
        self.port = port
        self.context = zmq.Context()
        self.socket_pub = self.context.socket(zmq.PUB)
        if not self.port:
            self.port = self.socket_pub.bind_to_random_port("tcp://*")
        else:
            self.socket_pub.bind(f"tcp://*:{self.port}")

        self.socket_sub = self.context.socket(zmq.SUB)
        self.socket_sub.connect(f"tcp://localhost:{self.port}")
        self.socket_sub.subscribe("")

        self.poller = zmq.Poller()
        self.poller.register(self.socket_sub, zmq.POLLIN)

        if sys.platform != "win32":
            register_after_fork(self, ZeroQueue._after_fork)

    def __str__(self) -> str:
        """Magic methods for string representation of queue."""
        return f"{self.__class__.__name__}(port={self.port})"

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
        return self.socket_sub.recv_pyobj(zmq.NOBLOCK)

    def put(self, item: Any) -> None:
        """Send a message.

        Args:
        ----
            item (Any): Object to send.

        """
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


class ZeroQueueConsumer(QueueLike):
    """Message receiver based on ZeroMQ REQ/REP pattern.

    This class is used to receive messages from a producer.
    """

    def __init__(self, port: int | None = None) -> None:
        """Initialize the ZeroQueueConsumer.

        This class is used to receive messages from a producer using the REQ/REP pattern.

        Args:
        ----
            port (Optional[int]): Server port. If None, the server creates and binds a socket.

        """
        self.port = port
        self.context = zmq.Context()
        self.socket_sub = self.context.socket(zmq.REP)
        if not self.port:
            self.port = self.socket_sub.bind_to_random_port("tcp://*")
        else:
            self.socket_sub.connect(f"tcp://localhost:{self.port}")

        self.poller = zmq.Poller()
        self.poller.register(self.socket_sub, zmq.POLLIN)

    def __str__(self) -> str:
        """Magic methods for string representation of queue."""
        return f"{self.__class__.__name__}(port={self.port})"

    def __del__(self) -> None:
        """Magic method to remove the socket and context with destructor."""
        self.socket_sub.close()
        self.context.term()

    def get(self, timeout: float | None = None) -> Any | None:
        """Receive a message with a timeout.

        Args:
        ----
            timeout (Optional[float]): Timeout in seconds.

        Returns:
        -------
            Optional[Any]: Received message, or None if timeout expired.

        """
        if timeout:
            timeout = timeout * 1000
        if self.socket_sub in dict(self.poller.poll(timeout=timeout)):
            data = self.socket_sub.recv_pyobj(zmq.NOBLOCK)
            self.socket_sub.send(b"0", zmq.NOBLOCK)
            return data
        return None

    def get_nowait(self) -> Any:
        """Receive a message without blocking.

        Returns
        -------
            Any: Received message.

        Raises
        ------
            queue.Empty: If no message is available.

        """
        if self.socket_sub in dict(self.poller.poll(timeout=1)):
            # socket is ready — but still might fail, so minimal try block
            try:
                data = self.socket_sub.recv_pyobj(zmq.NOBLOCK)
                self.socket_sub.send(b"0", zmq.NOBLOCK)
            except zmq.Again as err:  # more specific than ZMQError
                raise queue.Empty from err
            except zmq.ZMQError as err:
                raise queue.Empty from err
            return data
        raise queue.Empty

    def put(self, item: Any) -> None:
        """Not implemented."""
        raise NotImplementedError

    def put_nowait(self, item: Any) -> None:
        """Not implemented."""
        raise NotImplementedError


class ZeroQueueProducer(QueueLike):
    """Message producer using REQ/REP pattern.

    Supports message buffering and automatic retries if the connection is lost.
    """

    DEQUE_LEN = 100
    TIMEOUT_MS = 100
    TMP_N = 40

    def __init__(self, port: int | None = None, deque_len: int | None = None) -> None:
        """Initialize the ZeroQueueProducer.

        Args:
        ----
            port (Optional[int]): Port to connect to the Consumer.
            deque_len (Optional[int]): Maximum size of the message buffer.

        """
        self.port = port
        self.deque: deque = deque(maxlen=deque_len or self.DEQUE_LEN)
        self.init()

    def __str__(self) -> str:
        """Magic methods for string representation of queue."""
        return f"{self.__class__.__name__}(port={self.port})"

    def init(self) -> None:
        """Initialize sockets and context."""
        self.context = zmq.Context()

        self.socket_pub = self.context.socket(zmq.REQ)
        self.socket_pub.setsockopt(zmq.LINGER, 0)
        if not self.port:
            self.port = self.socket_pub.bind_to_random_port("tcp://*")
        else:
            self.socket_pub.connect(f"tcp://localhost:{self.port}")

        self.poller = zmq.Poller()
        self.poller.register(self.socket_pub, zmq.POLLIN)

    def __del__(self) -> None:
        """Magic method to remove the socket and context with destructor."""
        self.stop()

    def stop(self) -> None:
        """Close sockets and terminate context."""
        self.socket_pub.close()
        self.context.term()

    def _put_from_deque(self, timeout: int = TIMEOUT_MS) -> bool:
        """Try to send the first item from the buffer.

        Args:
        ----
            timeout (int): Timeout in milliseconds.

        Returns:
        -------
            bool: True if the message was successfully sent, False otherwise.

        """
        _item = self.deque[0]
        self.socket_pub.send_pyobj(_item)
        if self.socket_pub in dict(self.poller.poll(timeout=timeout)):
            self.socket_pub.recv()
            self.deque.popleft()
            return True
        return False

    def put(self, item: Any, timeout: float | None = None) -> None:
        """Put an item in the buffer and attempt to send it.

        Args:
        ----
            item (Any): The object to send.
            timeout (Optional[float]): Max duration to attempt sending (in seconds).

        """
        self.deque.append(item)
        timeout_millis = int(timeout * 1000) if timeout else None
        while self.deque:
            if not self._put_from_deque(timeout=timeout_millis or self.TIMEOUT_MS):
                self.stop()
                self.init()
                # retry once on the fresh connection
                continue

    def put_nowait(self, item: Any) -> None:
        """Send a message immediately without blocking.

        Args:
        ----
            item (Any): The object to send.

        Raises:
        ------
            queue.Full: If sending fails.

        """
        self.socket_pub.send_pyobj(item)
        if self.socket_pub in dict(self.poller.poll(timeout=self.TIMEOUT_MS // 5 + 1)):
            self.socket_pub.recv()
        else:
            # Preserve data - enqueue for later retry
            self.deque.appendleft(item)
            self.stop()
            self.init()
            raise queue.Full

    def get(self, timeout: float | None) -> Any:
        """Not implemented."""
        raise NotImplementedError

    def get_nowait(self) -> Any:
        """Not implemented."""
        raise NotImplementedError

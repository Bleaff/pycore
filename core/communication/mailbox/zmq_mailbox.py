"""ZMQMailbox module for inter-node communication in a distributed system.

This module defines the ZMQMailbox class, a concrete implementation of the
BaseMailbox interface. It uses ZeroMQ (PAIR socket) to enable inter-process or
inter-thread communication between nodes. The mailbox supports message sending,
receiving, checking for pending messages, and clearing its queue.

Typical usage:
    mailbox = ZMQMailbox("tcp://127.0.0.1:5555", bind=True)
    mailbox.start()
    mailbox.send({"event": "hello"})
    if mailbox.has_messages():
        msg = mailbox.receive()
    mailbox.clear()
    mailbox.stop()
"""

from __future__ import annotations
from queue import Queue, Empty, Full
import time
import logging
from typing import Any

from neudc.core.base.base_mailbox import BaseMailbox
from neudc.core.communication.zero_queue import ZeroQueuePub, ZeroQueueSub
import threading


logging.basicConfig(level=logging.DEBUG)


class ZMQMailbox(BaseMailbox[dict]):
    """ZeroMQ-based mailbox implementation."""

    def __init__(
        self,
        *,
        message_queue_size: int = 20,
        logger: logging.Logger | None = None,
        name: str = "ZMQMailbox",
    ) -> None:
        """Initialize the ZeroMQ mailbox."""
        self.logger = logger
        self.pub_sockets: dict[int, ZeroQueuePub] = {}
        self.sub_queue: ZeroQueueSub = ZeroQueueSub()
        self.consume_port: int = self.sub_queue.port
        self._message_queue: Queue = Queue(message_queue_size)
        self._running = False
        self._thread = None
        self._join_timeout = 0.5
        self.name = name

        if not logger:
            self.logger = logging.getLogger(__name__)
        self.start()
    def _receiver_loop(self) -> None:
        """Thread loop for receiving messages from the ZeroMQ subscriber."""
        _unsent_message: Any = None
        while self._running:
            try:
                message = self.sub_queue.get(timeout=1)
                self._message_queue.put(message, timeout=1)
                if self.logger:
                    self.logger.debug(f"[{self.name}][RECV] ← message")
            except Empty:
                continue
            except Full:
                self.logger.warning("Message queue is full")
                while self._message_queue.full():
                    time.sleep(0.01)  # Sleep briefly to avoid busy waiting
                self._message_queue.put(_unsent_message)
                self.logger.debug(f"[{self.name}][SENDING] -> unsent message")
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error in receiver loop: {e}")
            
    def start(self) -> None:
        """Start the receiving thread."""
        self._running = True
        self._thread = threading.Thread(target=self._receiver_loop, daemon=True)
        self._thread.start()


    def stop(self) -> None:
        """Stop the mailbox."""
        self.sub_queue.stop()
        self._running = False
        if self._thread:
            self._thread.join(timeout=self._join_timeout)
            
        for pub_socket in self.pub_sockets.values():
            pub_socket.stop()

    def send(self, message: Any) -> None:
        """Send a message to the mailbox."""
        for pub_socket in self.pub_sockets.values():
            if self.logger:
                self.logger.debug(f"[{self.name}][START SENDING] → {time.time()}")
            pub_socket.put(message)
            if self.logger:
                self.logger.debug(f"[{self.name}][END SENDING] → {time.time()}")
        if self.logger:
            self.logger.debug(f"[{self.name}][SEND] → {type(message)}")

    def receive(self) -> dict:
        """Receive a message from the mailbox."""
        try:
            message = self._message_queue.get(timeout=0.1)
            if self.logger:
                self.logger.debug(f"[{self.name}][RECV][{time.time()}] ← {type(message)}")
        except Empty:
            message = None
        return message

    def add_publisher(self, port: int) -> None:
        """Connect a publisher to the mailbox. This method is not thread-safe."""
        self.pub_sockets[port] = ZeroQueuePub(port=port)
        if self.logger:
            self.logger.debug(f"[{self.name}][Added publisher] → port:{port}")

    def remove_publisher(self, port: int) -> None:
        """Removes a publisher from the mailbox."""
        rm_pub = self.pub_sockets.pop(port)
        if self.logger:
            self.logger.debug(f"[{self.name}][Removed publisher] → {rm_pub}")
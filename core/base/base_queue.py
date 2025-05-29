"""Abstract base class for queue-like communication interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class QueueLike(ABC):
    """Interface for queue-like communication classes.

    Defines the standard methods any inter-process queue must implement.
    """

    @abstractmethod
    def put(self, message: Any) -> None:
        """Put an item into the queue.

        Args:
        ----
            message (Any): The message to enqueue.

        Raises:
        ------
            NotImplementedError: If the method is not implemented.

        """
        raise NotImplementedError

    @abstractmethod
    def put_nowait(self, message: Any) -> None:
        """Put an item into the queue without blocking.

        Args:
        ----
            message (Any): The message to enqueue.

        Raises:
        ------
            NotImplementedError: If the method is not implemented.

        """
        raise NotImplementedError

    @abstractmethod
    def get(self, timeout: float | None) -> Any:
        """Get an item from the queue, optionally waiting up to a timeout.

        Args:
        ----
            timeout (Optional[float]): Time in seconds to wait for a message.

        Returns:
        -------
            Any: The received message.

        Raises:
        ------
            NotImplementedError: If the method is not implemented.

        """
        raise NotImplementedError

    @abstractmethod
    def get_nowait(self) -> Any:
        """Get an item from the queue without blocking.

        Returns
        -------
            Any: The received message.

        Raises
        ------
            NotImplementedError: If the method is not implemented.

        """
        raise NotImplementedError

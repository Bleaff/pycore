"""Module contains classes and functions for data transfer between processes.

Communication builds on queues.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from neudc.core.communication.mailbox.zmq_mailbox import ZMQMailbox
from neudc.core.communication.zero_queue.queue_transfer import ZeroQueue, ZeroQueueProducer

if TYPE_CHECKING:
    from neudc.core.base.base_mailbox import BaseMailbox
    from neudc.core.base.base_queue import QueueLike


class TransferFactory:
    """Factory class for creating queue-like objects.

    This class provides a static method to create instances of different queue-like classes based on the specified data type.
    The available data types are:
        - "Queue": Creates an instance of ZeroQueue.
        - "QueueProducer": Creates an instance of ZeroQueueProducer.
        - "QueueConsumer": Creates an instance of ZeroQueueConsumer.
        - "ZMQMailbox": Creates an instance of ZMQMailbox.
    The factory method takes the data type as a string and any additional arguments or keyword arguments required for the class constructor.

    Raises
    ------
        ValueError: If the specified data type is not recognized or supported.

    """

    @staticmethod
    def create(data_type: str, *args: list, **kwargs: dict) -> QueueLike | BaseMailbox:
        """Create an instance of a queue-like class based on the specified data type.

        Args:
        ----
            data_type (str): The type of queue-like object to create.
            *args: Positional arguments for the class constructor.
            **kwargs: Keyword arguments for the class constructor.

        Returns:
        -------
            QueueLike: An instance of a queue-like class.
            BaseMailbox: An instance of a mailbox class.

        """
        to_return: QueueLike | BaseMailbox = None  # type: ignore[assignment]
        if data_type == "Queue":
            to_return = ZeroQueue(*args, **kwargs)  # type: ignore[arg-type]
        elif data_type in ("QueueProducer", "QueueConsumer"):
            to_return = ZeroQueueProducer(*args, **kwargs)  # type: ignore[arg-type]
        elif data_type == "ZMQMailbox":
            to_return = ZMQMailbox(*args, **kwargs)  # type: ignore[arg-type]
        else:
            msg = f"Unknown transfer type: {data_type}"
            raise ValueError(msg)
        return to_return

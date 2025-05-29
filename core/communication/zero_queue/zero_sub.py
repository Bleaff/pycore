"""ZeroQueueSub class for receiving data from another ZeroQueuePublisher.

This class extends the ZeroQueue class to receive data from a ZeroQueuePublisher.
"""

from typing import NoReturn

from neudc.core.communication.zero_queue.zero_queue import ZeroQueue
from neudc.core.communication.zero_queue.zmq_state import ZeroQueueConnectionType, ZeroQueueMode


class ZeroQueueSub(ZeroQueue):
    """ZeroQueueSub class for receiving data from another ZeroQueuePublisher.

    This class extends the ZeroQueue class to receive data from a ZeroQueuePublisher.

    Args:
    ----
            port (int): Port for PUB/SUB communication.
            mode (ZeroQueueMode): Mode of the queue (PUB(publisher) or SUB(subscriber)).

    """

    def __init__(self) -> None:
        """Initialize the ZeroQueueSub.

        This class is used to receive data from a ZeroQueuePublisher. It always binds to a random port.

        """
        super().__init__(port=-1, mode=ZeroQueueMode.SUB, contype=ZeroQueueConnectionType.BIND)

    def put(self, item) -> NoReturn:
        """Protect put method not supported for ZeroQueueSub."""
        msg = "ZeroQueueSub does not support put() method."
        raise NotImplementedError(msg)

    def put_nowait(self, item) -> NoReturn:
        """Protect put_nowait method not supported for ZeroQueueSub."""
        msg = "ZeroQueueSub does not support put_nowait() method."
        raise NotImplementedError(msg)

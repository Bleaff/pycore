"""BaseNode class serves as an abstract base class for node implementations in a distributed system.

Nodes are the fundamental building blocks that process data and communicate with
each other through mailboxes.
"""

from abc import ABC, abstractmethod
from typing import Any
import threading


class BaseNode(ABC):
    """Abstract base class for node implementations in a distributed system.

    This class defines the standard methods a node must implement to be used in
    the system. It provides a common interface for all nodes, regardless of the
    specific functionality they provide.

    Nodes are the fundamental building blocks that process data and communicate
    with each other through mailboxes.
    """
    def __init__(self, mailbox: Any, logger: Any, id:str = "BaseNode"):
        """Initialize the node with a mailbox and a logger."""
        super().__init__()
        self.mailbox = mailbox
        self.logger = logger
        self.thread = None
        self._stop_event = threading.Event()
        self._join_timeout = 0.1
        self.is_running = False
        self.id = id
        self.start()

    def _collect_data(self)-> Any:
        """Grabs data from mailbox."""
        return self.mailbox.receive()

    @staticmethod
    def from_config(config: dict[str, Any])-> "BaseNode":
        """Create a node instance from the given configuration.

        Args:
            config (dict[str, Any]): Configuration details for the node.

        Returns:
            BaseNode: A node instance.

        Raises:
            NotImplementedError: If the method is not implemented by a subclass.
        """
        raise NotImplementedError
    
    def __call__(self, *args, **kwargs)-> Any:
        """Calls the run method of the node."""
        return self.run(*args, **kwargs)
    
    @abstractmethod
    def process(self, *args, **kwargs)-> Any:
        """Execute the node's main functionality.

        Raises:
            NotImplementedError: If the method is not implemented by a subclass.
        """
        raise NotImplementedError
    def run(self):
        """Run the node processing loop."""
        while True:
            try:
                data = self._collect_data()
                if data is not None:
                    result = self.process(data)
                    self.mailbox.send(result)
            except Exception as e:
                self.logger.exception(f"Error while processing: {e}")
    
    def start(self):
        """Start the thread with the run method."""
        self.logger.info("Starting node...")
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()
        self.logger.info("Node started.")
    
    def stop(self):
        """Signal the thread to stop and wait for it."""
        self.logger.info("Stopping node...")
        self._stop_event.set()
        self.mailbox.stop()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=self._join_timeout)
        self.logger.info("Node stopped.")

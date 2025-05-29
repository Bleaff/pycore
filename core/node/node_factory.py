from neudc.core.node.readers.image_reader import FolderImageNode
from neudc.core.node.processors.dummy_resize import ResizeNode
from neudc.core.node.broadcast.image_saver import SaveImageNode
from typing import Any


class NodeFactory:
    """
    Factory to create node instances based on config.
    """

    NODE_CLASS_MAP = {
        "FolderImageNode": FolderImageNode,
        "ResizeNode": ResizeNode,
        "SaveImageNode": SaveImageNode,
    }

    @staticmethod
    def create(config: dict[str, Any], mailbox: Any, logger: Any) -> Any:
        """
        Create a node instance from its config.

        Args:
            config (dict): Node config.
            mailbox (Any): Precreated mailbox for this node.
            logger (Any): Logger for this node.

        Returns:
            Any: Instantiated node.
        """
        node_type = config["type"]
        node_class = NodeFactory.NODE_CLASS_MAP.get(node_type)

        if not node_class:
            raise ValueError(f"Unknown node type: {node_type}")

        config = dict(config)  # make a copy
        config["mailbox"] = mailbox
        config["logger"] = logger
        return node_class.from_config(config)

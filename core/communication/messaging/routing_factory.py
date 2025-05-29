"""
Factory responsible for creating and wiring mailboxes for nodes.

The factory is responsible for:
    1. Creating mailboxes for all nodes
    2. Wiring output connections between nodes

The factory takes the application configuration as a parameter.
The configuration must contain a list of node configurations.
Each node configuration must contain an "id" parameter.
The "outputs" parameter is optional and contains a list of target node_ids
that the node should send messages to.
"""

from neudc.core.communication.mailbox.zmq_mailbox import ZMQMailbox
from typing import Dict


class RoutingFactory:
    """
    Factory responsible for creating and wiring mailboxes for nodes.
    """

    def __init__(self, config: dict):
        self.config = config

    def create_mailboxes(self) -> Dict[str, ZMQMailbox]:
        """
        Create mailboxes for all nodes and wire their output queues.

        Returns:
            Dict[str, ZMQMailbox]: Mapping of node_id to its ZMQMailbox instance.
        """
        mailboxes: Dict[str, ZMQMailbox] = {}

        # 1. Create mailbox for every node
        for node_cfg in self.config["nodes"]:
            node_id = node_cfg["id"]
            mailboxes[node_id] = ZMQMailbox(name=node_id)

        # 2. Wire output connections
        for node_cfg in self.config["nodes"]:
            node_id = node_cfg["id"]
            outputs = node_cfg.get("outputs", [])
            for target_node_id in outputs:
                pub_port = mailboxes[target_node_id].consume_port
                mailboxes[node_id].add_publisher(pub_port)

        return mailboxes

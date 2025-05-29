"""
Node that processes Frame objects.

This node is the base class for all processor nodes. It provides a common interface
for processing Frame objects.

The process method is called for each Frame object that is sent to the node. The
method must be implemented by subclasses.

The node also provides a method to create a node instance from a configuration
dictionary.

Example:
    >>> config = {
    ...     "mailbox": mailbox,
    ...     "logger": logger,
    ...     "target_width": 640,
    ...     "target_height": 480
    ... }
    >>> processor_node = ProcessorNode.from_config(config)

"""

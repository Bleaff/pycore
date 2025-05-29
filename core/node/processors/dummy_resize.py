"""
A node that resizes incoming Frame objects to a target resolution.

This node is useful for cases where processing needs to be done on images of a specific size.
The node will resize any incoming Frame object to the target resolution.

The target resolution is specified in the configuration dictionary as 'target_width' and 'target_height'.

Example:
    >>> config = {
    ...     "mailbox": mailbox,
    ...     "logger": logger,
    ...     "target_width": 640,
    ...     "target_height": 480
    ... }
    >>> resize_node = ResizeNode.from_config(config)

"""

import cv2
from typing import Any

from neudc.core.base.base_node import BaseNode
from neudc.core.communication.messaging.types import Frame


class ResizeNode(BaseNode):
    """
    A node that resizes incoming Frame objects to a target resolution.
    """

    def __init__(self, mailbox: Any, logger: Any, target_width: int, target_height: int):
        self.target_width = target_width
        self.target_height = target_height
        super().__init__(mailbox, logger)

    @staticmethod
    def from_config(config: dict[str, Any]) -> "ResizeNode":
        """
        Create ResizeNode from configuration dictionary.

        Args:
            config (dict): Configuration dict containing 'mailbox', 'logger', 'target_width', and 'target_height'.

        Returns:
            ResizeNode: Instantiated ResizeNode.
        """
        return ResizeNode(
            mailbox=config["mailbox"],
            logger=config["logger"],
            target_width=config["target_width"],
            target_height=config["target_height"]
        )

    def process(self, frame: Frame) -> Frame:
        """
        Resize the image in the Frame and return a new Frame with updated image.

        Args:
            frame (Frame): Input Frame object.

        Returns:
            Frame: Frame object with resized image.
        """
        resized_image = cv2.resize(frame.image, (self.target_width, self.target_height))
        frame.image = resized_image
        self.logger.debug(f"Resized frame {frame.frame_id} to {self.target_width}x{self.target_height}")
        return frame

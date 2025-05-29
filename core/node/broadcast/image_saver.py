"""
Image Saver Node

This node saves incoming Frame objects to disk in the specified directory.

"""
import os
import cv2
from typing import Any

from neudc.core.base.base_node import BaseNode
from neudc.core.communication.messaging.types import Frame


class SaveImageNode(BaseNode):
    """
    A node that saves incoming Frame images to disk in the specified directory.
    """

    def __init__(self, mailbox: Any, logger: Any, save_dir: str):
        self.save_dir = save_dir
        os.makedirs(self.save_dir, exist_ok=True)
        super().__init__(mailbox, logger)

    @staticmethod
    def from_config(config: dict[str, Any]) -> "SaveImageNode":
        """
        Create SaveImageNode from configuration.

        Args:
            config (dict): Dictionary containing 'mailbox', 'logger', 'save_dir'.

        Returns:
            SaveImageNode: Instantiated node.
        """
        return SaveImageNode(
            mailbox=config["mailbox"],
            logger=config["logger"],
            save_dir=config["save_dir"]
        )

    def process(self, frame: Frame) -> Frame:
        """
        Save the image from a Frame to disk.

        Args:
            frame (Frame): Input frame with image.

        Returns:
            Frame: The same frame, unmodified.
        """
        filename = os.path.join(self.save_dir, f"frame_{frame.frame_id}.jpg")
        success = cv2.imwrite(filename, frame.image)
        if success:
            self.logger.debug(f"Saved frame {frame.frame_id} to {filename}")
        else:
            self.logger.warning(f"Failed to save frame {frame.frame_id} to {filename}")
        return frame

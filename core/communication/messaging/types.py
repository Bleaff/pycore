"""Base class for box attributes.

This class defines the base attributes for a box, including the source node ID.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

import numpy as np

# === Base Attribute ===


class BaseAttribute(BaseModel):
    """Base class for box attributes."""

    source_node_id: int = -1


# === Specific Attributes ===


class Class(BaseAttribute):
    """Attribute representing class membership."""

    class_id: str
    score: float | None = None


class Segmentation(BaseAttribute):
    """Segmentation mask (image) attached to a box."""

    image: np.ndarray

    class Config:
        """Pydantic config for Segmentation class."""

        arbitrary_types_allowed = True


class Text(BaseAttribute):
    """Text attribute with confidence."""

    text: str
    score: float


# === Detection Box ===


class Box(BaseAttribute):
    """Box with absolute coordinates."""

    x1: float
    y1: float
    x2: float
    y2: float
    class_id: str
    score: float
    labels: list[Class] | None = None
    reid: str = "-1"

    class Config:
        """Service config for Box class."""

        arbitrary_types_allowed = True


# === Keypoints ===


class Keypoint(BaseModel):
    """Relative keypoint (0.0 - 1.0)."""

    x: float
    y: float
    class_id: str
    score: float


class Keypoints(BaseModel):
    """Dict[str, Keypoint]. Used by models to describe body parts, facial landmarks, etc."""

    keypoints: dict[str, Keypoint] = {}
    description: str = ""


# === Frame ===


class Frame(BaseModel):
    """Frame with image, timestamp, and boxes."""

    image: np.ndarray
    timestamp: float
    source_frame: str
    frame_id: int
    boxes: list[Box]

    class Config:
        """Pydantic config for Frame class."""

        arbitrary_types_allowed = True


# === Pipeline Configuration ===


class NodeConfig(BaseModel):
    """Single node configuration for pipeline."""

    name: str
    type: str
    params: dict[str, Any]
    output_queue: str


class Pipeline(BaseModel):
    """Pipeline consisting of multiple nodes."""

    name: str
    nodes: dict[str, NodeConfig]


class Task(BaseModel):
    """Task wrapping a pipeline."""

    name: str
    pipeline: Pipeline

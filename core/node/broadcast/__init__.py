"""
Broadcasting nodes for NEUDC.

This module provides nodes that can be used to broadcast or save data streams
in a NEUDC pipeline. The nodes are designed to be used as a sink for data streams
and can be used to send data to external systems or save data to disk.

The provided nodes are:

- `StreamNode`: A node that streams video frames to a specified URL using a
  video encoding library such as OpenCV or FFmpeg.
- `SaveVideoNode`: A node that saves video frames to a file using a video encoding
  library such as OpenCV or FFmpeg.
- `SaveImageNode`: A node that saves individual images to a file.

Example:
    >>> from neudc.node.broadcast import StreamNode
    >>> node = StreamNode("rtmp://example.com/stream")
    >>> node.start()
"""

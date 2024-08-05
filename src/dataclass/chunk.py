"""
This module contains the Chunk dataclass.
"""

from dataclasses import dataclass


@dataclass
class Chunk:
    index: int
    """The index of the chunk"""

    text: str
    """The text of the chunk"""

    length: int
    """The length of the chunk"""

    @classmethod
    def from_dict(cls, d: dict) -> "Chunk":
        """
        Creates a chunk from a dictionary.
        """
        return Chunk(index=d["index"], text=d["text"], length=d["length"])

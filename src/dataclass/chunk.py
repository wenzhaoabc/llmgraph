"""
This module contains the Chunk dataclass.
"""

from dataclasses import dataclass


@dataclass
class Chunk:
    id: int
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
        return Chunk(id=d["id"], text=d["text"], length=d["length"])

    def to_dict(self) -> dict:
        """
        Converts the chunk to a dictionary.
        """
        return {"id": self.id, "text": self.text, "length": self.length}

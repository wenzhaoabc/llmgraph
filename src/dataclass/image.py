"""
This module contains the Image class.
"""

from dataclasses import dataclass


@dataclass
class Image:

    title: str
    """The title of the image"""

    path: str
    """The path of the image"""

    chunks: list[int]
    """The chunks of the image occuring in the document"""

    text_snippets: list[str]
    """The text snippets extracted from the image"""

    @classmethod
    def from_dict(cls, d: dict) -> "Image":
        """
        Creates an image from a dictionary.
        """
        return Image(
            title=d["title"],
            path=d["path"],
            chunks=d["chunks"],
            text_snippets=d["text_snippets"],
        )

    def to_dict(self) -> dict:
        """
        Converts the image to a dictionary.
        """
        return {
            "title": self.title,
            "path": self.path,
            "chunks": self.chunks,
            "text_snippets": self.text_snippets,
        }

"""
This module contains the Image class.
"""

import json

from dataclasses import dataclass, field


@dataclass
class Image:

    title: str
    """The title of the image"""

    path: str
    """The path of the image"""

    chunks: list[int] = field(default_factory=list)
    """The chunks of the image occuring in the document"""

    text_snippets: list[str] = field(default_factory=list)
    """The text snippets extracted from the image"""

    description: str = ""
    """The description of the image"""

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
            description=d.get("description", ""),
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
            "description": self.description,
        }

    def to_origin_text(self) -> str:
        """
        Converts the image to its original text representation.
        """
        return f"<{self.title}, {self.path}, {json.dumps(self.text_snippets)}, {self.description}>"

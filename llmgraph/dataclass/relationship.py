"""
This module contains the Relationship dataclass.
"""

import json
from dataclasses import dataclass, field


@dataclass
class Relationship:
    start: str
    """The source entity of the relationship"""

    end: str
    """The target entity of the relationship"""

    type: str
    """The label of the relationship"""

    references: list[str] = field(default_factory=list)
    """The original text references of the relationship"""

    properties: dict[str, str] = field(default_factory=dict)
    """The properties of the relationship"""

    images: list[str] = field(default_factory=list)
    """The images associated with the relationship"""

    chunks: list[int] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> "Relationship":
        """
        Creates a relationship from a dictionary.
        """
        return Relationship(
            start=d["start"],
            end=d["end"],
            type=d["type"],
            references=d["references"],
            properties=d["properties"],
            images=d["images"],
            chunks=d["chunks"],
        )

    def to_dict(self) -> dict:
        """
        Converts the relationship to a dictionary.
        """
        return {
            "start": self.start,
            "end": self.end,
            "type": self.type,
            "references": self.references,
            "properties": self.properties,
            "images": self.images,
            "chunks": self.chunks,
        }

    def to_origin_text(self) -> str:
        """
        Converts the relationship to the original text.
        """
        return f"<{self.start}, {self.type}, {self.end}, {json.dumps(self.properties)}, {json.dumps(self.references)}>"

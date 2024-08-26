"""
This module contains the Entity class, which represents an entity.
"""

import json
from dataclasses import dataclass, field


@dataclass
class Entity:
    """A class representing a entity in the database"""

    name: str
    """The name of the entity, unique in the database"""

    label: str = ""
    """The label of the entity"""

    references: list[str] = field(default_factory=list)
    """The original text references of the entity"""

    properties: dict[str, str] = field(default_factory=dict)
    """The properties of the entity"""

    images: list[str] = field(default_factory=list)
    """The images associated with the entity"""

    chunks: list[int] = field(default_factory=list)
    """The chunks associated with the entity"""

    @classmethod
    def from_dict(cls, d: dict) -> "Entity":
        """
        Creates an entity from a dictionary.
        """
        return Entity(
            name=d["name"],
            label=d["label"],
            references=d["references"],
            properties=d["properties"],
            images=d["images"],
            chunks=d["chunks"],
        )

    def to_dict(self) -> dict:
        """
        Converts the entity to a dictionary.
        """
        return {
            "name": self.name,
            "label": self.label,
            "references": self.references,
            "properties": self.properties,
            "images": self.images,
            "chunks": self.chunks,
        }

    def to_origin_text(self) -> str:
        """
        Converts the entity to a string.
        """
        return f"<{self.name}, {self.label}, {json.dumps(self.properties)}, {json.dumps(self.references)}>"

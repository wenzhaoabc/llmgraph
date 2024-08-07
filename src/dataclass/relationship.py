"""

"""

from dataclasses import dataclass


@dataclass
class Relationship:
    start: str
    """The source entity of the relationship"""

    end: str
    """The target entity of the relationship"""

    type: str
    """The label of the relationship"""

    references: list[str] | None = None
    """The original text references of the relationship"""

    properties: dict[str, str] | None = None
    """The properties of the relationship"""

    images: list[str] | None = None
    """The images associated with the relationship"""

    @classmethod
    def from_dict(cls, d: dict) -> "Relationship":
        """
        Creates a relationship from a dictionary.
        """
        return Relationship(
            start=d["start"],
            end=d["end"],
            type=d["type"],
            references=d.get("references"),
            properties=d.get("properties"),
            images=d.get("images"),
        )

    def to_dict(self) -> dict:
        """
        Converts the relationship to a dictionary.
        """
        pros = self.properties.update({"references": self.references})
        return {
            "start": self.start,
            "end": self.end,
            "type": self.type,
            "properties": pros,
        }

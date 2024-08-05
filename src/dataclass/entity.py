from dataclasses import dataclass


@dataclass
class Entity:
    """A class representing a entity in the database"""

    name: str
    """The name of the entity, unique in the database"""

    label: str | None = None
    """The label of the entity"""

    references: list[str] | None = None
    """The original text references of the entity"""

    properties: dict[str, str] | None = None
    """The properties of the entity"""

    images: list[str] | None = None
    """The images associated with the entity"""

    @classmethod
    def from_dict(cls, d: dict) -> "Entity":
        """
        Creates an entity from a dictionary.
        """
        refernences = None
        if d.get("properties") is not None and d.get("properties").get("references"):
            del d["properties"]["references"]
            refernences = d.get("properties").get("references")
        return Entity(
            name=d["name"],
            label=d.get("label"),
            references=refernences,
            properties=d.get("properties"),
            images=d.get("images"),
        )

    def to_dict(self) -> dict:
        """
        Converts the entity to a dictionary.
        """
        pros = self.properties.update({"references": self.references})
        return {"name": self.name, "label": self.label, "properties": pros}

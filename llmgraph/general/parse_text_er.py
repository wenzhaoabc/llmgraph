"""
从大模型的回答中提取信息
"""

import re
import json
import logging


from ..dataclass import Entity, Relationship
from ..common.tools import shorten_string, remove_duplicates

log = logging.getLogger("llmgraph")


def extract_acronym(text: str) -> list[tuple[str, str]]:
    """
    Extract acronyms from text
    """
    pattern = r"\b([A-Za-z\s]+)\s?\(([A-Z]+)\)"

    matches = re.findall(pattern, text)

    result = []
    for full_text, acronym in matches:
        words = [
            word
            for word in full_text.split()
            if word.lower() not in {"of", "is", "the", "and", "in", "on", "at", "to"}
        ]

        if len(words) >= len(acronym):
            result.append((str(full_text).strip(), str(acronym).strip()))

    return result


def e_raw_parse(text: str) -> list["Entity"]:
    """
    Extract entities from raw text
    """
    entities: list["Entity"] = []
    entity_pattern = r"<([^,]+),\s?([^,]+),\s?(\{[^\}]*\}),\s?(\[[^\]]*\])>"
    matches = re.finditer(entity_pattern, text, re.MULTILINE)

    for _, match in enumerate(matches, start=1):
        if len(match.groups()) < 4:
            log.warning(f"Invalid entity: {match}")
            continue
        name: str = match.group(1).replace('"', "").strip()
        label: str = match.group(2).replace('"', "").strip()
        properties: str = match.group(3).strip()
        references: str = match.group(4).strip()
        try:
            properties = json.loads(properties)
        except (json.JSONDecodeError, TypeError) as e:
            log.warning("Invalid entity properties: %s exception: %s", properties, e)
            properties = {}
        try:
            references: list[str] = json.loads(references)
        except (json.JSONDecodeError, TypeError) as e:
            log.warning("Invalid entity references: %s, exception: %s", references, e)
            references = []

        entities.append(
            Entity(name=name, label=label, properties=properties, references=references)
        )
    return entities


def r_raw_parse(text: str) -> list["Relationship"]:
    """
    Extract relationships from raw text
    """
    relationships: list["Relationship"] = []
    relationship_pattern = (
        r"<([^,]+),\s?([^,]+),\s?([^,]+),\s?(\{[^\}]*\}),\s?(\[[^\]]*\])>"
    )
    matches = re.finditer(relationship_pattern, text, re.MULTILINE)

    for _, match in enumerate(matches, start=1):
        if len(match.groups()) < 5:
            log.warning(f"Invalid relationship: {match}")
            continue
        start: str = match.group(1).replace('"', "").strip()
        relationship_type: str = match.group(2).replace('"', "").strip()
        end: str = match.group(3).replace('"', "").strip()
        properties: str = match.group(4).strip()
        references: str = match.group(5).strip()
        try:
            properties = json.loads(properties)
        except Exception as e:
            log.warning("Invalid rel properties: %s, exception: %s", properties, e)
            properties = {}
        try:
            references: list[str] = json.loads(references)
        except Exception as e:
            log.warning("Invalid rel references: %s, exception: %s", references, e)
            references = []

        relationships.append(
            Relationship(
                start=start, end=end, type=relationship_type, properties=properties
            )
        )
    return relationships


def parse_rawtext_to_er(rawtext: str) -> tuple[list["Entity"], list["Relationship"]]:
    """
    Parse rawtext to entities and relationships
    """
    regex = r"Entities:\s*([\s\S]*?)Relationships:\s*([\s\S]*)"
    match = re.search(regex, rawtext, re.DOTALL | re.MULTILINE)

    raw_e = ""
    raw_r = ""

    if match and len(match.groups()) > 1:
        raw_e = match.group(1)
        raw_r = match.group(2)
    else:
        log.error(f"Can not parse entities and relationships from rawtext: {rawtext}")
        log.warning(
            f"Can not parse entity and rel from rawtext: {shorten_string(rawtext, 10,10)}"
        )

    es: list["Entity"] = []
    rs: list["Relationship"] = []

    es.extend(e_raw_parse(raw_e))
    rs.extend(r_raw_parse(raw_r))

    return es, rs


def merge_er(
    es: list["Entity"], rs: list["Relationship"]
) -> tuple[list["Entity"], list["Relationship"]]:
    """
    Merge entities and relationships
    Delete invalid relationships
    """

    def merge_deduplicate(l1: list, l2: list) -> list:
        result = l1 + l2
        result = remove_duplicates(result)
        return result

    # Merge entities
    me: dict[tuple, "Entity"] = {}
    for entity in es:
        key = (entity.name.upper(), entity.label.upper())
        if key not in me:
            me[key] = entity
        else:
            log.info(f"Merge entity: (name, label) = {key}")
            me[key].properties.update(entity.properties)
            me[key].references = merge_deduplicate(
                me[key].references, entity.references
            )

            me[key].images = merge_deduplicate(me[key].images, entity.images)
            me[key].chunks = merge_deduplicate(me[key].chunks, entity.chunks)

    entity_names = [entity.name for entity in list(me.values())]
    # Merge relationships
    mr: dict[tuple, "Relationship"] = {}
    for relationship in rs:
        if (
            relationship.start not in entity_names
            or relationship.end not in entity_names
        ):
            log.warning(
                "Invalid relationship, start or end not in existing entities: "
                + f"(start, type, end) = {relationship.start, relationship.type, relationship.end}"
            )
            continue
        key = (
            relationship.start.upper(),
            relationship.type.upper(),
            relationship.end.upper(),
        )
        if key not in mr:
            mr[key] = relationship
        else:
            # log.debug(f"Merge relationship: (start, type, end) = {key}")
            mr[key].properties.update(relationship.properties)
            mr[key].references = merge_deduplicate(
                mr[key].references, relationship.references
            )
            mr[key].images = merge_deduplicate(mr[key].images, relationship.images)
            mr[key].chunks = merge_deduplicate(mr[key].chunks, relationship.chunks)

    return list(me.values()), list(mr.values())

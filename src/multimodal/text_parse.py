"""
This module contains functions to parse structed data from the response of LLM.
"""

import logging
import re
import json

from dataclass import Image
from text.tools import remove_duplicates

log = logging.getLogger("llmgraph")

def parse_rawtext_images(rawtext: str) -> list["Image"]:
    """
    Parse rawtext to images
    """
    images: list["Image"] = []
    image_pattern = r"!\[(.*?)\]\((.*?)\)"
    matches = re.finditer(image_pattern, rawtext, re.MULTILINE)

    for _, match in enumerate(matches, start=1):
        if len(match.groups()) < 2:
            log.warning(f"Invalid image: {match}")
            continue
        image_title: str = match.group(1).strip()
        image_path: str = match.group(2).strip()
        images.append(Image(title=image_title, path=image_path))
    return images


def parse_attris_from_rawtext(text: str, image: "Image") -> "Image":
    """
    Parses attributes from the raw text output by LLM.
    """
    regex = r"Title:\s*(.*?)$\nText Snippets:\s*(.*?)$\nDescription:\s*(.*?)$"
    matches = re.findall(regex, text, re.MULTILINE | re.DOTALL)
    if not matches or len(matches) == 0:
        return image
    match = matches[0]
    if len(match) < 3:
        log.warning(
            f"Failed to parse attributes from raw text: {text}, matches: {matches}"
        )
    title = match[0].strip()
    text_snippets = match[1].strip()
    description = match[2].strip()
    try:
        text_snippets = json.loads(text_snippets)
    except json.JSONDecodeError:
        log.warning(f"Failed to parse text snippets: {text_snippets}")
        text_snippets = []
    image.title = title
    image.text_snippets = text_snippets
    image.description = description

    return image


def merge_images(ims: list["Image"]) -> list["Image"]:
    """
    Merge images
    """
    mi: dict[str, "Image"] = {}
    for image in ims:
        if image.path not in mi:
            mi[image.path] = image
        else:
            log.info(f"Merge image: {image}, {mi[image.path]}")
            mi[image.path].title = image.title
            mi[image.path].chunks = remove_duplicates(
                mi[image.path].chunks + image.chunks
            )
    return list(mi.values())

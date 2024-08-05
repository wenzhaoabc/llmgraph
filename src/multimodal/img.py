"""
This module contains functions for processing images.
"""

import re
from itertools import groupby

from src.text_extract import get_nodes_relationships_from_rawtext
from src.tools import encode_image
from src.llm import LLM
from src.dataclass import Image, Chunk, Entity, Relationship
from .prompts import (
    EXTRACT_TEXT_PROMPT,
    EXTRACT_IMAGE_TITLE_PROMPT,
    EXTRACT_NODE_RELS_PROMPT,
)


def parse_text_snippets(text: str) -> list[str]:
    """
    Parses text snippets from the raw text outtput by LLM.
    """
    regex = r"\[(.*?)\]"
    result: list[str] = []
    matches = re.findall(regex, text, re.MULTILINE)

    for match in matches:
        raw_text = str(match).strip().split(",")
        if len(raw_text) < 1:
            continue
        text_snippet = raw_text[0].replace('"', "").strip()
        result.append(text_snippet)

    return result


def extract_image_text(image_path: str) -> list[str]:
    """
    Extracts text from images using OCR.
    """
    image_base64 = encode_image(image_path)
    messages = [
        {"role": "system", "content": EXTRACT_TEXT_PROMPT},
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": image_base64},
                }
            ],
        },
    ]
    llm = LLM()
    res = llm.chat(messages, callback=None, model="gpt-4o-mini")
    text_snippets = parse_text_snippets(res)
    return text_snippets


def extract_image_title(chunk: Chunk) -> dict[str, str]:
    """
    Extracts the title of images in a chunk.
    """
    regex = r"!\[(.*?)\]\((.*?)\)"
    matches = re.findall(regex, chunk.text, re.MULTILINE)
    image_titles = {}
    for match in matches:
        title = match[0].strip()
        path = match[1].strip()
        image_titles[path] = title

    image_paths = list(image_titles.keys())
    prompt = (
        EXTRACT_IMAGE_TITLE_PROMPT
        + "\n"
        + "Please extract titles for the following images: "
        + str(image_paths)
    )
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": chunk.text},
    ]

    llm = LLM()
    res = llm.chat(messages, callback=None, model="gpt-4o-mini")
    result: dict[str, str] = {}

    regex = r"<(.*?);(.*?)>"
    matches = re.findall(regex, res, re.MULTILINE)
    for match in matches:
        path = match[0].strip()
        title = match[1].strip()
        image_titles[path] = title
        result[path] = title
    return result


def extract_images(chunk: Chunk) -> list[Image]:
    regex = r"!\[(.*?)\]\((.*?)\)"
    matches = re.findall(regex, chunk.text, re.MULTILINE)
    image_titles = extract_image_title(chunk)
    images: list[Image] = []
    for match in matches:
        title = match[0].strip()
        path = match[1].strip()
        text_snippets = extract_image_text(path)
        image = Image(
            title=image_titles.get(path, title),
            path=path,
            text_snippets=text_snippets,
            chunks=[chunk.index],
        )
        images.append(image)

    return images


def similar_chunks(image: Image, chunks: list[Chunk]) -> list[int]:
    """
    Find similar chunks based on the text snippets extracted from an image
    """
    result = []
    for chunk in chunks:
        if any(snippet in chunk.text for snippet in image.text_snippets):
            result.append(chunk.index)

    return result


def merge_entity_rels(
    ens: list[Entity], rels: list[Relationship]
) -> tuple[list[Entity], list[Relationship]]:
    """
    Merge entities and relationships
    """
    merged_ens: list[Entity] = []
    merged_rels: list[Relationship] = []
    for name, group in groupby(ens, key=lambda x: x.name):
        group = list(group)
        entity = group[0]
        for e in group[1:]:
            entity.images.extend(e.images)
            entity.properties.update(e.properties)
            entity.references.extend(e.references)
            entity.references = list(set(entity.references))[:3]
        merged_ens.append(entity)

    for key, group in groupby(rels, key=lambda x: (x.start, x.type, x.end)):
        group = list(group)
        rel = group[0]
        for r in group[1:]:
            rel.images.extend(r.images)
            rel.properties.update(r.properties)
            rel.references.extend(r.references)
            rel.references = list(set(rel.references))[:3]
        merged_rels.append(rel)

    return merged_ens, merged_rels


def extract_entity_rels_images(
    chunks: list[Chunk],
    image: Image,
) -> tuple[list["Entity"], list["Relationship"]]:
    """
    Extract entities, relationships and images from a chunk
    """
    image_base64 = encode_image(image.path)
    messages = [
        {"role": "user", "content": EXTRACT_NODE_RELS_PROMPT},
        {
            "role": "user",
            "content": "The follwing is the markdown text:"
            + "\n".join([chunk.text for chunk in chunks]),
        },
        {
            "role": "user",
            "content": {
                "type": "image_url",
                "image_url": {"url": image_base64},
            },
        },
    ]
    llm = LLM()
    res = llm.chat(messages, callback=None, model="gpt-4o-mini")
    nodes_rels = get_nodes_relationships_from_rawtext(res)
    entitys = [Entity.from_dict(d=n) for n in nodes_rels["nodes"]]
    for e in entitys:
        if e.properties.has_key("references"):
            e.references = e.properties["references"]
            del e.properties["references"]

        if e.name in image.text_snippets:
            e.images = [image.path]

    rels = [Relationship.from_dict(r) for r in nodes_rels["relationships"]]
    for r in rels:
        if r.properties.has_key("references"):
            r.references = r.properties["references"]
            del r.properties["references"]

        if r.start in image.text_snippets or r.end in image.text_snippets:
            r.images = [image.path]

    return entitys, rels


"""
全文检索，查找可能chunk
实体与图片对应
多跳关系
检索测试

图表论文
PDF抽取
"""

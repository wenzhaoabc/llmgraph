"""
This module contains functions for processing images.
"""

import logging
import concurrent.futures

from text.tools import encode_image, merge_nearby_text
from text.llm import LLM
from text.parse_text_er import parse_rawtext_to_er
from dataclass import Image, Chunk, Entity, Relationship

from .text_parse import parse_attris_from_rawtext, parse_rawtext_images
from .prompts import (
    EXTRACT_IMAGE_ER_P,
    EXTRACT_IMAGE_ATTRS_P,
)


log = logging.getLogger("llmgraph")


def get_image_context_text(img: "Image", chunks: list["Chunk"]) -> str:
    """
    Get the context text of an image based on the chunks.
    """
    cs = [c for c in chunks if c.id in img.chunks or img.title in c.text]
    sorted(cs, key=lambda x: x.id)
    return merge_nearby_text([c.text for c in cs]) or ""


def extract_images_from_chunk(
    doc: "Chunk",
) -> list["Image"]:
    """
    Extract images from each chunk
    """
    imgs = parse_rawtext_images(doc.text)
    for img in imgs:
        img.chunks.append(doc.id)
    log.info(f"Extracted {len(imgs)} images from chunk {doc.id}")
    log.debug(f"Chunk {doc.id} Images: {imgs}")

    return imgs


def extract_image_attri(
    image: "Image",
    context_text: str,
    llm: "LLM",
) -> "Image":
    """
    Extracts the attributes of images in context text
    """
    image_base64 = encode_image(image.path)
    messages = [
        {"role": "system", "content": EXTRACT_IMAGE_ATTRS_P},
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"The image path is {image.path}. The image context: \n"
                    + context_text,
                },
                {"type": "image_url", "image_url": {"url": image_base64}},
            ],
        },
    ]
    res = llm.chat(messages, callback=None, model="gpt-4o-mini")
    log.debug(f"Extracted image attributes: image = {image}, llm res = {res}")
    image = parse_attris_from_rawtext(res, image)
    log.info(
        f"Extracted attributes for image {image.path}, image title = {image.title}"
    )

    return image


def batch_extract_image_attri(
    images: list["Image"],
    chunks: list["Chunk"],
    llm: "LLM",
    batch_size: int = 5,
) -> list["Image"]:
    """
    Batch extract attributes of images in context text
    """
    results: list["Image"] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=batch_size) as executor:
        futures = []
        for img in images:
            context_text = get_image_context_text(img, chunks)
            futures.append(executor.submit(extract_image_attri, img, context_text, llm))

        for future in concurrent.futures.as_completed(futures):
            img = future.result()
            results.append(img)
    return results


def extract_er_from_image(
    image: "Image",
    chunks: list["Chunk"],
    llm: "LLM",
) -> tuple[list["Entity"], list["Relationship"]]:
    """
    Extract entities, relationships and images from an image
    """
    image_encode = encode_image(image.path)
    image_context_text = get_image_context_text(image, chunks)
    prompt = "The following is the context of the image:\n" + image_context_text
    prompt += "\nImage Attributes: \n" + str(image.to_dict())

    messages = [
        {"role": "system", "content": EXTRACT_IMAGE_ER_P},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": image_encode},
                },
            ],
        },
    ]
    res = llm.chat(messages, callback=None, model="gpt-4o-mini")
    log.debug(f"Extracted ER from image {image}, llm res = {res}")
    es, rs = parse_rawtext_to_er(res)
    for e in es:
        e.images.append(image.path)
    for r in rs:
        r.images.append(image.path)
    return es, rs


def batch_extract_er_from_images(
    images: list["Image"],
    chunks: list["Chunk"],
    llm: "LLM",
    batch_size: int = 5,
) -> tuple[list["Entity"], list["Relationship"]]:
    """
    Batch extract entities and relationships from images
    """
    results: list[tuple[list["Entity"], list["Relationship"]]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=batch_size) as executor:
        futures = []
        for img in images:
            futures.append(executor.submit(extract_er_from_image, img, chunks, llm))

        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            results.append(result)
    entities: list["Entity"] = []
    relationships: list["Relationship"] = []
    for es, rs in results:
        entities.extend(es)
        relationships.extend(rs)

    return entities, relationships

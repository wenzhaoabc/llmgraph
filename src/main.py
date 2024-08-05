import re
import logging

import sys

sys.path[0] = sys.path[0] + "/../"

from src.prompts import SYSTEM_PROMPT, ALIGN_PROMPT, DEEP_RELS, QA_PROMPT
from src.llm import LLM
from src.text_extract import (
    get_nodes_relationships_from_rawtext,
    nodes_rels_combine_text,
    merge_nodes_rels,
)
from src.tools import encode_image
from src.dataclass import Chunk, Relationship, Entity, Image
from src.multimodal.img import (
    extract_images,
    extract_entity_rels_images,
    merge_entity_rels,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    stream=open("log.log", "w"),
)


def split_document(
    document: str, chunk_size: int = 1000, over_lap: float = 0.1
) -> list[str]:
    from langchain.text_splitter import MarkdownTextSplitter

    text_splitter = MarkdownTextSplitter(
        chunk_size=chunk_size, chunk_overlap=int(chunk_size * over_lap)
    )
    chunks = text_splitter.split_text(document)
    return chunks


def _extract_images_paths(document: str) -> list[str]:
    """
    提取文档中的图片路径和图片标题。
    """
    images = re.findall(r"!\[.*?\]\((.*?)\)", document)
    return images


def extract_entities_relations(
    chunk: Chunk, prompt
) -> tuple[list["Entity"], list["Relationship"]]:
    """
    使用LLM提取chunk中的实体及关系。
    """

    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": chunk.text},
    ]
    llm = LLM()
    # callback = lambda x: print(x, end="")
    res = llm.chat(messages, callback=None, model="gpt-4o-mini")
    logging.info(f"Extracted entities and relationships from chunk.llm res:\n {res}")

    nodes_rels = get_nodes_relationships_from_rawtext(res)
    entities = [Entity.from_dict(node) for node in nodes_rels["nodes"]]
    relationships = [Relationship.from_dict(rel) for rel in nodes_rels["relationships"]]
    for entity in entities:
        if entity.properties.get("references"):
            entity.references = entity.properties["references"]
            del entity.properties["references"]

    for rel in relationships:
        if rel.properties.get("references"):
            rel.references = rel.properties["references"]
            del rel.properties["references"]

    """
    images: list[Image] = extract_images(chunk)
    images = _extract_images_paths(chunk.text)
    merged_node_rels = nodes_rels

    for img in images:
        logging.info(f"Processing image: {img}")
        content = (
            IMAGE_PROMPT
            + "\nBelow is a list of entities and relationships extracted from the context of the image:\n"
            + nodes_rels_combine_text(merged_node_rels)
        )
        base64_image = encode_image(img)
        messages = [
            {"role": "system", "content": content},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": base64_image},
                    }
                ],
            },
        ]
        logging.info(f"Sending image to LLM messages: {messages}")
        images_nodes_rels_text = llm.chat(messages, callback=None, model="gpt-4o-mini")
        logging.info(
            f"Extracted entities and relationships from image.llm res:\n {images_nodes_rels_text}"
        )
        image_nodes_rels = get_nodes_relationships_from_rawtext(images_nodes_rels_text)
        for node in image_nodes_rels["nodes"]:
            if node["properties"]["images"]:
                node["properties"]["images"].append(img)
            else:
                node["properties"]["images"] = [img]
        for rel in image_nodes_rels["relationships"]:
            if rel["properties"]["images"]:
                rel["properties"]["images"].append(img)
            else:
                rel["properties"]["images"] = [img]
        merged_node_rels: dict[str, list] = merge_nodes_rels(
            merged_node_rels, image_nodes_rels
        )
    """
    return entities, relationships


def align_entities_relations(
    previous_result: dict[str, list], current_chunk: dict[str, list]
) -> dict[str, list]:
    """
    将上一个chunk的结果与当前chunk的结果一起发送给LLM，要求其完成实体及关系对齐。
    """
    prompt = (
        "Previous entities and relationships:\n"
        + nodes_rels_combine_text(previous_result)
        + "\nCurrent entities and relationships:"
        + nodes_rels_combine_text(current_chunk)
    )
    messages = [
        {"role": "system", "content": ALIGN_PROMPT},
        {"role": "user", "content": prompt},
    ]
    llm = LLM()
    res = llm.chat(messages, callback=None, model="gpt-4o-mini")
    logging.info(f"Aligned entities and relationships.llm res:\n {res}")
    return get_nodes_relationships_from_rawtext(res)


def dig_deep_relationships(nodes_rels: dict[str, list]):
    messages = [
        {"role": "system", "content": DEEP_RELS},
        {"role": "user", "content": nodes_rels_combine_text(nodes_rels)},
    ]
    llm = LLM()
    llm_res = llm.chat(messages, callback=None, model="gpt-4o-mini")
    logging.info(f"Deep relationships.llm res:\n {llm_res}")
    return get_nodes_relationships_from_rawtext(llm_res)


def main(doc_path: str):
    text = open(doc_path, "r", encoding="utf-8").read()
    chunks = split_document(text, chunk_size=8000)
    logging.info(
        f"Split document into chunks: {[c[:10]+'...'+c[-10:] for c in chunks]}"
    )
    chunks = [
        Chunk(index=i, text=chunk, length=len(chunk)) for i, chunk in enumerate(chunks)
    ]
    all_entities: list[Entity] = []
    all_relationships: list[Relationship] = []
    all_images: list[Image] = []
    all_nodes_rels = {"nodes": [], "relationships": []}
    entities, rels = extract_entities_relations(chunks[0], SYSTEM_PROMPT)
    all_entities.extend(entities)
    all_relationships.extend(rels)
    images: list[Image] = extract_images(chunks[0])
    all_images.extend(images)
    index = 1
    print("Process chunk 0")
    print(all_entities, all_relationships)
    print()

    for chunk in chunks[1:]:
        es, rs = extract_entities_relations(chunk=chunk, prompt=SYSTEM_PROMPT)
        imgs = extract_images(chunk)
        all_images.extend(imgs)
        print("Process chunk " + index.__str__())
        print(es, rs)
        print()

        logging.info(
            f"Extracted entities and relationships from chunk {index}: {es}; {rs}"
        )
        logging.info(f"Extracted images from chunk {index}: {imgs}")
        all_nodes_rels = align_entities_relations(
            {
                "nodes": [e.to_dict() for e in all_entities],
                "relationships": [r.to_dict() for r in all_relationships],
            },
            {
                "nodes": [e.to_dict() for e in es],
                "relationships": [r.to_dict() for r in rs],
            },
        )
        aes = [Entity.from_dict(node) for node in all_nodes_rels["nodes"]]
        ars = [Relationship.from_dict(rel) for rel in all_nodes_rels["relationships"]]
        all_entities.extend(aes)
        all_relationships.extend(ars)
        # 去重
        all_entities = list({e.name: e for e in all_entities}.values())
        all_relationships = list(
            {(r.start, r.type, r.end): r for r in all_relationships}.values()
        )
        all_images_temp = list({i.path: i for i in all_images}.values())
        for img in all_images_temp:
            for i2 in all_images:
                if i2.path == img.path:
                    img.chunks.extend(i2.chunks)
                    img.chunks = list(set(img.chunks))

        all_images = all_images_temp
        index += 1

    logging.info(f"Extract From text END")

    for img in all_images:
        es, rs = extract_entity_rels_images(
            [c for c in chunks if c.index in img.chunks], img
        )
        all_entities.extend(es)
        all_relationships.extend(rs)
        logging.info(
            f"Extracted entities and relationships from image {img.path}: {es}; {rs}"
        )
        all_entities, all_relationships = merge_entity_rels(
            all_entities, all_relationships
        )

    logging.info(f"Final entities: {all_entities}")
    logging.info(f"Final relationships: {all_relationships}")

    # 基于Entity和Relationships的问答
    question = input("Please input your question:\n")
    while question != "exit":
        # user_content =
        user_content = (
            "Entities:"
            + "\n".join([e.to_dict() for e in all_entities])
            + "Relationships: "
            + "\n".join([r.to_dict() for r in all_relationships])
            + "Images: "
            + "\n".join([img.to_dict() for img in all_images])
            + "Question: "
            + question
        )
        messages = [
            {"role": "system", "content": QA_PROMPT},
            {"role": "user", "content": user_content},
        ]
        llm = LLM()
        res = llm.chat(messages, callback=None, model="gpt-4o-mini")
        print(res)
        question = input("Please input your question:\n")
    with open("output.txt", "w") as f:
        f.write(f"Entities:\n{all_entities}\nRelationships:\n{all_relationships}")

if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv("../.env")
    text_path = "examples\chapter1-personal_support.md"
    main(text_path)

import re
import logging


from prompts import SYSTEM_PROMPT, IMAGE_PROMPT, ALIGN_PROMPT, DEEP_RELS
from llm import LLM
from text_extract import (
    get_nodes_relationships_from_rawtext,
    nodes_rels_combine_text,
    merge_nodes_rels,
)
from tools import encode_image

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(message)s", stream=open("log.txt", "w")
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


def extract_entities_relations(chunk: str, prompt) -> dict[str, list]:
    """
    使用LLM提取chunk中的实体及关系。
    """

    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": chunk},
    ]
    llm = LLM()
    # callback = lambda x: print(x, end="")
    res = llm.chat(messages, callback=None, model="gpt-4o-mini")
    logging.info(f"Extracted entities and relationships from chunk.llm res:\n {res}")

    nodes_rels = get_nodes_relationships_from_rawtext(res)
    images = _extract_images_paths(chunk)
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
    return merged_node_rels


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
    chunks = split_document(text, chunk_size=4000)
    logging.info(f"Split document into chunks: {chunks}")
    all_nodes_rels = extract_entities_relations(chunks[0], SYSTEM_PROMPT)
    index = 1
    for chunk in chunks[1:]:
        nodes_rels = extract_entities_relations(chunk=chunk, prompt=SYSTEM_PROMPT)
        print(f"Chunk {index} : nodes rels\n")
        print(nodes_rels)
        print()
        logging.info(
            f"Extracted entities and relationships from chunk {index}: {nodes_rels}"
        )
        all_nodes_rels = align_entities_relations(all_nodes_rels, nodes_rels)
        deep_rels = dig_deep_relationships(all_nodes_rels)
        print(f"Chunk {index} : deep rels\n")
        print(deep_rels)
        print()
        logging.info(f"Deep relationships: chunk {index}, deep_rels: {deep_rels}")
        all_nodes_rels = merge_nodes_rels(all_nodes_rels, deep_rels)
        index += 1


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv("../.env")
    text_path = "../examples/chapter1-personal_support.md"
    main(text_path)

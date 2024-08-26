"""
Extract entities and relationships from text
1. split the text into chunks
2. extract entities and relationships from each chunk
3. extract images from each chunk
4. align entities and relationships from each chunk with entities and relationships from previous chunks
5. remove duplicates
6. merge images from each chunk
7. extract entities and relationships from images
8. merge entities and relationships from text and images
"""

import logging
import concurrent.futures
from functools import partial
from langchain_text_splitters import MarkdownTextSplitter

from ..dataclass import Chunk, Entity, Relationship, Image
from ..multimodal import (
    extract_images_from_chunk,
    merge_images,
    batch_extract_image_attri,
    batch_extract_er_from_images,
)
from ..common.llm import LLM
from .prompts import (
    EXTRACT_ENTITY_REL_P,
    CONTINUE_EXTRACT_P,
    IF_COTINUE_P,
)
from .parse_text_er import parse_rawtext_to_er, merge_er, extract_acronym
from .merge_er import merge_er_by_llm

log = logging.getLogger("llmgraph")


def split_document(
    text: str, chunk_size: int = 4000, over_lap: int = 200
) -> list["Chunk"]:
    """
    Split the text into chunks
    """
    result_chunk: list["Chunk"] = []
    splitter = MarkdownTextSplitter(chunk_size=chunk_size, chunk_overlap=over_lap)
    chunks = splitter.split_text(text)
    for i, chunk in enumerate(chunks):
        c = Chunk(id=i, text=chunk, length=len(chunk))
        result_chunk.append(c)

    return result_chunk


def extract_acronym_extities(
    text: str, llm: LLM
) -> tuple[list["Entity"], list["Relationship"]]:
    """
    Extract entities from acronyms in text
    """
    entities: list["Entity"] = []
    acronyms = extract_acronym(text)
    prompt = "Full name and acronym:\n"
    prompt += ", ".join(
        [f"({full_text}, {acronym})" for full_text, acronym in acronyms]
    )
    prompt += "\nThe Text:\n" + text

    messages = [
        {"role": "system", "content": EXTRACT_ENTITY_REL_P},
        {"role": "user", "content": prompt},
    ]

    res = llm.chat(messages=messages, callback=None, model="gpt-4o-mini")
    log.debug(f"Extracted entities from acronyms in text, llm response: {res}")
    entities, rels = parse_rawtext_to_er(res)
    full_acronyms_dict = dict(acronyms)  #  {full_text: acronym }
    acronyms_full_dict = {acronym: full_text for full_text, acronym in acronyms}

    acronym_list = [acronym for _, acronym in acronyms]
    for e in entities:
        if e.name in acronym_list:
            e.name = acronyms_full_dict[e.name]
            e.properties["acroyum"] = full_acronyms_dict[e.name]

    for r in rels:
        if r.start in acronym_list:
            r.start = acronyms_full_dict[r.start]
        if r.end in acronym_list:
            r.end = acronyms_full_dict[r.end]

    return entities, rels


def extract_er_from_chunk(
    doc: "Chunk",
    llm: "LLM",
    loop_num: int = 1,
) -> tuple[list["Entity"], list["Relationship"]]:
    """
    Extract entities and relationships from each chunk
    """
    messages = [
        {"role": "system", "content": EXTRACT_ENTITY_REL_P},
        {"role": "user", "content": doc.text},
    ]

    raw_res = llm.chat(messages=messages, callback=None, model="gpt-4o-mini")
    llm_output = raw_res or ""
    log.debug(
        f"Extracted entities and relationships from chunk {doc.id}, llm response: {raw_res}"
    )
    for i in range(1, loop_num + 1, 1):
        messages += [
            {"role": "assistant", "content": raw_res},
            {"role": "user", "content": CONTINUE_EXTRACT_P},
        ]
        raw_res = llm.chat(messages=messages, callback=None, model="gpt-4o-mini")
        llm_output += raw_res or ""
        log.debug(
            f"Extract ER from chunk {doc.id} in LOOP {i+1}, messages: {messages} llm response: {raw_res}"
        )
        messages += [
            {"role": "assistant", "content": raw_res},
            {"role": "user", "content": IF_COTINUE_P},
        ]
        raw_res = llm.chat(messages=messages, callback=None, model="gpt-4o-mini")
        log.debug(
            f"IF continue extracte ER from chunk {doc.id} in LOOP {i+1}, messages: {messages} llm response: {raw_res}"
        )
        if "NO" in raw_res or "no" in raw_res:
            break

    log.debug(f"Extract ER from chunk {doc.id}, llm output: {llm_output}")
    entities, relationships = parse_rawtext_to_er(llm_output)

    es2, rs2 = extract_acronym_extities(doc.text, llm)
    log.info(
        f"Extract {len(es2)} entities and {len(rs2)} relationships from acronyms text, chunk {doc.id}"
    )
    log.debug(f"Acronym Entities Chunk {doc.id}: {es2}, Relationships: {rs2}")
    acronyms_full_dict = {
        e.properties.get("acroyum"): e.name for e in es2 if e.properties.get("acroyum")
    }
    for e in entities:
        if e.name in acronyms_full_dict.keys():
            e.name = acronyms_full_dict[e.name]

    for r in relationships:
        if r.start in acronyms_full_dict.keys():
            r.start = acronyms_full_dict[r.start]
        if r.end in acronyms_full_dict.keys():
            r.end = acronyms_full_dict[r.end]

    entities.extend(es2)
    relationships.extend(rs2)

    for e in entities:
        e.chunks.append(doc.id)
    for r in relationships:
        r.chunks.append(doc.id)

    log.info(
        f"Extracted {len(entities)} entities and {len(relationships)} relationships from chunk {doc.id}"
    )
    log.debug(f"Chunk {doc.id} Entities: {entities}, Relationships: {relationships}")
    return entities, relationships


def batch_extract_er_execute(
    chunks: list[Chunk], llm: "LLM", batch_size: int = 5
) -> tuple[list[Entity], list[Relationship]]:
    """
    Extract entities and relationships from each chunk in batch
    """
    results = []
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=batch_size, thread_name_prefix="text_er"
    ) as executor:
        futures = []
        for chunk in chunks:
            partial_func = partial(extract_er_from_chunk, chunk, llm)
            futures.append(executor.submit(partial_func))
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
    es: list[Entity] = []
    rs: list[Relationship] = []
    for res in results:
        es.extend(res[0])
        rs.extend(res[1])

    return es, rs


def process_text_er(
    chunks: list["Chunk"], llm: "LLM"
) -> tuple[list["Entity"], list["Relationship"]]:
    """
    Process text entities and relationships
    """
    es: list["Entity"] = []
    rs: list["Relationship"] = []
    batch_size = len(chunks) if len(chunks) < 8 else 8
    es, rs = batch_extract_er_execute(chunks, llm, batch_size)
    log.info(f"Extracted {len(es)} entities and {len(rs)} relationships from text")
    log.debug(f"Entities: {es}, Relationships: {rs}")
    es, rs = merge_er(es, rs)
    log.info(
        f"Merged entities and relationships. Entities: {len(es)}, Relationships: {len(rs)}"
    )
    es_str = "\n".join([str(e.to_dict()) for e in es])
    rs_str = "\n".join([str(r.to_dict()) for r in rs])
    log.debug(
        f"Merged Entities And Relationships:\n Entities:\n{es_str}, Relationships:\n{rs_str}"
    )
    return es, rs


def process_image_er(
    chunks: list["Chunk"], llm: "LLM"
) -> tuple[list["Entity"], list["Relationship"], list["Image"]]:
    """
    Process image entities and relationships
    """
    images: list["Image"] = []
    for chunk in chunks:
        images.extend(extract_images_from_chunk(chunk))
    log.info(f"Extracted {len(images)} images from text")
    images = merge_images(images)
    log.info(f"Merged images. Images: {len(images)}")
    log.debug(f"Merged Images: {images}")
    images = batch_extract_image_attri(images, chunks, llm)
    log.debug(f"Extracted attributes from images: {images}")
    es, rs = batch_extract_er_from_images(images, chunks, llm)
    log.info(f"Extracted {len(es)} entities and {len(rs)} relationships from images")
    log.debug(f"Image Entities: {es}, Relationships: {rs}")
    es, rs = merge_er(es, rs)
    log.info(
        f"Merged Image entities and relationships. Entities: {len(es)}, Relationships: {len(rs)}"
    )
    log.debug(f"Merged Image Entities: {es}, Relationships: {rs}")
    return es, rs, images


def pipeline(
    doc_path: str,
) -> tuple[list["Entity"], list["Relationship"], list["Image"]]:
    """
    Extract entities and relationships from text
    """
    with open(doc_path, "r", encoding="utf-8") as f:
        text = f.read()
    chunks = split_document(text)
    log.info(f"Split the text into {len(chunks)} chunks")
    llm = LLM()
    entities = []
    relationships = []
    entities, relationships = process_text_er(chunks, llm)
    ies, irs, images = process_image_er(chunks, llm)
    for img in images:
        for e in entities:
            if e.name in img.text_snippets:
                e.images.append(img.path)
    entities.extend(ies)
    relationships.extend(irs)
    entities, relationships = merge_er(entities, relationships)
    entities, relationships = merge_er_by_llm(entities, relationships, llm)
    entities, relationships = merge_er(entities, relationships)
    log.info(
        "Finished extracting ER Image from text, Entities: %d, Relationships: %d, Image: %d",
        len(entities),
        len(relationships),
        len(images),
    )
    entities_str = "\n".join([str(e.to_dict()) for e in entities])
    relationships_str = "\n".join([str(r.to_dict()) for r in relationships])
    images_str = "\n".join([str(i.to_dict()) for i in images])
    log.debug(
        f"Extracted Entities And Relationships:\nEntities:\n{entities_str}\nRelationships:\n{relationships_str}\nImages:\n{images_str}"
    )
    return entities, relationships, images

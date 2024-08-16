"""
Merge Entities and Relationships By LLM
1. generate a graph from the entities and relationships
2. weekly connected components
"""

import logging
import copy
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import networkx as nx

from dataclass import Entity, Relationship
from .llm import LLM
from .tools import remove_duplicates
from .prompts import MERGE_ER_P


log = logging.getLogger("llmgraph")


def get_entity_embedding(es: list["Entity"], llm: "LLM") -> dict[str, list[float]]:
    """
    Get the embedding of an entity
    """
    results: dict[str, list[float]] = {}
    with ThreadPoolExecutor(max_workers=8) as executor:
        features = [executor.submit(llm.embed, e.name) for e in es]
        for e, future in zip(es, features):
            e_embedding = future.result()
            results[e.name] = e_embedding
    return results


def create_graph(es: list["Entity"]) -> nx.DiGraph:
    """
    Create a graph from entities and relationships
    """

    def calculate_similarity(emb1: list[float], emb2: list[float]) -> float:
        v1 = np.array(emb1).reshape(1, -1)
        v2 = np.array(emb2).reshape(1, -1)
        return cosine_similarity(v1, v2)[0][0]

    entity_embeddings = get_entity_embedding(es, llm=LLM())
    G = nx.DiGraph()
    for e in es:
        G.add_node(e.name, entity=e)

    for i in range(len(es)):
        for j in range(i + 1, len(es)):
            e1_emb, e2_emb = (
                entity_embeddings[es[i].name],
                entity_embeddings[es[j].name],
            )
            similarity = calculate_similarity(e1_emb, e2_emb)
            if similarity > 0.9:
                G.add_edge(es[i].name, es[j].name, similarity=similarity)
    log.debug(f"Created graph from ER, nodes {G.nodes()}, edges {G.edges()}")
    return G


def get_er_groups(g: nx.Graph) -> list[list["Entity"]]:
    """
    Get connected components from the graph
    """
    sub_graphs = []
    for component in nx.weakly_connected_components(g):
        es = [g.nodes[n]["entity"] for n in component]
        sub_graphs.append(es)

    sub_graphs_str = "\n".join([', '.join([e.name for e in es]) for es in sub_graphs])
    log.debug(f"Get weekly connected subgraphs: \n{sub_graphs_str}")
    log.info(f"Merge Entity By LLM, Get {len(sub_graphs)} weekly connected subgraphs")
    return sub_graphs


def merge_e_with_llm(es: list["Entity"], llm: "LLM") -> list["Entity"]:
    """
    Merge entities by LLM
    """
    prompt = ["- " + e.to_origin_text() for e in es]
    messages = [
        {"role": "system", "content": MERGE_ER_P},
        {"role": "user", "content": "\n".join(prompt)},
    ]
    llm_res = llm.chat(messages, callback=None)
    log.debug(f"Merge ER with LLM, llm response: {llm_res}")
    if "NO" in llm_res.upper():
        return es
    merged_entity = Entity(
        name=es[0].name,
        label=es[0].label,
        images=remove_duplicates([i for e in es for i in e.images]),
        chunks=remove_duplicates([c for e in es for c in e.chunks]),
        properties={},
    )
    merged_entity.properties.update({"_alias": [e.name for e in es]})
    for e in es:
        merged_entity.properties.update(e.properties)

    return [merged_entity]


def merge_er_by_llm(
    es: list["Entity"], rs: list["Relationship"], llm: "LLM"
) -> tuple[list["Entity"], list["Relationship"]]:
    """
    Merge entities and relationships by LLM
    """

    def process_group(es_group: list["Entity"]) -> list["Entity"]:
        if len(es_group) == 1:
            return es_group
        return merge_e_with_llm(es_group, llm)

    g = create_graph(es)
    es_groups = get_er_groups(g)
    merged_es: list["Entity"] = []
    merged_rs: list["Relationship"] = []

    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_group, es_group) for es_group in es_groups]
        for future, group in zip(futures, es_groups):
            merged_res_es = future.result()
            if len(merged_res_es) > 1:
                merged_es.extend(merged_res_es)
            else:
                merged_e = merged_res_es[0]
                group_names = [e.name for e in group]
                merged_es.append(merged_e)
                for r in rs:
                    m_r = copy.deepcopy(r)
                    if m_r.start in group_names:
                        m_r.start = merged_e.name
                    if m_r.end in group_names:
                        m_r.end = merged_e.name
                    merged_rs.append(m_r)
    merged_es_str = "\n".join([str(e.to_dict()) for e in merged_es])
    merged_rs_str = "\n".join([str(r.to_dict()) for r in merged_rs])
    log.debug(
        f"Merged ER by LLM, merged entities: \n{merged_es_str}, relationships: \n{merged_rs_str}"
    )
    log.info(
        f"Merged Entity ly LLM, Entity: {len(merged_es)}, Relationships: {len(merged_rs)}"
    )
    return merged_es, merged_rs

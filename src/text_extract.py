"""
从大模型的回答中提取信息
"""

import re
import json
from itertools import groupby


def nodes_text_to_list_of_dict(nodes: str) -> list[dict]:
    regex = r"<(.*?)>"
    jsonRegex = r"\{.*\}"
    result = []
    matches = re.findall(regex, nodes, re.MULTILINE)

    for match in matches:
        raw_node = str(match).strip().split(",", 3)
        if len(raw_node) < 2:
            continue
        name = raw_node[0].replace('"', "").strip()
        label = raw_node[1].replace('"', "").strip()
        properties = re.search(jsonRegex, match)
        if properties is None:
            properties = None
        else:
            properties = properties.group(0)
        if properties is not None:
            properties = properties.replace("True", "true")
            properties = properties.replace("False", "false")
        try:
            properties = json.loads(properties)
        except:
            properties = {}
        result.append({"name": name, "label": label, "properties": properties})

    return result


def relationships_text_to_list_of_dict(relations: str) -> list[dict]:
    regex = r"<(.*?)>"
    jsonRegex = r"\{.*\}"

    result = []
    matches = re.findall(regex, relations, re.MULTILINE)

    for match in matches:
        raw_relationship = str(match).strip().split(",", 3)
        if len(raw_relationship) < 3:
            continue

        start = raw_relationship[0].replace('"', "").strip()
        relationship_type = raw_relationship[1].replace('"', "").strip()
        end = raw_relationship[2].replace('"', "").strip()

        properties = re.search(jsonRegex, match)
        if properties is None:
            properties = None
        else:
            properties = (
                properties.group(0)
                .strip()
                .replace("True", "true")
                .replace("False", "false")
            )
        try:
            properties = json.loads(properties)
        except:
            properties = {}

        result.append(
            {
                "start": start,
                "end": end,
                "type": relationship_type,
                "properties": properties,
            }
        )
    return result


def get_nodes_relationships_from_rawtext(rawtext: str) -> dict:
    regex = r"Nodes:\s*([\s\S]*?)Relationships:\s*([\s\S]*)"

    result = dict()
    matches = re.findall(regex, rawtext, re.DOTALL)

    raw_nodes = ""
    raw_relationships = ""

    for matchNum, match in enumerate(matches, start=1):
        if len(match) > 1:
            raw_nodes = match[0]
            raw_relationships = match[1]
        break

    result["nodes"] = []
    result["relationships"] = []

    result["nodes"].extend(nodes_text_to_list_of_dict(raw_nodes))
    result["relationships"].extend(
        relationships_text_to_list_of_dict(raw_relationships)
    )

    return result


def duplicate_nodes_relationships(data: dict[str, list]) -> dict:
    # 创建一个字典来存储合并后的节点和关系
    merged_nodes = {}
    merged_relationships = {}

    # 合并节点
    for node in data["nodes"]:
        key = (node["name"], node["label"])
        if key not in merged_nodes:
            merged_nodes[key] = node
        else:
            merged_nodes[key]["properties"].update(node["properties"])

    node_names = [node["name"] for node in list(merged_nodes.values())]

    # 合并关系
    for relationship in data["relationships"]:
        key = (relationship["start"], relationship["type"], relationship["end"])
        if key not in merged_relationships:
            start_key = relationship.get("start", None)
            end_key = relationship.get("end", None)
            if (start_key in node_names) and (end_key in node_names):
                merged_relationships[key] = relationship
        else:
            merged_relationships[key]["properties"].update(relationship["properties"])

    # 将合并后的节点和关系转换回列表
    data["nodes"] = list(merged_nodes.values())
    data["relationships"] = list(merged_relationships.values())

    return data


def nodes_rels_combine_text(kg: dict[str, list]) -> str:
    """
    将结构化的节点和关系组装成对应的字符串
    """
    nodes = sorted(kg["nodes"], key=lambda x: x["label"])
    relationships = sorted(kg["relationships"], key=lambda x: x["start"])
    nodes_str = ""
    for node in nodes:
        nodes_str += (
            '<'
            + node["name"]
            + ', '
            + node["label"]
            + ', '
            + json.dumps(node["properties"])
            + ">\n"
        )

    relationships_str = ""
    for relation in relationships:
        relationships_str += (
            '<'
            + relation["start"]
            + ', '
            + relation["type"]
            + ', '
            + relation["end"]
            + ', '
            + json.dumps(relation["properties"])
            + ">\n"
        )

    return f"Nodes:\n{nodes_str}Relationships:\n{relationships_str}"


def merge_nodes_rels(nr1: dict[str, list], nr2: dict[str, list]) -> dict[str, list]:
    """
    将具有同样名称的实体合并，将具有同样关系的关系合并，其中properties会合并。
    其中properties的images和references属性会合并。
    """

    def merge_properity_list_key(key: str, p1: dict, p2: dict) -> list:
        result = []
        if key in p1:
            result.extend(p1[key])
        if key in p2:
            result.extend(p2[key])
        return list(set(result))

    def merge_properties(p1: dict, p2: dict) -> dict:
        images = merge_properity_list_key("images", p1, p2)
        references = merge_properity_list_key("references", p1, p2)
        result = dict()
        result.update(p2)
        result["images"] = images
        result["references"] = references
        return result

    nodes = nr1["nodes"] + nr2["nodes"]
    relationships = nr1["relationships"] + nr2["relationships"]

    # 合并节点
    merged_nodes = {}
    for node in nodes:
        key = (node["name"], node["label"])
        if key not in merged_nodes:
            merged_nodes[key] = node
        else:
            merged_nodes[key]["properties"] = merge_properties(
                merged_nodes[key]["properties"], node["properties"]
            )

    # 合并关系
    merged_relationships = {}
    for relationship in relationships:
        key = (relationship["start"], relationship["type"], relationship["end"])
        if key not in merged_relationships:
            merged_relationships[key] = relationship
        else:
            merged_relationships[key]["properties"] = merge_properties(
                merged_relationships[key]["properties"], relationship["properties"]
            )

    return {
        "nodes": list(merged_nodes.values()),
        "relationships": list(merged_relationships.values()),
    }



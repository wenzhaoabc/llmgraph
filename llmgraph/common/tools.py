import base64
import os
from functools import lru_cache


@lru_cache
def encode_image(image_path: str) -> str:
    parent_path = os.path.abspath(os.path.join(os.environ.get("PYTHONPATH"), os.pardir))
    image_path = parent_path + "/examples/" + image_path
    with open(image_path, "rb") as image_file:
        image_data = image_file.read()

    base64_encoded = base64.b64encode(image_data).decode("utf-8")
    image_url = f"data:image/png;base64,{base64_encoded}"

    return image_url


def shorten_string(text: str, head_length: int, tail_length: int) -> str:
    """
    Shorten the string by keeping the head and tail of the string
    """
    if len(text) <= head_length + tail_length:
        return text
    return text[:head_length] + "..." + text[-tail_length:]


def remove_duplicates(lst: list, key=None) -> list:
    """
    Remove duplicates from a list. If key is provided, use it to determine uniqueness.
    """
    seen = set()
    result = []
    for item in lst:
        comparator = item if key is None else key(item)
        if comparator not in seen:
            seen.add(comparator)
            result.append(item)
    return result


def merge_nearby_text(text: list[str]) -> str:
    """
    Merge text snippets that are nearby
    """
    if not text:
        return ""

    merged_text = text[0]

    for i in range(1, len(text)):
        current_text = text[i]
        max_overlap = min(len(merged_text), len(current_text))
        overlap = ""

        for j in range(1, max_overlap + 1):
            if merged_text[-j:] == current_text[:j]:
                overlap = merged_text[-j:]

        merged_text += current_text[len(overlap) :]

    return merged_text

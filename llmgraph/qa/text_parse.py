"""
Text Parse with regex
"""

import re
import json
import logging

log = logging.getLogger("llmgraph")


def parse_keywords(text: str) -> list[str]:
    """
    Parse keywords from text
    """
    regex = r"(\[.*?\])"
    matches = re.findall(regex, text, re.MULTILINE)
    keywords = []
    for match in matches:
        try:
            json_str = match.strip()
            keywords.extend(json.loads(json_str))
        except:
            log.warning(f"Invalid keyword json: {json_str}")
    return keywords

"""
This module is the entry point of the package. It initializes the logging system.
"""

import sys
import logging
from datetime import datetime


def setup_logging():
    log = logging.getLogger("llmgraph")
    log.setLevel(logging.DEBUG)
    log_file_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    file_handler = logging.FileHandler(f"logs/{log_file_name}.log", "w", "utf-8")
    file_handler.setLevel(logging.DEBUG)

    stream_handler = logging.StreamHandler(stream=sys.stdout)
    stream_handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)-8s - %(filename)s:%(lineno)-3d - %(message)s"
    )
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    log.addHandler(file_handler)
    log.addHandler(stream_handler)


setup_logging()

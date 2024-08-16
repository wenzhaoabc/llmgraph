"""
This is the main file to run the pipeline.
"""

import sys
import pickle
import logging
import os
from datetime import datetime


from text.extract import pipeline


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

class LLMForEntityExctract:
    def __init__(self, initial_system_prompt):
        self.conversation_history = [
            {"role": "system", "content": initial_system_prompt},
        ]
        self.llm = LLM()

    def add_message_and_call_llm(self, new_message, model="gpt-4o-mini"):
        self.conversation_history.append({"role": "user", "content": new_message})
        res = self.llm.chat(self.conversation_history, callback=None, model=model)
        # assistant_message = res["choices"][0]["message"]["content"]
        # self.conversation_history.append({"role": "assistant", "content": assistant_message})
        self.conversation_history.append({"role": "assistant", "content": res})
        return res

def save_objects_to_file(obj_list, filename):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "wb") as f:
        pickle.dump(obj_list, f)


def main():
    es, rs, imgs = pipeline(text_path)
    # save to file
    save_objects_to_file(es, "res/entities.pkl")
    save_objects_to_file(rs, "res/relationships.pkl")
    save_objects_to_file(imgs, "res/images.pkl")
    print("Entities and relationships extracted successfully!")


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv("../.env")
    text_path = "examples/chapter1-personal_support.md"
    main()

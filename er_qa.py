"""
Question answering 
"""

import os
import re
import logging
import pickle

import gradio as gr


from llmgraph.qa.prompts import QUESTION_KEYWORDS, QA_PROMPT
from llmgraph.qa.text_parse import parse_keywords

from llmgraph.common import llm, tools
from llmgraph.dataclass import Entity, Relationship, Image


log = logging.getLogger("llmgraph")
log.addHandler(
    logging.StreamHandler(stream=open("logs/query.log", "w", encoding="utf-8"))
)
log.setLevel(logging.DEBUG)

entities: list["Entity"] = []
relationships: list["Relationship"] = []
images: list["Image"] = []
llm = llm.LLM()


def replace_local_images_with_url(text, base_url: str = None):
    """
    Replace local images with url
    """
    if not base_url:
        base_url = os.getenv("ASSESTS_PATH", "http://localhost:8000")
    pattern = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")

    def replace_match(match):
        alt_text = match.group(1)
        img_path = match.group(2)

        if not img_path.startswith("http://") and not img_path.startswith("https://"):
            img_url = f"{base_url}/{img_path}"
            return f"![{alt_text}]({img_url})"
        else:
            return match.group(0)

    return pattern.sub(replace_match, text)


def load_objects_from_file(filename):
    with open(filename, "rb") as f:
        return pickle.load(f)


def search_rels_by_entities(es: list["Entity"]) -> list["Relationship"]:
    """
    Search relationships by entities
    """
    result = []
    es_names = [e.name for e in es]
    for r in relationships:
        if r.start in es_names and r.end in es_names:
            result.append(r)

    return result


def search_extities_by_keywords(keywords: list[str]) -> list["Entity"]:
    result = []
    keywords = [k.upper() for k in keywords]
    e_words = {e.name.upper(): e for e in entities}
    for e in entities:
        e_words = [k.upper() for k in e.name.split(" ") if len(k) > 1]
        if any([w.upper() in e_words for w in keywords]):
            result.append(e)
        elif e.properties.get("_alias") and any(
            [w.upper() in keywords for w in e.properties.get("_alias")]
        ):
            result.append(e)
        elif (
            e.properties.get("acronym")
            and e.properties.get("acronym").upper() in keywords
        ):
            result.append(e)
        elif (
            e.properties.get("abbreviation")
            and e.properties.get("abbreviation").upper() in keywords
        ):
            result.append(e)
    return result


def search_images_by_entities(es: list["Entity"], imgs: list["Image"]) -> list["Image"]:
    """
    Search images by entities
    """
    result = []
    e_imgs = []
    for e in es:
        e_imgs.extend(e.images)
    for img in imgs:
        if img.path in e_imgs:
            result.append(img)
    return result


def answer_question(question: str):
    """
    Answer question
    """

    def call_back(rwa_res):
        yield rwa_res

    # extract key words
    messages = [
        {"role": "system", "content": QUESTION_KEYWORDS},
        {"role": "user", "content": "Question: " + question},
    ]
    key_words = llm.chat(messages=messages, callback=None, model="gpt-4o-mini")
    log.debug(
        f"Extracted keywords from question: {question}, llm response: {key_words}"
    )
    key_words = parse_keywords(key_words)
    log.info("Keyword length: " + str(len(key_words)))
    call_back("The question key words is " + ", ".join(key_words))

    # search entities
    es = search_extities_by_keywords(key_words)
    rs = search_rels_by_entities(es)
    imgs = search_images_by_entities(es, images)
    log.info("Entities: " + ", ".join([e.name for e in es]))
    log.info("Relationships: " + ", ".join([r.to_origin_text() for r in rs]))
    log.info("Images: " + ", ".join([i.to_origin_text() for i in imgs]))

    es_str = "\n".join([e.to_origin_text() for e in es])
    rs_str = "\n".join([r.to_origin_text() for r in rs])
    imgs_str = "\n".join([i.to_origin_text() for i in imgs])
    content = (
        "Question: "
        + question
        + "\nEntities:\n"
        + es_str
        + "\nRelationships:\n"
        + rs_str
    )
    if imgs:
        content += "\nImages:\n" + imgs_str

    user_conetnt = [
        {"type": "text", "text": content},
    ]
    for img in imgs:
        image_encode = tools.encode_image(img.path)
        user_conetnt.append(
            {
                "type": "image_url",
                "image_url": {"url": image_encode},
            },
        )

    messages = [
        {"role": "system", "content": QA_PROMPT},
        {"role": "user", "content": user_conetnt},
    ]

    res = llm.chat(messages=messages, callback=call_back, model="gpt-4o-mini")
    log.debug(f"Answer question: {question}, llm response: {res}")
    return res


def grdio_interface(user_input, history):
    print("user_input = ", user_input, "history = ", history)
    history = history or []
    user_input = history[-1][0] if history else user_input
    history[-1][1] = ""
    for r in answer_question(user_input):
        history[-1][1] += r
        history[-1][1] = replace_local_images_with_url(history[-1][1])
        yield history


def user(user_input, history):
    print("user", "user_input = ", user_input, "history = ", history)
    return "", history + [[user_input, None]]


with gr.Blocks() as demo:
    chatbot = gr.Chatbot(height=1200)
    msg = gr.Textbox(show_label=False, placeholder="Type your question here...")
    btn = gr.Button("Submit")
    with gr.Row():
        btn.click(user, [msg, chatbot], [msg, chatbot]).then(
            grdio_interface, [msg, chatbot], chatbot
        )


if __name__ == "__main__":
    entities = load_objects_from_file("res/entities.pkl")
    relationships = load_objects_from_file("res/relationships.pkl")
    images = load_objects_from_file("res/images.pkl")
    demo.launch()

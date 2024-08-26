"""
Parse text and extract entities and relationships
"""

import pickle
import os
import logging
from datetime import datetime

import gradio as gr

from llmgraph.general.extract import pipeline

log = logging.getLogger("llmgraph")


def save_objects_to_file(obj_list, filename):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "wb") as f:
        pickle.dump(obj_list, f)


def text_er(filepath: str):
    es, rs, imgs = pipeline(filepath)
    # save to file
    folder_name = datetime.now().strftime("%Y%m%d%H%M%S")
    folder_name = os.path.join("res", folder_name)
    os.makedirs(folder_name, exist_ok=True)
    save_objects_to_file(es, f"{folder_name}/entities.pkl")
    save_objects_to_file(rs, f"{folder_name}/relationships.pkl")
    save_objects_to_file(imgs, f"{folder_name}/images.pkl")
    print("Entities and relationships extracted successfully!")
    es_txt = "\n".join([str(e.to_dict()) for e in es])
    rs_txt = "\n".join([str(r.to_dict()) for r in rs])
    imgs_txt = "\n".join([str(i.to_dict()) for i in imgs])
    return es_txt, rs_txt, imgs_txt


face = gr.Interface(
    fn=text_er,
    inputs=gr.File(),
    outputs=[gr.Text(), gr.Text(), gr.Text()],
)

face.launch()

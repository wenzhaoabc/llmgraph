import base64
import os


def encode_image(image_path):
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"The file {image_path} does not exist.")

    with open(image_path, "rb") as image_file:
        image_data = image_file.read()

    base64_encoded = base64.b64encode(image_data).decode("utf-8")
    image_url = f"data:image/png;base64,{base64_encoded}"

    return image_url

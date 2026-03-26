import base64
import os
import requests


def upload_to_imgbb(image_path: str) -> str:
    """imgbb APIに画像をアップロードして公開URLを返す"""
    api_key = os.environ["IMGBB_API_KEY"]
    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")

    response = requests.post(
        "https://api.imgbb.com/1/upload",
        data={"key": api_key, "image": encoded},
        timeout=30,
    )
    response.raise_for_status()
    url = response.json()["data"]["url"]
    print(f"[upload] Image URL: {url}")
    return url

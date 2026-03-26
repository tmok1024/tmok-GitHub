import os
import time
import requests


GRAPH_URL = "https://graph.facebook.com/v21.0"


def post_to_instagram(image_url: str, caption: str, hashtags: list[str]) -> str:
    """Instagram Graph APIで画像を投稿し、投稿IDを返す"""
    user_id = os.environ["INSTAGRAM_USER_ID"]
    access_token = os.environ["INSTAGRAM_ACCESS_TOKEN"]

    full_caption = f"{caption}\n\n" + " ".join(f"#{tag}" for tag in hashtags)

    # Step 1: メディアコンテナ作成
    container_resp = requests.post(
        f"{GRAPH_URL}/{user_id}/media",
        params={
            "image_url": image_url,
            "caption": full_caption,
            "access_token": access_token,
        },
        timeout=30,
    )
    container_resp.raise_for_status()
    container_id = container_resp.json()["id"]
    print(f"[instagram] Container created: {container_id}")

    # Step 2: コンテナの準備完了を待機
    for attempt in range(10):
        status_resp = requests.get(
            f"{GRAPH_URL}/{container_id}",
            params={"fields": "status_code", "access_token": access_token},
            timeout=30,
        )
        status_resp.raise_for_status()
        status = status_resp.json().get("status_code")
        if status == "FINISHED":
            break
        if status == "ERROR":
            raise RuntimeError(f"Container processing failed: {status_resp.json()}")
        print(f"[instagram] Waiting for container... status={status} (attempt {attempt + 1})")
        time.sleep(5)
    else:
        raise TimeoutError("Container did not finish processing in time")

    # Step 3: 投稿公開
    publish_resp = requests.post(
        f"{GRAPH_URL}/{user_id}/media_publish",
        params={
            "creation_id": container_id,
            "access_token": access_token,
        },
        timeout=30,
    )
    publish_resp.raise_for_status()
    post_id = publish_resp.json()["id"]
    print(f"[instagram] Published! Post ID: {post_id}")
    return post_id

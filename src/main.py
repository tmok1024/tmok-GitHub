#!/usr/bin/env python3
"""Instagram 毎日自動投稿スクリプト"""
import sys
import os

# .envファイルがあればロード（ローカル開発用）
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from generate_content import generate_daily_tip
from create_image import create_tip_image
from upload_image import upload_to_imgbb
from post_instagram import post_to_instagram


def main() -> None:
    print("=== Instagram Auto Post: 開始 ===")

    # 1. コンテンツ生成
    print("[1/4] Claudeでコンテンツを生成中...")
    tip_data = generate_daily_tip()
    print(f"  カテゴリ: {tip_data['category']}")
    print(f"  見出し: {tip_data['headline']}")

    # 2. 画像生成
    print("[2/4] 投稿画像を作成中...")
    image_path = create_tip_image(tip_data, output_path="output/post.jpg")
    print(f"  保存先: {image_path}")

    # 3. 画像アップロード
    print("[3/4] imgbbに画像をアップロード中...")
    image_url = upload_to_imgbb(image_path)

    # 4. Instagram投稿
    print("[4/4] Instagramに投稿中...")
    post_id = post_to_instagram(
        image_url=image_url,
        caption=tip_data["caption"],
        hashtags=tip_data["hashtags"],
    )

    print(f"=== 完了！投稿ID: {post_id} ===")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

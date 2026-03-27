#!/usr/bin/env python3
"""
Instagram アクセストークン 更新ツール
-------------------------------------
既存の長期トークンを再度60日延長します。
（長期トークンは有効期限内であれば延長可能です）

使い方:
    python tools/refresh_token.py
"""
import os
import sys

import requests

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
except ImportError:
    pass

GRAPH_URL = "https://graph.facebook.com/v21.0"
ENV_FILE  = os.path.join(os.path.dirname(__file__), "..", ".env")


def refresh_long_token(app_id: str, app_secret: str, current_token: str) -> str:
    resp = requests.get(
        f"{GRAPH_URL}/oauth/access_token",
        params={
            "grant_type":        "fb_exchange_token",
            "client_id":         app_id,
            "client_secret":     app_secret,
            "fb_exchange_token": current_token,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def update_env(key: str, value: str) -> None:
    lines = []
    updated = False
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE) as f:
            for line in f:
                if line.strip().startswith(f"{key}="):
                    lines.append(f"{key}={value}\n")
                    updated = True
                else:
                    lines.append(line)
    if not updated:
        lines.append(f"{key}={value}\n")
    with open(ENV_FILE, "w") as f:
        f.writelines(lines)


def main():
    print("=== Instagram トークン更新 ===\n")

    app_id        = input("Meta アプリID: ").strip()
    app_secret    = input("Meta アプリシークレット: ").strip()
    current_token = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "")

    if not current_token:
        current_token = input("現在のアクセストークン: ").strip()

    if not all([app_id, app_secret, current_token]):
        print("ERROR: 必要な情報が不足しています。")
        sys.exit(1)

    try:
        new_token = refresh_long_token(app_id, app_secret, current_token)
        update_env("INSTAGRAM_ACCESS_TOKEN", new_token)
        print("\n✅ トークンを更新しました（60日延長）")
        print("  .env の INSTAGRAM_ACCESS_TOKEN を更新済み")
        print("  GitHub Secrets も忘れずに更新してください！")
    except requests.HTTPError as e:
        print(f"\nERROR: トークン更新失敗: {e.response.text}")
        sys.exit(1)


if __name__ == "__main__":
    main()

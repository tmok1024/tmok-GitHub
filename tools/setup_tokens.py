#!/usr/bin/env python3
"""
Instagram自動投稿システム セットアップツール
----------------------------------------
このスクリプトは以下を自動処理します：
  1. Meta OAuth認証フロー（ブラウザ起動 → コールバック受信）
  2. 短期トークン → 長期トークン（60日）に交換
  3. Instagram ビジネスアカウントIDの取得
  4. すべてを .env ファイルに保存

事前準備（手動）：
  - https://developers.facebook.com でMetaアプリを作成済みであること
  - アプリのリダイレクトURIに http://localhost:8888/callback を追加済みであること
  - InstagramアカウントをプロアカウントにしてMetaページと連携済みであること
"""
import http.server
import json
import os
import sys
import threading
import urllib.parse
import webbrowser

import requests

# ─── 定数 ───────────────────────────────────────────────────────────────────
GRAPH_URL     = "https://graph.facebook.com/v21.0"
REDIRECT_URI  = "http://localhost:8888/callback"
PERMISSIONS   = "instagram_basic,instagram_content_publish,pages_show_list,pages_read_engagement"
ENV_FILE      = os.path.join(os.path.dirname(__file__), "..", ".env")
PORT          = 8888


# ─── OAuth コールバックサーバー ──────────────────────────────────────────────
_auth_code: str | None = None
_auth_error: str | None = None
_server_done = threading.Event()


class _CallbackHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        global _auth_code, _auth_error
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if "code" in params:
            _auth_code = params["code"][0]
            body = b"<h2>\u2705 \u8a8d\u8a3c\u6210\u529f\uff01\u3053\u306e\u30bf\u30d6\u3092\u9589\u3058\u3066\u30bf\u30fc\u30df\u30ca\u30eb\u306b\u623b\u3063\u3066\u304f\u3060\u3055\u3044\u3002</h2>"
        else:
            _auth_error = params.get("error_description", ["unknown error"])[0]
            body = f"<h2>\u274c \u30a8\u30e9\u30fc: {_auth_error}</h2>".encode()

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body)
        _server_done.set()

    def log_message(self, *_):
        pass  # ログを抑制


def _start_callback_server():
    server = http.server.HTTPServer(("localhost", PORT), _CallbackHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server


# ─── Meta Graph API ヘルパー ─────────────────────────────────────────────────
def _exchange_short_token(app_id: str, app_secret: str, code: str) -> str:
    """認証コード → 短期アクセストークン"""
    resp = requests.get(
        f"{GRAPH_URL}/oauth/access_token",
        params={
            "client_id":     app_id,
            "client_secret": app_secret,
            "redirect_uri":  REDIRECT_URI,
            "code":          code,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def _exchange_long_token(app_id: str, app_secret: str, short_token: str) -> str:
    """短期トークン → 長期トークン（60日）"""
    resp = requests.get(
        f"{GRAPH_URL}/oauth/access_token",
        params={
            "grant_type":        "fb_exchange_token",
            "client_id":         app_id,
            "client_secret":     app_secret,
            "fb_exchange_token": short_token,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def _get_instagram_user_id(long_token: str) -> tuple[str, str]:
    """Metaページ一覧からInstagramビジネスアカウントIDを取得"""
    resp = requests.get(
        f"{GRAPH_URL}/me/accounts",
        params={"access_token": long_token},
        timeout=30,
    )
    resp.raise_for_status()
    pages = resp.json().get("data", [])

    if not pages:
        raise RuntimeError(
            "Metaページが見つかりません。\n"
            "InstagramをMetaページと連携しているか確認してください。"
        )

    # 各ページのInstagramアカウントIDを取得
    for page in pages:
        page_id    = page["id"]
        page_token = page["access_token"]
        ig_resp = requests.get(
            f"{GRAPH_URL}/{page_id}",
            params={
                "fields":       "instagram_business_account",
                "access_token": page_token,
            },
            timeout=30,
        )
        ig_resp.raise_for_status()
        ig_data = ig_resp.json().get("instagram_business_account")
        if ig_data:
            return ig_data["id"], page_token

    raise RuntimeError(
        "Instagramビジネスアカウントが見つかりません。\n"
        "InstagramアカウントがプロアカウントでMetaページと連携しているか確認してください。"
    )


# ─── .env 書き込み ────────────────────────────────────────────────────────────
def _write_env(data: dict[str, str]) -> None:
    existing = {}
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE) as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    existing[k.strip()] = v.strip()
    existing.update(data)

    with open(ENV_FILE, "w") as f:
        for k, v in existing.items():
            f.write(f"{k}={v}\n")


# ─── メイン ──────────────────────────────────────────────────────────────────
def main():
    print("=" * 56)
    print("  Instagram 自動投稿システム セットアップ")
    print("=" * 56)

    # ── STEP 0: 事前確認 ────────────────────────────────
    print("""
【事前準備チェックリスト】
  □ https://developers.facebook.com でMetaアプリを作成済み
  □ アプリに「Instagram Graph API」製品を追加済み
  □ リダイレクトURI に http://localhost:8888/callback を追加済み
  □ Instagramをプロアカウントに切り替え、Metaページと連携済み

続行しますか？ (y/n): """, end="")
    if input().strip().lower() != "y":
        print("セットアップを中止しました。")
        sys.exit(0)

    # ── STEP 1: アプリ情報の入力 ─────────────────────────
    print("\n[1/5] Meta アプリ情報を入力してください")
    print("  → https://developers.facebook.com/apps → アプリ → 設定 → ベーシック")
    app_id     = input("  アプリID: ").strip()
    app_secret = input("  アプリシークレット: ").strip()

    if not app_id or not app_secret:
        print("ERROR: アプリIDとシークレットは必須です。")
        sys.exit(1)

    # ── STEP 2: ブラウザでOAuth認証 ──────────────────────
    print("\n[2/5] ブラウザでFacebook/Instagram認証を行います...")
    auth_url = (
        "https://www.facebook.com/v21.0/dialog/oauth"
        f"?client_id={app_id}"
        f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
        f"&scope={PERMISSIONS}"
        "&response_type=code"
    )

    server = _start_callback_server()
    print(f"  認証URL（自動でブラウザが開きます）:\n  {auth_url}\n")
    webbrowser.open(auth_url)
    print("  ブラウザで認証を完了してください...")

    _server_done.wait(timeout=120)
    server.shutdown()

    if _auth_error:
        print(f"\nERROR: OAuth認証エラー: {_auth_error}")
        sys.exit(1)
    if not _auth_code:
        print("\nERROR: タイムアウト（120秒以内に認証されませんでした）")
        sys.exit(1)

    print("  ✅ 認証コードを受信しました")

    # ── STEP 3: トークン交換 ─────────────────────────────
    print("\n[3/5] アクセストークンを取得中...")
    try:
        short_token = _exchange_short_token(app_id, app_secret, _auth_code)
        long_token  = _exchange_long_token(app_id, app_secret, short_token)
        print("  ✅ 長期アクセストークン（60日）を取得しました")
    except requests.HTTPError as e:
        print(f"\nERROR: トークン取得失敗: {e.response.text}")
        sys.exit(1)

    # ── STEP 4: Instagram ユーザーID取得 ──────────────────
    print("\n[4/5] Instagram ビジネスアカウントIDを取得中...")
    try:
        ig_user_id, _ = _get_instagram_user_id(long_token)
        print(f"  ✅ Instagram ユーザーID: {ig_user_id}")
    except (RuntimeError, requests.HTTPError) as e:
        print(f"\nERROR: {e}")
        sys.exit(1)

    # ── STEP 5: Anthropic APIキーの入力 ──────────────────
    print("\n[5/5] Anthropic APIキーを入力してください")
    print("  → https://console.anthropic.com/settings/keys でAPIキーを発行")
    anthropic_key = input("  Anthropic APIキー: ").strip()

    # imgbb APIキー（任意）
    print("\n  [オプション] imgbb APIキーを入力してください")
    print("  → https://api.imgbb.com でAPIキーを発行（無料）")
    imgbb_key = input("  imgbb APIキー（スキップするならEnter）: ").strip()

    # ── .env 保存 ────────────────────────────────────────
    env_data = {
        "ANTHROPIC_API_KEY":      anthropic_key,
        "INSTAGRAM_USER_ID":      ig_user_id,
        "INSTAGRAM_ACCESS_TOKEN": long_token,
    }
    if imgbb_key:
        env_data["IMGBB_API_KEY"] = imgbb_key

    _write_env(env_data)

    print(f"""
{'=' * 56}
  ✅ セットアップ完了！
{'=' * 56}

  .env ファイルに以下を保存しました：
    ANTHROPIC_API_KEY      = {'*' * 8}...
    INSTAGRAM_USER_ID      = {ig_user_id}
    INSTAGRAM_ACCESS_TOKEN = {'*' * 8}...{'IMGBB_API_KEY          = ' + '*' * 8 + '...' if imgbb_key else ''}

  ⚠️  アクセストークンの有効期限は60日です。
      期限前に以下で更新してください：
        python tools/setup_tokens.py

  次のステップ：
    1. GitHub Secrets に .env の値を登録する
       → リポジトリ Settings → Secrets and variables → Actions
    2. 動作確認（ローカル）:
         cd src && python main.py
    3. GitHub Actions で手動実行して確認
{'=' * 56}
""")


if __name__ == "__main__":
    main()

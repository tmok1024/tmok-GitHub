# Instagram 毎日自動投稿システム

Claude APIでライフハックTipsコンテンツを生成し、毎日自動でInstagramに投稿するシステムです。

## アーキテクチャ

```
GitHub Actions (毎朝9時 JST)
  ↓
Claude API → コンテンツ生成（見出し・Tips・キャプション・ハッシュタグ）
  ↓
Pillow → 投稿画像生成 (1080×1080px)
  ↓
imgbb API → 画像を公開URLにアップロード
  ↓
Instagram Graph API → 投稿
```

## セットアップ手順

### 1. Instagram / Meta 設定

1. **Metaビジネスアカウント**を作成（https://business.facebook.com）
2. **Instagramをプロアカウント**（クリエイターまたはビジネス）に切り替え
3. **Meta for Developers** (https://developers.facebook.com) でアプリを作成
   - アプリタイプ: ビジネス
   - 製品を追加: `Instagram Graph API`
4. **Instagram Basic Display API** または **Instagram Graph API** でアクセストークン取得
   - 必要な権限: `instagram_basic`, `instagram_content_publish`
5. **Instagramユーザー ID** を取得:
   ```
   GET https://graph.facebook.com/v21.0/me/accounts?access_token={TOKEN}
   ```
   取得したページIDを使って:
   ```
   GET https://graph.facebook.com/v21.0/{PAGE_ID}?fields=instagram_business_account&access_token={TOKEN}
   ```

> ⚠️ アクセストークンの有効期限は60日です。定期的に更新するか、長期トークン取得フローを実装してください。

### 2. imgbb APIキー取得

1. https://imgbb.com でアカウント作成
2. https://api.imgbb.com でAPIキーを発行

### 3. GitHub Secrets 設定

リポジトリの **Settings → Secrets and variables → Actions** で以下を追加:

| シークレット名 | 内容 |
|---|---|
| `ANTHROPIC_API_KEY` | Anthropic APIキー |
| `INSTAGRAM_USER_ID` | InstagramビジネスアカウントID |
| `INSTAGRAM_ACCESS_TOKEN` | Instagramアクセストークン |
| `IMGBB_API_KEY` | imgbb APIキー |

### 4. 動作確認

GitHub ActionsタブからWorkflowを手動実行（`workflow_dispatch`）して確認できます。

## ローカル実行

```bash
# 依存パッケージインストール
pip install -r requirements.txt

# .envファイル作成
cp .env.example .env
# .envを編集してAPIキーを設定

# 実行
cd src
python main.py
```

## 投稿スケジュール変更

`.github/workflows/daily_post.yml` の cron 式を変更してください:

```yaml
- cron: '0 0 * * *'   # 09:00 JST (デフォルト)
- cron: '0 1 * * *'   # 10:00 JST
- cron: '30 22 * * *' # 07:30 JST
```

## マネタイズ戦略

このシステムが生成するコンテンツは以下のマネタイズに最適化されています:

- **アフィリエイト**: 節約・仕事術カテゴリで商品リンクをストーリーやプロフィールに掲載
- **インフルエンサー案件**: フォロワー数増加後にブランド案件を獲得
- **デジタル商品**: まとめPDF・有料noteへの誘導
- **コンサルティング**: 専門性を活かしたオンライン相談

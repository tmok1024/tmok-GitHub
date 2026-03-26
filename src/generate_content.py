import anthropic
import json
import os
from datetime import datetime


def generate_daily_tip() -> dict:
    """Claude APIを使って今日のライフハックTipsを生成する"""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    today = datetime.now()
    day_of_year = today.timetuple().tm_yday

    prompt = f"""あなたはInstagramで人気のライフハック・Tipsアカウントの運営者です。
今日（{today.strftime('%Y年%m月%d日')}）の投稿コンテンツを作成してください。

以下のJSONフォーマット**のみ**で出力してください（前後の説明文は不要）：
{{
  "tip_number": {day_of_year},
  "category": "カテゴリ（仕事術/節約/健康/人間関係/学習/時間管理 から1つ選択）",
  "headline": "キャッチーな見出し（18文字以内）",
  "tips": [
    "具体的なTip1（32文字以内）",
    "具体的なTip2（32文字以内）",
    "具体的なTip3（32文字以内）",
    "具体的なTip4（32文字以内）"
  ],
  "caption": "Instagram投稿用キャプション。絵文字を使い読者に価値を提供する文章（180文字以内）",
  "hashtags": ["lifehack", "ライフハック", "生活の知恵", "仕事効率化", "節約術", "時間管理", "自己啓発", "朝活", "ビジネス", "スキルアップ", "tips", "豆知識", "生活改善", "毎日投稿", "有益な情報", "暮らしのコツ", "ためになる", "知識", "勉強", "成長"]
}}

条件：
- 今すぐ実践できる具体的なTips
- アフィリエイトや商品紹介に繋がりやすいトピックを優先
- 親しみやすく読みやすい日本語
- ハッシュタグは毎回同じリストで固定"""

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )

    content = message.content[0].text.strip()
    start = content.find("{")
    end = content.rfind("}") + 1
    return json.loads(content[start:end])

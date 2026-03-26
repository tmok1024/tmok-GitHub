import os
import textwrap
from PIL import Image, ImageDraw, ImageFont

FONT_PATH = os.environ.get(
    "FONT_PATH",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
)

COLOR_SCHEMES = {
    "仕事術":   {"top": (21, 67, 96),   "bot": (10, 40, 58),   "accent": (93, 173, 226)},
    "節約":     {"top": (27, 79, 45),   "bot": (14, 50, 28),   "accent": (88, 214, 141)},
    "健康":     {"top": (120, 40, 100), "bot": (70, 20, 60),   "accent": (241, 148, 138)},
    "人間関係": {"top": (86, 61, 20),   "bot": (50, 35, 10),   "accent": (244, 208, 63)},
    "学習":     {"top": (14, 74, 74),   "bot": (8, 44, 44),    "accent": (72, 201, 176)},
    "時間管理": {"top": (120, 35, 35),  "bot": (70, 20, 20),   "accent": (240, 128, 128)},
}
DEFAULT_SCHEME = COLOR_SCHEMES["仕事術"]


def load_font(size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except Exception:
        return ImageFont.load_default()


def draw_gradient(draw: ImageDraw.Draw, w: int, h: int, top: tuple, bot: tuple) -> None:
    for y in range(h):
        r_ratio = y / h
        r = int(top[0] + (bot[0] - top[0]) * r_ratio)
        g = int(top[1] + (bot[1] - top[1]) * r_ratio)
        b = int(top[2] + (bot[2] - top[2]) * r_ratio)
        draw.line([(0, y), (w, y)], fill=(r, g, b))


def wrap_cjk(text: str, draw: ImageDraw.Draw, font: ImageFont.FreeTypeFont, max_px: int) -> list[str]:
    """CJKテキストをmax_px幅に収まるよう折り返す"""
    lines = []
    current = ""
    for ch in text:
        test = current + ch
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_px:
            current = test
        else:
            if current:
                lines.append(current)
            current = ch
    if current:
        lines.append(current)
    return lines


def create_tip_image(tip_data: dict, output_path: str = "output/post.jpg") -> str:
    W, H = 1080, 1080
    scheme = COLOR_SCHEMES.get(tip_data.get("category", ""), DEFAULT_SCHEME)

    # --- ベース画像（RGBA） ---
    base = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    draw = ImageDraw.Draw(base)
    draw_gradient(draw, W, H, scheme["top"], scheme["bot"])

    # --- 装飾円 ---
    for cx, cy, r in [(960, 80, 220), (0, 960, 180), (W // 2, H + 60, 160)]:
        for dr in range(r, 0, -20):
            alpha = int(18 * (1 - dr / r))
            overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            od = ImageDraw.Draw(overlay)
            od.ellipse([cx - dr, cy - dr, cx + dr, cy + dr],
                       outline=(*scheme["accent"], alpha))
            base = Image.alpha_composite(base, overlay)

    # --- メインカード（半透明） ---
    card = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cd = ImageDraw.Draw(card)
    cd.rounded_rectangle([60, 330, W - 60, H - 65], radius=32, fill=(0, 0, 0, 110))
    base = Image.alpha_composite(base, card)

    draw = ImageDraw.Draw(base)

    # フォント
    f_header = load_font(30)
    f_num    = load_font(100)
    f_badge  = load_font(26)
    f_head   = load_font(62)
    f_tip    = load_font(36)
    f_footer = load_font(28)

    WHITE      = (255, 255, 255, 255)
    WHITE_DIM  = (210, 210, 210, 255)
    ACCENT     = (*scheme["accent"], 255)
    DARK       = (20, 20, 20, 255)

    PAD = 88

    # ヘッダー「LIFEHACK TIPS」
    draw.text((PAD, 68), "💡  LIFEHACK TIPS", font=f_header, fill=WHITE)
    draw.line([(PAD, 130), (W - PAD, 130)], fill=(*scheme["accent"], 160), width=2)

    # Tip番号
    tip_num = f"#{str(tip_data.get('tip_number', 1)).zfill(3)}"
    draw.text((PAD, 148), tip_num, font=f_num, fill=ACCENT)

    # カテゴリバッジ
    badge_txt = f"  {tip_data.get('category', '')}  "
    bx, by = PAD, 278
    bbox = draw.textbbox((bx, by), badge_txt, font=f_badge)
    draw.rounded_rectangle([bbox[0] - 4, bbox[1] - 4, bbox[2] + 4, bbox[3] + 4],
                            radius=14, fill=ACCENT)
    draw.text((bx, by), badge_txt, font=f_badge, fill=DARK)

    # 見出し
    headline = tip_data.get("headline", "")
    hl_lines = wrap_cjk(f"「{headline}」", draw, f_head, W - PAD * 2)
    hy = 348
    for line in hl_lines:
        draw.text((PAD, hy), line, font=f_head, fill=WHITE)
        hy += 74

    # Tipsリスト
    tips = tip_data.get("tips", [])
    ty = max(hy + 20, 530)
    for tip in tips[:4]:
        # アクセントドット
        draw.ellipse([PAD, ty + 8, PAD + 22, ty + 30], fill=ACCENT)
        # テキスト（折り返し）
        tip_lines = wrap_cjk(tip, draw, f_tip, W - PAD * 2 - 44)
        for tl in tip_lines:
            draw.text((PAD + 36, ty), tl, font=f_tip, fill=WHITE_DIM)
            ty += 46
        ty += 14

    # フッター
    draw.line([(PAD, H - 100), (W - PAD, H - 100)], fill=(*scheme["accent"], 80), width=1)
    draw.text((PAD, H - 80), "@lifehack.tips.jp", font=f_footer, fill=ACCENT)
    draw.text((W - 220, H - 80), "毎日更新 🔔", font=f_footer, fill=WHITE_DIM)

    # JPEG保存
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    final = base.convert("RGB")
    final.save(output_path, "JPEG", quality=95)
    return output_path

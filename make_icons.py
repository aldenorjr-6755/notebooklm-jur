# -*- coding: utf-8 -*-
"""
Gera ícones (.ico) para os três conversores PDF -> Markdown.
Mesma identidade visual; cor e rótulo diferentes para distinguir cada app.
"""
import os
from PIL import Image, ImageDraw, ImageFont

S = 256  # resolução base


def _font(size, bold=True):
    names = (["arialbd.ttf", "segoeuib.ttf"] if bold else ["arial.ttf", "segoeui.ttf"])
    for n in names:
        try:
            return ImageFont.truetype(n, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _rounded(draw, box, r, fill):
    draw.rounded_rectangle(box, radius=r, fill=fill)


def make_icon(path, accent, accent_dark, label):
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # Fundo arredondado com a cor de destaque
    _rounded(d, [8, 8, S - 8, S - 8], 46, accent_dark)
    _rounded(d, [8, 8, S - 8, S - 16], 46, accent)

    # Página (documento) branca, com canto dobrado
    px0, py0, px1, py1 = 64, 40, 192, 196
    fold = 34
    page = [
        (px0, py0), (px1 - fold, py0), (px1, py0 + fold),
        (px1, py1), (px0, py1),
    ]
    # sombra leve
    d.polygon([(x + 4, y + 6) for (x, y) in page], fill=(0, 0, 0, 60))
    d.polygon(page, fill=(255, 255, 255, 255))
    # canto dobrado
    d.polygon([(px1 - fold, py0), (px1 - fold, py0 + fold), (px1, py0 + fold)],
              fill=(225, 228, 232, 255))

    # "linhas de texto" na página
    for i, w in enumerate((96, 108, 80, 104, 72)):
        y = py0 + 30 + i * 20
        d.rounded_rectangle([px0 + 18, y, px0 + 18 + w, y + 8], radius=4,
                            fill=(176, 182, 190, 255))

    # Badge inferior com o rótulo (ex.: "M↓", "OCR", "AI")
    bf = _font(56 if len(label) <= 2 else 40)
    tb = d.textbbox((0, 0), label, font=bf)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]
    bw = max(tw + 44, 96)
    bx0 = (S - bw) // 2
    by1 = S - 18
    by0 = by1 - 64
    _rounded(d, [bx0, by0, bx0 + bw, by1], 22, (255, 255, 255, 255))
    d.text(((S - tw) // 2 - tb[0], (by0 + by1) // 2 - th // 2 - tb[1]),
           label, font=bf, fill=accent_dark)

    img.save(path, sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
    print("gerado:", path)


HERE = os.path.dirname(os.path.abspath(__file__))

# Os tres apps antigos (pdf2md_app, _tesseract, _marker) foram apagados em
# 2026-07-27; sobrou o `pdf2md`, que os substitui. O icone e' gravado na RAIZ
# do projeto porque e' ali que `pdf2md/empacotar.py` o procura ao gerar o .exe.
TARGETS = [
    # arquivo de saida     accent          accent_dark      rótulo
    ("pdf2md.ico",         (37, 99, 235),  (29, 64, 175),  "M↓"),   # azul
]

if __name__ == "__main__":
    for nome, accent, dark, label in TARGETS:
        out = os.path.join(HERE, nome)
        make_icon(out, accent, dark, label)

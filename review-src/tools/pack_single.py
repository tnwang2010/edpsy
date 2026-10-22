#!/usr/bin/env python3
"""把某一週的網頁打包成單一 .html（樣式與圖片內嵌），方便在上線前寄給老師審閱。

用法：python3 review-src/tools/pack_single.py review/week01/index.html 輸出檔.html
"""
import base64, os, re, sys

src, dst = sys.argv[1], sys.argv[2]
d = os.path.dirname(src)
page = open(src, encoding="utf-8").read()
css = open(os.path.join(d, "../assets/review.css"), encoding="utf-8").read()
page = page.replace('<link rel="stylesheet" href="../assets/review.css">', f"<style>\n{css}</style>")

def data_uri(m):
    raw = open(os.path.join(d, m.group(1)), "rb").read()
    return f'src="data:image/jpeg;base64,{base64.b64encode(raw).decode()}"'
page = re.sub(r'src="(slides/[^"]+\.jpg)"', data_uri, page)
page = page.replace(' loading="lazy"', "")
os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
open(dst, "w", encoding="utf-8").write(page)
print(dst, round(len(page.encode()) / 1e6, 1), "MB")

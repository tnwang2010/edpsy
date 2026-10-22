#!/usr/bin/env python3
"""驗證指定 GitHub commit 的靜態預覽，再輸出可放入 PR 的連結。只用 Python 標準函式庫。"""
import argparse
import concurrent.futures
import hashlib
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, unquote, urljoin, urlsplit, urlunsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]


class Resources(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        for attr in ("src", "href"):
            value = attrs.get(attr, "")
            if value and not value.startswith("#") and not urlsplit(value).scheme and not urlsplit(value).netloc:
                self.links.add(value)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("commit", help="已推送至 GitHub 的完整 40 字元 commit SHA")
    parser.add_argument("--repository", default="tnwang2010/edpsy")
    parser.add_argument("--page", default="review/week02/index.html")
    parser.add_argument("--section", default="s4")
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.commit):
        parser.error("請提供完整的 commit SHA，確保預覽固定在本次修改。")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", args.repository):
        parser.error("repository 格式須為 owner/name。")
    page = (ROOT / args.page).resolve()
    if not page.is_relative_to(ROOT / "review") or not page.is_file():
        parser.error("page 須為 review/ 內已產生的 HTML 檔案。")

    # raw.githack 以正確的 Content-Type 提供 GitHub 檔案；固定 commit 可避免舊快取。
    base = f"https://rawcdn.githack.com/{args.repository}/{args.commit}/"
    files = {page}
    pending = [page]
    while pending:
        html = pending.pop()
        resources = Resources()
        resources.feed(html.read_text(encoding="utf-8"))
        for link in resources.links:
            resolved = urlsplit(urljoin(html.as_uri(), link))
            target = Path(unquote(resolved.path)).resolve()
            if not target.is_relative_to(ROOT / "review") or not target.is_file():
                raise RuntimeError(f"預覽連結未指向有效的課後複習檔案：{html.relative_to(ROOT)} → {link}")
            if target not in files:
                files.add(target)
                if target.suffix == ".html":
                    pending.append(target)

    def verify(path):
        url = urljoin(base, quote(path.relative_to(ROOT).as_posix()))
        request = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; EdpsyPreview/1.0)"})
        with urlopen(request, timeout=30) as response:
            data = response.read()
            mime = response.headers.get_content_type()
        expected = {".html": "text/html", ".css": "text/css", ".jpg": "image/jpeg"}.get(path.suffix)
        if expected and mime != expected:
            raise RuntimeError(f"預覽的檔案格式不符：{url}（{mime}）")
        if hashlib.sha256(data).digest() != hashlib.sha256(path.read_bytes()).digest():
            raise RuntimeError(f"預覽內容與本機產出不同：{url}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        list(pool.map(verify, sorted(files)))
    preview = urljoin(base, quote(page.relative_to(ROOT).as_posix()))
    preview = urlunsplit((*urlsplit(preview)[:4], args.section))
    print(f"預覽驗證成功：{len(files)} 個 HTML、樣式與圖片檔案均與本機產出相同。")
    print(preview)


if __name__ == "__main__":
    main()

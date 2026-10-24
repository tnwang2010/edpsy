#!/usr/bin/env python3
"""把 review-src/ 的各週內容產生成 GitHub Pages 的課後複習網頁（只用 Python 標準函式庫）。

用法（在儲存庫根目錄）：python3 review-src/tools/build.py
  週次清單：review-src/weeks.json（content 為 null 的週次在導覽欄顯示「尚未上線」）
  各週內容：review-src/weekNN/content.py；投影片圖：review-src/weekNN/slides/<key>.jpg
  輸出：review/ 整個資料夾重新產生（index.html、assets/、weekNN/），請勿手動修改 review/
"""
import hashlib, html, json, os, re, runpy, shutil, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from headings import MARK, mark  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # review-src/
OUT = os.path.join(os.path.dirname(ROOT), "review")
# version tag appended to the stylesheet URL, so browsers fetch the new CSS as soon as it changes
CSS_V = hashlib.md5(open(os.path.join(ROOT, "assets/review.css"), "rb").read()).hexdigest()[:8]


def inline(md):
    """**粗體** 與 ==螢光== → HTML；其餘字元跳脫。"""
    s = html.escape(md, quote=False)
    # 長英文字標成英文，讓手機窄欄可以加連字號斷字，避免兩端對齊時整行被拉開
    s = re.sub(r"(?<![A-Za-z])[A-Za-z][A-Za-z'’-]{6,}(?![A-Za-z])", r'<span lang="en">\g<0></span>', s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"==(.+?)==", r'<span class="mark">\1</span>', s)
    return s.replace("王孜𡩋", '<span class="name">王孜𡩋</span>')


def heading(md):
    """標題：在詞組之間放 <wbr>，讓標題只在詞與詞之間或標點處換行（見 headings.py）。"""
    return inline(mark(md)).replace(MARK, "<wbr>")


def toc_of(blocks):
    return next(b[1] for b in blocks if b[0] == "ol")  # the first ol is the table of contents


def outline(blocks):
    """[(h2 標題, [h3 標題…])…]，順序與內文的 s1、s1-1 編號一致。"""
    out = []
    for b in blocks:
        if b[0] == "h2": out.append((b[1], []))
        elif b[0] == "h3" and out: out[-1][1].append(b[1])
    return out


def sidebar(weeks, current):
    """左側導覽：每週一個可收折的區塊，已上線的週次列出編號大綱與小節。"""
    groups = []
    for w in weeks:
        wk, label = f"week{w['week']:02d}", f"第 {w['week']} 週"
        if not w.get("blocks"):
            groups.append(f'<div class="wk off"><span>{label}</span><span class="soon">尚未上線</span></div>')
            continue
        here = w["week"] == current
        base = "" if here else f"../{wk}/index.html"
        secs = []
        for i, (h2, h3s) in enumerate(outline(w["blocks"]), 1):
            subs = "".join(f'<li><a href="{base}#s{i}-{j}">{inline(t)}</a></li>' for j, t in enumerate(h3s, 1))
            secs.append(f'<li><a class="sec" href="{base}#s{i}"><span class="n">{i}</span><span class="t">{inline(h2)}</span></a>'
                        + (f'<ul class="subs">{subs}</ul>' if subs else "") + "</li>")
        groups.append(f'<details class="wk{" on" if here else ""}"{" open" if here else ""}>'
                      f'<summary>{label}｜{inline(w["topic"])}</summary><ol class="secs">{"".join(secs)}</ol></details>')
    return ('<nav class="side" aria-label="課程週次"><div class="side-box">'
            '<div class="side-head"><span class="side-title">各週大綱</span>'
            '<button class="side-toggle" type="button" aria-expanded="true" aria-controls="side-list">收合</button></div>'
            f'<div class="side-list" id="side-list">{"".join(groups)}</div></div></nav>')


def page(w, weeks, out):
    blocks, wk = w["blocks"], f"week{w['week']:02d}"
    os.makedirs(f"{out}/{wk}/slides", exist_ok=True)
    head = {b[0]: b[1] for b in blocks if b[0] in ("label", "title", "dek", "byline", "foot")}
    body, n, m, skip_toc = [], 0, 0, True
    for b in blocks:
        k = b[0]
        if k in ("label", "title", "dek", "byline", "foot", "toc_label"):
            continue
        if k == "ol" and skip_toc:
            skip_toc = False
            items = "".join(f'<li><a href="#s{i}">{inline(t)}</a></li>' for i, t in enumerate(b[1], 1))
            body.append(f'<nav class="toc" aria-label="本文目錄"><p>本文目錄</p><ol>{items}</ol></nav>')
        elif k == "p":
            body.append(f"<p>{inline(b[1])}</p>")
        elif k == "h2":
            n += 1; m = 0; body.append(f'<h2 id="s{n}">{heading(b[1])}</h2>')
        elif k == "h2plain":
            body.append(f'<h2 class="plain">{heading(b[1])}</h2>')
        elif k == "h3":
            m += 1; body.append(f'<h3 id="s{n}-{m}">{heading(b[1])}</h3>')
        elif k in ("ul", "ol"):
            cls = ' class="sources"' if body and body[-1].startswith('<h2 class="plain"') else ""
            body.append(f"<{k}{cls}>" + "".join(f"<li>{inline(t)}</li>" for t in b[1]) + f"</{k}>")
        elif k == "img":
            key, cap = b[1], b[2]
            shutil.copyfile(f"{ROOT}/{wk}/slides/{key}.jpg", f"{out}/{wk}/slides/{key}.jpg")
            body.append(f'<figure class="slide"><img src="slides/{key}.jpg" alt="投影片：{html.escape(cap)}" '
                        f'width="1600" height="900" loading="lazy"><figcaption>{inline(cap)}</figcaption></figure>')
        elif k == "note":
            lines = "".join(f"<p>{inline(t)}</p>" for t in b[2])
            body.append(f'<aside class="note"><span class="t">{inline(b[1])}</span>{lines}</aside>')
        elif k == "table":
            rows = b[1]
            th = "".join(f"<th>{inline(c)}</th>" for c in rows[0])
            trs = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in rows[1:])
            body.append(f'<div class="tbl"><table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>')

    byline = "".join(f"<span>{inline(x)}</span>" for x in head["byline"].split("｜"))
    # 導言與作者資訊依 content.py 裡的先後順序排列
    intro = "\n    ".join(f'<p class="dek">{inline(b[1])}</p>' if b[0] == "dek" else f'<p class="byline">{byline}</p>'
                          for b in blocks if b[0] in ("dek", "byline"))
    foot = inline(head["foot"]).replace(
        "「牛刀小試」", '「<a href="https://sites.google.com/view/tn-edpsy/quiz" target="_blank" rel="noopener">牛刀小試</a>」')
    doc = f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{html.escape(head["title"])}｜{html.escape(head["label"])}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700&family=Noto+Serif+TC:wght@700&display=swap">
<link rel="stylesheet" href="../assets/review.css?v={CSS_V}">
</head>
<body id="top">
<div class="layout">
{sidebar(weeks, w["week"])}
<article class="post" data-week="{w['week']}">
  <header class="post-head">
    <p class="tag"><a class="crumb" href="../index.html">課後複習首頁</a><span class="sep" aria-hidden="true">›</span>{inline(head["label"])}</p>
    <h1>{heading(head["title"])}</h1>
    {intro}
  </header>
  <div class="body">
    {chr(10).join("    " + x for x in body).strip()}
  </div>
  <footer class="post-foot"><p>{foot}</p></footer>
</article>
</div>
<script>
/* sidebar: fold/unfold (closed by default on narrow screens, remembered per reader) and highlight the section being read */
(function(){{
  var layout=document.querySelector('.layout'), btn=document.querySelector('.side-toggle'), mq=matchMedia('(max-width:1023px)');
  function set(folded){{ layout.classList.toggle('folded',folded); btn.setAttribute('aria-expanded',String(!folded)); btn.textContent=folded?'展開':'收合'; }}
  var saved=null; try{{ saved=localStorage.getItem('review-side'); }}catch(e){{}}
  set(mq.matches || saved==='folded');
  btn.addEventListener('click',function(){{
    var folded=!layout.classList.contains('folded'); set(folded);
    if(!mq.matches){{ try{{ localStorage.setItem('review-side',folded?'folded':'open'); }}catch(e){{}} }}
  }});
  document.querySelector('.side-list').addEventListener('click',function(e){{ if(mq.matches&&e.target.closest('a')) set(true); }});
  var heads=[].slice.call(document.querySelectorAll('.body h2[id], .body h3[id]'));
  var cur=document.querySelector('.wk.on');
  function spy(){{
    if(!cur) return;
    var id=null;
    for(var i=0;i<heads.length;i++){{ if(heads[i].getBoundingClientRect().top<140) id=heads[i].id; else break; }}
    var sec=id?id.split('-')[0]:null;
    [].forEach.call(cur.querySelectorAll('.secs>li'),function(li){{ li.classList.toggle('active',li.querySelector('.sec').getAttribute('href')==='#'+sec); }});
    [].forEach.call(cur.querySelectorAll('.subs a'),function(a){{ a.classList.toggle('active',a.getAttribute('href')==='#'+id); }});
  }}
  var t=null; addEventListener('scroll',function(){{ if(!t) t=requestAnimationFrame(function(){{ t=null; spy(); }}); }},{{passive:true}});
  spy();
}})();
</script>
</body>
</html>
"""
    open(f"{out}/{wk}/index.html", "w", encoding="utf-8").write(doc)
    print(f"{out}/{wk}/index.html", n, "sections")


def home(weeks, out):
    """review/index.html：各週卡片（日期、主題、各節大綱），未上線的週次顯示為預告。"""
    cards, soon = [], []
    for w in weeks:
        label = f"第 {w['week']} 週"
        if not w["blocks"]:
            soon.append(f'<div class="wcard off"><span class="wnum">{label}</span><span class="wsoon">尚未上線</span></div>')
            continue
        h = {b[0]: b[1] for b in w["blocks"] if b[0] in ("title", "byline")}
        wk = f"week{w['week']:02d}"
        date = re.search(r"(\d{4})/(\d{2})/(\d{2})", h["byline"])
        when = f'<span class="wdate">{int(date[2])}/{int(date[3])} 上課</span>' if date else ""
        heads = outline(w["blocks"])
        secs = "".join(f"<li>{inline(t)}</li>" for t, _ in heads)
        cards.append(f'<a class="wcard" href="{wk}/index.html">'
                     f'<div class="wbody"><div class="wmeta"><span class="wnum">{label}</span>{when}</div>'
                     f'<h2>{inline(w["topic"])}</h2><p class="wtitle">{inline(h["title"])}</p>'
                     f'<ol class="wsecs" style="--rows:{(len(heads) + 1) // 2}">{secs}</ol><span class="wgo">開始閱讀 →</span></div></a>')
    doc = f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>課後複習｜教育心理學</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700&family=Noto+Serif+TC:wght@700&display=swap">
<link rel="stylesheet" href="assets/review.css?v={CSS_V}">
</head>
<body>
<main class="home">
  <header class="home-head">
    <p class="tag">115學士後教育學分班｜教育心理學</p>
    <h1>課後複習</h1>
    <p class="intro">依<span class="name">王孜𡩋</span>老師每週課堂內容與投影片整理，適合缺課或想複習的同學閱讀。點選下方的週次進入；進入後可用「各週大綱」跳到任一節。</p>
  </header>
  <div class="wlist">{"".join(cards)}</div>
  {f'<div class="wsoon-row">{"".join(soon)}</div>' if soon else ""}
</main>
</body>
</html>
"""
    open(f"{out}/index.html", "w", encoding="utf-8").write(doc)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else OUT
    weeks = json.load(open(f"{ROOT}/weeks.json", encoding="utf-8"))
    for w in weeks:
        w["blocks"] = runpy.run_path(f"{ROOT}/{w['content']}")["BLOCKS"] if w.get("content") else None
    shutil.rmtree(out, ignore_errors=True)  # review/ is fully generated
    os.makedirs(f"{out}/assets")
    shutil.copyfile(f"{ROOT}/assets/review.css", f"{out}/assets/review.css")
    for w in weeks:
        if w["blocks"]:
            page(w, weeks, out)
    home(weeks, out)


if __name__ == "__main__":
    main()

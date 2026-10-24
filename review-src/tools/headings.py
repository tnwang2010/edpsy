"""標題的換行點：用 BudouX 繁中模型把標題切成詞組，在詞組之間放換行點。
搭配 CSS 的 word-break: keep-all，標題只會在詞組之間或標點處換行，不會把詞拆開。"""
import re

from budoux.parser import load_zh_hant

_PARSER = load_zh_hant()
HAN = "一-鿿\U00020000-\U0002ffff"
PUNCT = "（「『〈《【）」』〉》】，。、：；？！"
OPEN, CLOSE = set("（「『〈《【"), set("）」』〉》】，。、：；？！")
RIGHT = set("與和或及並而從到在給依對以就把被將一二三四五六七八九十兩幾每個種項期段位")  # 單獨一個字時，附在後一個詞前面
MARK = "\ue000"  # 換行點的暫代字元，產生 HTML 時換成 <wbr>
# 模型偶爾會切錯的詞，列在這裡就不會被拆開；之後發現新的錯切，加進來即可
KEEP = ["古希臘", "時機", "他律", "自律", "皮亞傑", "維高斯基", "心理學", "學習風格", "心理社會", "道德發展",
        "獨立自主", "羞愧懷疑", "主動探索", "勤奮努力", "自貶自卑", "自我認同", "角色混淆",
        "友愛親密", "孤獨疏離", "積極生產", "自我頹廢", "完美無憾", "悲觀絕望",
        "人本主義", "建構主義", "行為主義", "晚期經驗", "更多選擇", "文化觀點"]
NBSP = "\u00a0"


def _core(s):
    return re.sub(f"[^{HAN}]", "", s)


def _units(chunks):
    """BudouX 常切出單一個字；連接詞、數字、量詞併到後一個詞，其他單字（的、了…）併到前一個詞。"""
    out, carry = [], ""
    for c in chunks:
        core = _core(c)
        if len(core) <= 1 and (core in RIGHT or not out):
            carry += c
        elif len(core) <= 1:
            out[-1] += carry + c; carry = ""
        else:
            out.append(carry + c); carry = ""
    if carry:
        if out: out[-1] += carry
        else: out.append(carry)
    return out


def mark(text):
    """在中文詞組之間插入 MARK；英文、數字與標點前後不另加換行點。"""
    parts = []
    for run in re.findall(f"[{HAN}{PUNCT}]+|[^{HAN}{PUNCT}]+", text):
        if not re.match(f"[{HAN}{PUNCT}]", run):
            parts.append(run); continue
        units = _units(_PARSER.parse(run))
        s = units[0]
        for u in units[1:]:  # 兩邊都至少兩個字才放換行點，避免把詞拆開
            ok = len(_core(s.split(MARK)[-1])) >= 2 and len(_core(u)) >= 2 and s[-1] not in OPEN and u[0] not in CLOSE
            s += (MARK if ok else "") + u
        parts.append(s)
    s = "".join(parts)
    for w in KEEP:
        s = re.sub((re.escape(MARK) + "?").join(map(re.escape, w)), w, s)
    s = re.sub(f"(?<=[{HAN}]){MARK}?（", MARK + "（", s)  # 括號前可以換行
    # 括號內不換行（例如「（1920 年代至 1950 年代）」），「A vs. B」不從 vs. 前後斷開
    s = re.sub(r"（[^（）]*）", lambda m: m.group(0).replace(MARK, "").replace(" ", NBSP), s)
    s = re.sub(r" vs\. ", NBSP + "vs." + NBSP, s)
    return s

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一問一答CSVの問題文・解説を整える。

- 問題文: 文脈のない断片（「〜を防止する」だけ等）に親設問の論点を付与
- 解説: 同じ設問から派生した5件を1グループとして○行と照合し、用語集定義で再作成
"""

from __future__ import annotations

import csv
import os
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_CSV = ROOT / "data" / "past_questions_marubatsu_all_explanations.csv"
GLOSSARY_CSV = ROOT / "data" / "glossary_terms.csv"
OCR_DIR = Path(os.environ.get("BOILER_OCR_DIR", ""))

FORBIDDEN_PATTERNS = [
    "選択肢",
    "元問題",
    "正答選択肢",
    "この記述は（",
    "次のうちどれか",
]

CATEGORY_TIPS = {
    "ボイラーの構造に関する知識": "構造分野では、装置名だけでなく、取付位置、扱う流体、どの異常を防ぐ部品かを結び付けて判断します。",
    "ボイラーの取扱いに関する知識": "取扱い分野では、操作の目的、実施する順序、異常時に危険を広げない理由をセットで確認します。",
    "燃料及び燃焼に関する知識": "燃焼分野では、空気量、通風、燃料性状、排ガス成分の因果関係を逆にしないことが判定の軸になります。",
    "関係法令": "法令分野では、義務の主体、対象となるボイラー、数値条件、期限や保存期間を分けて読むことが重要です。",
}

SPECIAL_TERMS = [
    "亜硫酸ナトリウム",
    "炭酸ナトリウム",
    "りん酸ナトリウム",
    "リン酸ナトリウム",
    "塩化ナトリウム",
    "ヒドラジン",
    "タンニン",
    "常用水位",
    "安全低水面",
    "最高水位",
    "最低水位",
    "温水出口温度",
    "専用の建物",
    "耐火構造物",
    "密閉された室",
    "一次空気",
    "二次空気",
    "油・ガスだき",
    "火格子",
    "流動層",
    "熱伝導",
    "熱貫流",
    "蒸発熱",
    "着火温度",
    "引火点",
    "顕熱",
    "潜熱",
    "酸素",
    "蒸気",
    "水素",
    "処理水量",
    "残留硬度",
    "臨界点",
    "貫流点",
    "飽和点",
    "煙管",
    "管板",
    "胴板",
    "溶接",
    "構造",
    "使用",
    "落成",
    "配管",
    "据付基礎",
]

JUDGEMENT_TAIL_RE = re.compile(r"^(?P<prefix>.*?)「(?P<inner>.+)」という記述は(?P<label>正しい|誤っている)。$")
DEVICE_HEAD_RE = re.compile(r"^(.{2,40}?)(は|が|には|では|も)(?=[^、。]{0,30}(?:である|ない|できる|される|という|もの|部分|装置|弁|計|方式|構造|作用|目的|理由|場合|とき))")
METHOD_HINT_RE = re.compile(r"(方法|手段|手順|場合|とき|作用|目的|理由|順序|組合せ|条件|記述|装置|弁|計|バーナ|ポンプ|ドラム|室|器|トラップ|予熱器|節炭器|エコノマイザ|分離器|調節器|コントローラ|火格子|流動層|据付|検査|届出|選任|変更|設置|使用|廃止|再|除去|防止|抑制|調整|調節|燃焼|給水|排水|点火|たき上|停止|異常|故障|損傷|腐食|すす|灰分|水分|層内|排ガス|NOx|脱硫|伝熱|循環|圧力|水位|蒸気|温水|燃料|空気|法令|ボイラー)")


def norm(text: str | None) -> str:
    text = (text or "").strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"(?<=[一-龥ぁ-んァ-ン]) (?=[一-龥ぁ-んァ-ン])", "", text)
    return text


def group_key(row_id: str) -> str:
    return "-".join(row_id.split("-")[:2])


def extract_quoted(question: str) -> str:
    m = re.search(r"「(.+)」", question)
    return norm(m.group(1) if m else question)


def split_items(text: str) -> list[str]:
    text = text.replace("，", "、")
    if "、" not in text and " " in text:
        text = "、".join(p for p in text.split(" ") if p)
    if "、" not in text:
        text = segment_known_terms(text)
    parts = [norm(p) for p in text.split("、")]
    return [p for p in parts if p]


def segment_known_terms(text: str) -> str:
    rest = norm(text)
    if not rest or "、" in rest:
        return rest
    m = re.match(r"^(水|蒸気)(最高|最低)(上|下)$", rest)
    if m:
        return "、".join(m.groups())
    m = re.match(r"^(0\.[0-9])([0-9]{2,3})$", rest)
    if m:
        return "、".join(m.groups())
    parts: list[str] = []
    terms = sorted(SPECIAL_TERMS, key=len, reverse=True)
    while rest:
        hit = next((term for term in terms if rest.startswith(term)), "")
        if hit:
            parts.append(hit)
            rest = rest[len(hit) :]
        else:
            return text
    return "、".join(parts)


def display_target(text: str) -> str:
    items = split_items(text)
    return "、".join(items) if len(items) > 1 else text


def load_ocr_contexts() -> dict[str, dict[int, str]]:
    contexts: dict[str, dict[int, str]] = {}
    if not OCR_DIR.is_dir():
        return contexts
    for path in OCR_DIR.glob("*_exa_ocr.txt"):
        exam = path.name.replace("_exa_ocr.txt", "")
        text = path.read_text(encoding="utf-8", errors="ignore")
        matches = list(re.finditer(r"(?:【問\s*(\d{1,2})[】）]|[1l]?問\s*(\d{1,2})[】）\s]+)", text))
        for i, match in enumerate(matches):
            qno = int(match.group(1) or match.group(2))
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            contexts.setdefault(exam, {})[qno] = text[match.start() : end]
    return contexts


def ocr_focus(block: str) -> str:
    if not block:
        return ""
    compact = norm(block)
    if "鋳鉄製温水ボイラー" in compact and "温水温度自動制御装置" in compact:
        return "鋳鉄製温水ボイラーの温水温度自動制御装置に関する法令上の数値"
    if "水面測定" in compact and "水位" in compact and "連絡管" in compact:
        return "鋼製ボイラーの水面測定装置に関する空欄A～C"
    if "単純軟化法" in compact and "残留硬度" in compact and "処理水量" in compact:
        return "単純軟化法の残留硬度と処理水量のグラフに関する語句"
    if "次の文中" in compact and "数字" in compact and ("語句の組合せ" in compact or "句の組合せ" in compact):
        return "文中の空欄に入る数字・語句"
    if "次の文中" in compact and "数値の組合せ" in compact:
        return "文中の空欄に入る数値"
    if "次の文中" in compact and ("語句の組合せ" in compact or "句の組合せ" in compact):
        return "文中の空欄に入る語句"
    text = re.sub(r"=== PAGE \d+ ===", "", block)
    text = re.sub(r"【問\s*\d+[】）]|問\s*\d+\s*", "", text, count=1)
    text = re.split(r"\n\s*[A-EＡ-Ｅ]\s*[：:．.]", text)[0]
    text = re.split(r"\n\s*[■ロ]?\s*[1-5１-５]\s*[．.]", text)[0]
    text = norm(text)
    text = re.sub(r"（\s*1\s*）\s*[～〜]\s*（\s*5\s*）のうちどれか。?", "", text)
    text = re.sub(r"次のうちどれか。?", "", text)
    text = re.sub(r"について、?", "について、", text)
    text = re.sub(r"として、?適切なもの.*", "として適切なもの", text)
    text = re.sub(r"として、?誤っているもの.*", "として誤っているもの", text)
    text = re.sub(r"の組合せは、?$", "", text)
    return text.rstrip("、。")


def parse_judgement_question(question: str) -> tuple[str, str, str] | None:
    m = JUDGEMENT_TAIL_RE.match(norm(question))
    if not m:
        return None
    return m.group("prefix").strip(), m.group("inner"), m.group("label")


def needs_context_prefix(inner: str, existing_prefix: str) -> bool:
    if existing_prefix:
        return False
    inner = norm(inner)
    if not inner:
        return False
    if re.match(r"^[^、。]{2,36}(は|が|には|では)", inner):
        return False
    if DEVICE_HEAD_RE.match(inner):
        return False
    if len(inner) >= 55 and re.search(r"(である|ない|できる|される|とい|こと|もので|部分|装置|とき|場合|方式|構造|範囲|効率)", inner):
        return False
    if re.search(
        r"(する|させる|下げる|上げる|防止|向上|低下|用いる|行う|設ける|採用|変更|移動|保存|記録|届出|検査|排出|供給|混合|除去|抑制|閉じ|開く|取り替|加減|停止|確認|配管|連絡|損傷|変形|折損|焼損|上昇|増加|減少|付着|混入|閉そく|不完全|選び|除く|設置|廃止|再び|再使用|選任)$",
        inner,
    ):
        return True
    if len(inner) < 50 and not re.search(r"(である|ない|できる|される)", inner):
        return True
    return False


def group_inners_and_labels(group_rows: list[dict[str, str]]) -> tuple[list[str], list[str], str]:
    inners: list[str] = []
    labels: list[str] = []
    category = ""
    for row in group_rows:
        category = category or norm(row.get("category"))
        parsed = parse_judgement_question(norm(row.get("question")))
        if not parsed:
            continue
        _, inner, label = parsed
        inners.append(inner)
        labels.append(label)
    return inners, labels, category


def infer_group_prefix(group_rows: list[dict[str, str]], block: str) -> str:
    focus = ocr_focus(block)
    if focus:
        return focus

    inners, labels, category = group_inners_and_labels(group_rows)
    if not inners:
        return ""

    joined = " ".join(inners)
    unique_labels = set(labels)

    if category == "関係法令":
        if any("伝熱面積" in x or "電気ボイラー" in x or "貫流ボイラー" in x for x in inners):
            return "第2種ボイラー技士を選任しなければならないボイラーとして"
        if any("変更を加えた" in x for x in inners):
            return "構造変更検査を要する場合として"
        if any("使用の廃止" in x or "再び使用" in x or "再使用" in x for x in inners):
            return "使用の廃止又は再使用の届出が必要な場合として"
        if any("設置の届出" in x or "設置しよう" in x for x in inners):
            return "ボイラーの設置届出が必要な場合として"
        if any("検査" in x for x in inners) and any("保存" in x for x in inners):
            return "検査関係書類の保存について"
        if any("作業主任者" in x or "選任" in x for x in inners):
            return "作業主任者の選任が必要な場合として"
        if any("ボイラー室" in x or "ボイラー設置場所" in x for x in inners):
            return "ボイラー室又は設置場所に関する規定として"
        if any("移動式" in x for x in inners):
            return "移動式ボイラーに関する規定として"
        if unique_labels == {"正しい"}:
            return "法令上の規定として正しいものは"

    keyword_focus = [
        (("低水位事故", "低水位"), "低水位燃焼防止装置の作用"),
        (("戻り油式", "プランジャ式", "ノズルチップ", "バーナの数"), "燃焼量の広い調節範囲を確保する方法"),
        (("たき始め", "点火後", "空気抜き弁", "圧力計の指針"), "ボイラーのたき始めの手順"),
        (("満水保存", "乾燥保存", "凍結"), "ボイラーの保存方法"),
        (("吹出し", "給水温度が低下", "給水内管", "水面計が閉そく"), "ボイラー水位が異常に上昇した原因"),
        (("主蒸気弁を急開", "燃焼量を下げ", "水質試験"), "ボイラー内圧力が異常に上昇したときの対処"),
        (("バイメタル", "電磁コイル", "弁座", "弁棒"), "安全弁が作動しない原因"),
        (("すすの付着", "酸消費量", "亜硫酸"), "ボイラー運転中の内部処理"),
        (("エコノマイザ", "空気予熱器", "節炭器"), "エコノマイザ又は空気予熱器の効果"),
        (("自然循環式水管", "強制循環式", "貫流ボイラー", "二胴形"), "水管ボイラーの形式"),
        (("温度調節器", "感温体", "シリコングリス"), "温度調節器の取付"),
        (("主蒸気弁", "減圧弁", "気水分離器", "蒸気トラップ", "伸縮継手"), "蒸気配管の附属装置"),
        (("比例動作", "積分動作", "微分動作"), "自動制御の動作"),
        (("流量計", "水面計", "二色水面計"), "計測器の原理"),
        (("流動層", "石灰石", "炉内脱硫"), "流動層燃焼装置の特徴"),
        (("NOx", "すす", "遊離炭素"), "燃焼生成物"),
        (("重油", "灯油", "LPG", "都市ガス", "発熱量"), "燃料の性質"),
        (("過剰空気", "完全燃焼", "すす及びダスト"), "低酸素燃焼の特徴"),
        (("灰分", "スラッジ", "残留炭素"), "固体燃料の性質"),
    ]
    for keys, phrase in keyword_focus:
        if any(any(k in inner for k in keys) for inner in inners):
            return phrase + "として"

    for inner in sorted(inners, key=len, reverse=True):
        m = DEVICE_HEAD_RE.match(inner)
        if m and len(m.group(1)) >= 3:
            head = m.group(1)
            if head not in {"次の", "以下の", "この", "その"}:
                return head + "に関する記述"

    if unique_labels == {"誤っている"}:
        return "次の記述のうち誤っているものとして"
    if unique_labels == {"正しい"}:
        return "次の記述のうち正しいものとして"
    return "次の記述として"


def apply_group_context_prefix(group_rows: list[dict[str, str]], prefix: str) -> int:
    if not prefix:
        return 0
    changed = 0
    prefix = prefix.rstrip("、。")
    for row in group_rows:
        question = norm(row.get("question"))
        parsed = parse_judgement_question(question)
        if not parsed:
            continue
        existing_prefix, inner, label = parsed
        if not needs_context_prefix(inner, existing_prefix):
            continue
        row["question"] = f"{prefix}、「{inner}」という記述は{label}。"
        changed += 1
    return changed


def ocr_letter_map(block: str) -> dict[str, str]:
    if not block:
        return {}
    mapping: dict[str, str] = {}
    pattern = re.compile(
        r"([A-EＡ-Ｅ])\s*[：:．.]\s*(.*?)(?=\n\s*[A-EＡ-Ｅ]\s*[：:．.]|\n\s*[1-5１-５]\s*[．.]|$)",
        re.S,
    )
    for letter, value in pattern.findall(block):
        key = chr(ord("A") + "ＡＢＣＤＥ".find(letter)) if letter in "ＡＢＣＤＥ" else letter
        mapping[key] = norm(value).rstrip("。")
    return mapping


def ocr_choices(block: str) -> dict[int, str]:
    choices: dict[int, list[str]] = {}
    current: int | None = None
    for raw_line in block.splitlines()[1:]:
        line = norm(raw_line)
        if not line or line.startswith("Copyright") or "このデータは" in line or "再配布" in line or "株式会社" in line:
            continue
        if line.startswith("===") or line.startswith("No."):
            current = None
            continue
        if current and re.match(r"^[0-9]\.[0-9]+$", line):
            choices[current].append(line)
            continue
        m = re.match(r"^[■ロ□\s]*([1-5１-５])\s*[．.]\s*(.*)$", line)
        if m:
            digit = m.group(1)
            current = int("１２３４５".find(digit) + 1) if digit in "１２３４５" else int(digit)
            choices[current] = []
            if m.group(2):
                choices[current].append(m.group(2))
            continue
        if current and not re.match(r"^[A-EＡ-Ｅ]\s*[：:．.]|^A$|^B$|^C$|^D$|^E$", line):
            choices[current].append(line)

    normalized: dict[int, str] = {}
    for key, parts in choices.items():
        text = norm(" ".join(parts))
        text = text.replace("頭熱", "顕熱").replace("貴流", "貫流").replace("制 ", "制御")
        text = segment_known_terms(text)
        normalized[key] = display_target(text)
    return normalized


def expand_arrow_target(target: str, block: str) -> str:
    if "→" not in target:
        return target
    mapping = ocr_letter_map(block)
    if not mapping:
        return target
    letters = re.findall(r"[A-EＡ-Ｅ]", target)
    expanded: list[str] = []
    for letter in letters:
        key = chr(ord("A") + "ＡＢＣＤＥ".find(letter)) if letter in "ＡＢＣＤＥ" else letter
        if key not in mapping:
            return target
        expanded.append(mapping[key])
    return "、".join(expanded)


def expand_letter_combo_target(target: str, block: str) -> str:
    if not re.fullmatch(r"[A-EＡ-Ｅ](?:\s*[,、]\s*[A-EＡ-Ｅ])*", target):
        return target
    mapping = ocr_letter_map(block)
    if not mapping:
        return target
    letters = re.findall(r"[A-EＡ-Ｅ]", target)
    expanded: list[str] = []
    for letter in letters:
        key = chr(ord("A") + "ＡＢＣＤＥ".find(letter)) if letter in "ＡＢＣＤＥ" else letter
        if key not in mapping:
            return target
        expanded.append(mapping[key])
    return "、".join(expanded)


def rewrite_question(row: dict[str, str], ocr_contexts: dict[str, dict[int, str]]) -> None:
    question = norm(row["question"])
    question = question.replace("爺炭器管", "節炭器管").replace("最彽", "最低")
    target = extract_quoted(question)
    clean_target = re.split(r"、===|、■|、株式会社|、（燃料|===|Copyright|株式会社", target)[0]
    if clean_target != target:
        question = question.replace(f"「{target}」", f"「{clean_target}」")
        target = clean_target
    exam, qno, choice_no = row["id"].split("-")
    block = ocr_contexts.get(exam, {}).get(int(qno), "")
    choices = ocr_choices(block)
    if int(choice_no) in choices:
        suspicious = (
            "1～5のうちどれか" in question
            or bool(re.search(r"\b[A-E](?:\s|として)|A\s+B|P点", question))
            or bool(re.search(r"^[A-EＡ-Ｅ\s→]+$", target))
            or bool(re.search(r"爺|巳|囗|讐|莨|廴|弁水|0\.[0-9]{3,}|^[0-9.]+[^、]+$", target))
            or ("組合せ" in question and "、" not in target and len(target) <= 14)
        )
        if suspicious:
            new_target_from_ocr = choices[int(choice_no)]
            new_target_from_ocr = re.split(r"、===|、■|、株式会社|、（燃料|===|Copyright|株式会社", new_target_from_ocr)[0]
            question = question.replace(f"「{target}」", f"「{new_target_from_ocr}」")
            target = new_target_from_ocr

    new_target = expand_arrow_target(target, block)
    letter_combo_target = expand_letter_combo_target(new_target, block)
    if letter_combo_target != new_target:
        new_target = letter_combo_target
    if new_target != target:
        question = question.replace(f"「{target}」", f"「{new_target}」")
        focus = ocr_focus(block)
        if focus and re.search(r"」の順序は正しい。$", question):
            question = re.sub(r"」の順序は正しい。$", f"」の順序は、{focus}として正しい。", question)
        target = new_target

    m = re.match(r"^「(.+)」の組合せは(正しい|適切である)。$", question)
    if m:
        focus = ocr_focus(block)
        shown = display_target(m.group(1))
        if focus:
            question = f"「{shown}」は、{focus}として正しい組合せである。"
        else:
            question = f"「{shown}」は、問われている条件に合う正しい組合せである。"

    m = re.match(r"^「(.+)」は、(.+正しい組合せである。)$", question)
    if m:
        shown = display_target(m.group(1))
        focus = ocr_focus(block)
        needs_focus = bool(re.search(r"[A-EＡ-Ｅ]|[1１]\s*[～〜]\s*5のうちどれか|次の文中", question))
        if focus and needs_focus:
            question = f"「{shown}」は、{focus}として正しい組合せである。"
        else:
            question = f"「{shown}」は、{m.group(2)}"

    m = re.match(r"^「(.+)」\s+[A-E](?:\s+[A-E]|\s+口|\s+P点)*\s*として正しい組合せである。$", question)
    if m:
        shown = display_target(m.group(1))
        focus = ocr_focus(block) or "問われている空欄"
        question = f"「{shown}」は、{focus}として正しい組合せである。"

    m = re.match(r"^「(.+)」という記述は正しい。$", question)
    if m and re.match(r"^(0\.[0-9])([0-9]{2,3})$", m.group(1)):
        focus = ocr_focus(block)
        shown = display_target(m.group(1))
        focus = focus or "問われている法令上の数値"
        question = f"「{shown}」は、{focus}として正しい組合せである。"

    question = question.replace("としてに照らして", "として")
    question = question.replace("。(」", "」")
    question = re.sub(r"。+$", "。", question)
    row["question"] = question


def load_glossary() -> tuple[list[str], dict[str, dict[str, str]]]:
    term_info: dict[str, dict[str, str]] = {}
    aliases: set[str] = set()
    with GLOSSARY_CSV.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            term = norm(row.get("term"))
            if not term:
                continue
            term_info[term] = row
            aliases.add(term)
    return sorted(aliases, key=len, reverse=True), term_info


def first_sentence(text: str) -> str:
    text = norm(text)
    if not text:
        return ""
    parts = re.split(r"(?<=。)", text)
    return norm(parts[0])


def glossary_points(question: str, correct_target: str, aliases: list[str], term_info: dict[str, dict[str, str]]) -> tuple[list[str], list[str]]:
    haystack = question + " " + correct_target
    found: list[str] = []
    for alias in aliases:
        if alias in haystack and alias not in found:
            found.append(alias)
        if len(found) >= 2:
            break

    points: list[str] = []
    for alias in found:
        row = term_info[alias]
        base = first_sentence(row.get("definition")) or first_sentence(row.get("short_def"))
        if base and "2級ボイラー技士試験" not in base:
            points.append(f"{alias}は、{base}")
    return found, points


def special_points(question: str, correct_target: str) -> list[str]:
    text = question + " " + correct_target
    points: list[str] = []
    if all(word in text for word in ("圧力計", "ゲージ圧力", "絶対圧力")):
        points.append("一般の圧力計が示すのはゲージ圧力で、絶対圧力はゲージ圧力に大気圧を加えた圧力です")
    if "セルシウス" in text and "絶対温度" in text:
        points.append("絶対温度Tはセルシウス温度tに約273を加えて表すため、t＝T＋273のように逆にした式は誤りです")
    if "シリコングリス" in text and "感温体" in text:
        points.append("保護管を用いる感温体では熱の伝わりをよくするため、保護管内にシリコングリスを入れる扱いです")
    if "比例動作" in text and "偏差が変化する速度" in text:
        points.append("偏差が変化する速度に応じるのは微分動作であり、比例動作は偏差の大きさに比例して操作量を変える動作です")
    if "亜硫酸ナトリウム" in text or "タンニン" in text or "炭酸ナトリウム" in text:
        if "脱酸素" in text or "薬剤" in text or "組合せ" in text:
            points.append("脱酸素剤として扱う代表例は亜硫酸ナトリウム、タンニン、ヒドラジンで、炭酸ナトリウムやりん酸ナトリウムは主に軟化・スケール防止側の薬剤として区別します")
    if "グランドパッキン" in text and "水漏れがない" in text:
        points.append("グランドパッキンシール式では、運転中に少量の水が連続して滴下する程度に調整するため、水漏れゼロを目標にしません")
    if "吐出し弁を全開" in text and "起動" in text:
        points.append("遠心ポンプの起動では電動機の過負荷を避けるため、一般に吐出し弁を閉じた状態から始めます")
    if "空気抜" in text and "真空" in text:
        points.append("停止後の排水では、内部が負圧にならないよう空気抜き弁から空気を入れる点が重要です")
    return points[:2]


def question_kind(question: str) -> str:
    if "組合せ" in question or "組み合わせ" in question:
        return "combo"
    if "順序" in question:
        return "order"
    if "記述は誤っている" in question:
        return "wrong_statement"
    if "記述は正しい" in question:
        return "right_statement"
    if "記述は適切である" in question:
        return "appropriate"
    return "statement"


def base_judgement(row: dict[str, str], kind: str) -> str:
    answer = norm(row["answer"])
    if kind == "combo":
        if answer == "○":
            return "判定は○です。示された組合せは、問われている条件に合うものを過不足なく挙げています。"
        return "判定は×です。示された組合せは、問われている条件に合うものを過不足なく挙げていません。"
    if kind == "order":
        if answer == "○":
            return "判定は○です。示された順序は、操作の目的と安全上の優先順位に沿っています。"
        return "判定は×です。示された順序は、操作の目的と安全上の優先順位に沿っていません。"
    if kind == "wrong_statement":
        if answer == "○":
            return "判定は○です。提示文には誤りがあるため、「誤っている」という判断が成り立ちます。"
        return "判定は×です。提示文は誤りとして扱う内容ではないため、「誤っている」とは判断しません。"
    if answer == "○":
        return "判定は○です。提示文は、問われている条件に合う正しい内容です。"
    return "判定は×です。提示文は、問われている条件に合う正しい内容とはいえません。"


def diff_sentence(target: str, correct_target: str, kind: str) -> str:
    target_display = display_target(target)
    correct_display = display_target(correct_target)
    if target == correct_target:
        if kind == "combo":
            return "この組合せを基準に、含めるものと除外するものの境目を押さえてください。"
        if kind == "order":
            return "この順序を基準に、先に止める操作、換気、弁の操作、水位維持の位置づけを整理してください。"
        return "この内容を基準に、似た語句や数値が入れ替わった文と区別してください。"

    if kind in {"combo", "order"}:
        current_items = split_items(target)
        correct_items = split_items(correct_target)
        missing = [x for x in correct_items if x not in current_items]
        extra = [x for x in current_items if x not in correct_items]
        parts = [f"同じ設問で○になる内容は「{correct_display}」です。"]
        if missing:
            parts.append("不足している内容は「" + "、".join(missing) + "」です。")
        if extra:
            parts.append("余分に入っている内容は「" + "、".join(extra) + "」です。")
        if not missing and not extra and current_items and correct_items:
            parts.append("要素が近くても、並べる順序が違うと操作手順としては誤りになります。")
        return "".join(parts)

    return f"同じ設問で○になる内容は「{correct_display}」です。提示文とこの内容を比べ、語句、数値、対象、因果関係のどこが違うかを確認します。"


def build_explanation(
    row: dict[str, str],
    correct_row: dict[str, str],
    aliases: list[str],
    term_info: dict[str, dict[str, str]],
) -> tuple[str, list[str]]:
    question = norm(row["question"])
    target = extract_quoted(question)
    correct_target = extract_quoted(correct_row["question"])
    kind = question_kind(question)
    found_terms, points = glossary_points(question, correct_target, aliases, term_info)
    points = special_points(question, correct_target) + points

    sentences = [
        base_judgement(row, kind),
        diff_sentence(target, correct_target, kind),
    ]

    if points:
        joined = "。また、".join(p.rstrip("。") for p in points[:2])
        sentences.append("確認ポイントは、" + joined + "。")
    else:
        sentences.append(CATEGORY_TIPS.get(row["category"], "設問の対象、条件、理由を分けて確認すると判断しやすくなります。"))

    explanation = re.sub(r"。。+", "。", "".join(sentences))
    return explanation, found_terms


def audit(rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[group_key(row["id"])].append(row)

    for key, group in groups.items():
        if len(group) != 5:
            errors.append(f"{key}: 派生行が5件ではありません")
        positives = [r for r in group if norm(r["answer"]) == "○"]
        if len(positives) != 1:
            errors.append(f"{key}: ○の件数が1件ではありません")

    for row in rows:
        for col in ("question", "explanation"):
            text = row.get(col, "")
            for forbidden in FORBIDDEN_PATTERNS:
                if forbidden in text:
                    errors.append(f"{row['id']}: {col} に禁止語句 {forbidden!r} が残っています")
        if not norm(row.get("explanation")):
            errors.append(f"{row['id']}: explanation が空です")
        if not row["explanation"].startswith(f"判定は{row['answer']}です。"):
            errors.append(f"{row['id']}: explanation 冒頭の判定が answer と一致しません")
    return errors


def main() -> int:
    aliases, term_info = load_glossary()
    ocr_contexts = load_ocr_contexts()
    with DATA_CSV.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        rows = list(reader)

    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        rewrite_question(row, ocr_contexts)
        groups[group_key(row["id"])].append(row)

    context_changed = 0
    for key, group in groups.items():
        exam, qno, _ = key.split("-", 2) if key.count("-") >= 2 else (key, "0", "0")
        block = ocr_contexts.get(exam, {}).get(int(qno), "")
        prefix = infer_group_prefix(group, block)
        context_changed += apply_group_context_prefix(group, prefix)

    term_counter: Counter[str] = Counter()
    no_term = 0
    for group in groups.values():
        correct = [r for r in group if norm(r["answer"]) == "○"]
        if len(correct) != 1:
            continue
        correct_row = correct[0]
        for row in group:
            explanation, found_terms = build_explanation(row, correct_row, aliases, term_info)
            row["explanation"] = explanation
            row["note"] = "正答キー照合済み・解説再作成"
            if found_terms:
                term_counter.update(found_terms)
            else:
                no_term += 1

    errors = audit(rows)
    if errors:
        for error in errors[:50]:
            print(error)
        print(f"audit errors: {len(errors)}")
        return 1

    with DATA_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"rewrote rows: {len(rows)}")
    print(f"groups checked: {len(groups)}")
    print(f"questions with context prefix added: {context_changed}")
    print(f"rows with glossary/source terms: {len(rows) - no_term}")
    print(f"rows using category-level reason: {no_term}")
    print("top matched terms:", ", ".join(f"{term}:{count}" for term, count in term_counter.most_common(10)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

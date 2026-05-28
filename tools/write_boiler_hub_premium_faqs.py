# -*- coding: utf-8 -*-
"""2級ボイラー技士 知識ハブ：比較スラッグ向けプレミアムFAQ."""

from tools.write_boiler_hub_s30 import _OFFICIAL

SLUG_TITLES = {
    "kantai-empkan": "貫流ボイラーと炉筒煙管ボイラーの違い",
    "suikan-empkan": "水管ボイラーと煙管ボイラーの違い",
    "hojo-kanki-jouki": "飽和蒸気と過熱蒸気の違い",
    "shizen-kyosei-junkan": "自然循環と強制循環の違い",
    "anzen-nigasiben": "安全弁と逃がし弁の違い",
    "kansen-teibu-buro": "連続ブローと底部ブローの違い",
    "kanzen-fukanzen-nensho": "完全燃焼と不完全燃焼の違い",
    "rouho-boiler-kisoku": "労働安全衛生法とボイラー規則の違い",
    "jitsuryoku-hisshi": "実力試験と筆記試験の違い",
    "kanki-kyuki-nensho": "関気燃焼と給気燃焼の違い",
}


def _answers(title: str) -> list[tuple[str, str]]:
    return [
        (
            f"{title}は何から押さえるべきですか？",
            "最初に『主語・目的・適用場面』の3点を固定してください。2級ボイラー技士では似た用語を入れ替えた肢が多く、"
            "定義だけでなく運転手順や法令上の位置づけまで一緒に確認すると誤答率が下がります。比較表を声に出して説明できる状態を目標にします。",
        ),
        (
            "本番で迷ったときの判断手順は？",
            "問題文の条件（圧力・水位・法令・手順）を先に抽出し、次に比較軸へ当てはめます。選択肢を先に読むより、"
            "判断軸を固定してから照合する方が引っかけを回避しやすく、時間配分も安定します。過去問では同型の誤答理由を必ず記録してください。",
        ),
        (
            "学習を定着させる復習法は？",
            "S30で定義を確認し、S31で運転・法令の実務軸を追加して往復してください。誤答した問題は『条件読み落とし・数値混同・手順逆転』の"
            "どれかに分類して再演習すると、短期間で再発を抑えられます。復習時は必ず関連用語と比較表をセットで参照します。",
        ),
        (
            "公式情報はどのタイミングで確認すべきですか？",
            "受験直前だけでなく、週次の学習サイクル末尾で更新有無を確認するのが安全です。法令・検査・試験制度に関わる数値は"
            "改正や運用変更で差が出るため、要項・条文・試験実施団体の案内を一次情報として照合してください。"
            + _OFFICIAL,
        ),
    ]


PREMIUM_FAQS: dict[str, list[tuple[str, str]]] = {
    slug: _answers(title) for slug, title in SLUG_TITLES.items()
}


def apply_premium_faqs(row: dict[str, str]) -> dict[str, str]:
    slug = row.get("slug", "")
    if slug not in PREMIUM_FAQS:
        return row
    row = dict(row)
    for i, (q, a) in enumerate(PREMIUM_FAQS[slug], start=1):
        row[f"faq_{i}_question"] = q
        row[f"faq_{i}_answer"] = a
    return row


def apply_all(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [apply_premium_faqs(r) for r in rows]

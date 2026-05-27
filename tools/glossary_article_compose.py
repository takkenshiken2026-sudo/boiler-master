# -*- coding: utf-8 -*-
"""用語詳細記事の本文・要点・覚え方・FAQを組み立てる（平易な文体・具体例付き）。"""

from __future__ import annotations

from tools.site_config import exam_name

FIELD_LABEL = {
    "ボイラーの構造に関する知識": "構造",
    "ボイラーの取扱いに関する知識": "取扱い",
    "燃料及び燃焼に関する知識": "燃料・燃焼",
    "関係法令": "法令",
}


def pick(term: str, options: list[str]) -> str:
    if not options:
        return ""
    return options[hash(term) % len(options)]


def merge_defs(short: str, detail: str) -> str:
    s = short.rstrip("。").strip()
    d = detail.rstrip("。").strip()
    if not d:
        return s
    if d == s or d.startswith(s):
        return d
    if s and s not in d:
        return f"{s}。{d}"
    return d


def related_phrase(term: str, related: list[str], max_n: int = 3) -> str:
    names = [r for r in related if r != term][:max_n]
    if not names:
        return "同分野の用語索引"
    if len(names) == 1:
        return f"「{names[0]}」"
    return f"「{'」「'.join(names)}」"


def concrete_example(
    term: str, kind: str, category: str, related: list[str], merged: str
) -> str:
    rel = related[0] if related else ""
    field = FIELD_LABEL.get(category, "本分野")
    if kind == "law":
        if "検査" in term:
            return pick(
                term,
                [
                    f"たとえば、休止後にボイラーを再び使う前に受ける手続きが「{term}」に関係します。"
                    f"「いつ・誰が・何を確認するか」をセットで思い出せるかが、選択肢の正誤を分けます。",
                    f"たとえば、新設・移設・改造のあとに必要になる手続きと、「{term}」の違いが問われることがあります。"
                    f"名称が似た検査用語と混同しないよう、目的と時期を並べて覚えましょう。",
                ],
            )
        if "届" in term or "申請" in term:
            return (
                f"たとえば、設置者が所定の書類を提出しなければならない場面が「{term}」のイメージです。"
                f"「誰が・いつまでに・何を」提出するかを、条文の趣旨どおりに選べるようにしておきましょう。"
            )
        if "主任者" in term or "作業者" in term:
            return (
                f"たとえば、一定規模以上のボイラー設置場所で、誰が運転の指揮を取るかが「{term}」と結びつきます。"
                f"資格・選任・職務の範囲を、似た用語と取り違えないことが重要です。"
            )
        return (
            f"たとえば、試験では「{merged[:36]}」という一文の主語や期限だけが入れ替わった選択肢が出ます。"
            f"数字と主体（設置者・作業者・検査機関）をメモに書き写して確認する習慣が有効です。"
        )
    if kind == "operation":
        if any(k in term for k in ("水位", "だき", "ブロー", "吹出")):
            return (
                f"たとえば、運転中に水位計の表示が急に下がったとき、最初に取るべき対応と「{term}」の関係が問われます。"
                f"「燃焼を続ける」「大量給水する」など、危険な手順が正解になりにくい点に注意してください。"
            )
        if "点火" in term or "たき" in term or "パージ" in term:
            return (
                f"たとえば、冷えたボイラーを運転開始するとき、点火の前後で行う手順の順番が「{term}」と結びつきます。"
                f"手順を前後逆にした選択肢は、安全上の理由から誤りになりやすいです。"
            )
        return (
            f"たとえば、日常点検や異常時の記録で「{term}」がいつ・なぜ必要かを説明できると、現場の理解にもつながります。"
            f"{f'「{rel}」と' if rel else ''}前後の作業をセットで思い出せるようにしましょう。"
        )
    if kind == "combustion":
        return (
            f"たとえば、排ガス分析で数値が変化したとき、「{term}」が増えると効率や安全にどう影響するかが問われます。"
            f"「空気を増やすと〇〇」「燃料を減らすと△△」の方向を、逆にしないことが大切です。"
        )
    if "弁" in term:
        return (
            f"たとえば、圧力が上がりすぎたときに自動で開く装置か、運転員が手で開閉する装置かで、"
            f"「{term}」の役割が決まります。系統図上の位置を思い浮かべながら覚えると整理しやすいです。"
        )
    if kind == "boiler_type":
        return (
            f"たとえば、水量の多い少ない、起動までの時間、水質管理の厳しさなどが、"
            f"「{term}」を他のボイラー形式と比べるときのポイントになります。"
        )
    if kind == "equipment":
        return (
            f"たとえば、運転室で計器の指示が変わったとき、「{term}」の異常かどうかを判断し、"
            f"次に操作する弁や装置を選ぶ場面で使われる知識です。"
        )
    opts = [
        (
            f"たとえば、{field}分野の過去問では定義文の一部だけが別の語に置き換えられた選択肢が出ます。"
            f"条件の追加・削除がないかを、一文ずつ確認する癖をつけましょう。"
        ),
    ]
    if rel:
        opts.append(
            f"たとえば、「{rel}」と並べて、「{term}」だけが説明している範囲を"
            f"一言で言えるようにすると、似た用語との違いがはっきりします。"
        )
    return pick(term, opts)


def compose_key_summary(
    term: str, short: str, detail: str, kind: str, category: str, related: list[str]
) -> str:
    core = merge_defs(short, detail).rstrip("。")
    example = concrete_example(term, kind, category, related, core)
    lead = pick(
        term,
        [
            f"「{term}」は、{core}。",
            f"まず覚えるのは、{core}、ということです。",
        ],
    )
    return f"{lead}\n\n{example}"


def paragraph_definition(term: str, merged: str, kind: str, category: str) -> str:
    field = FIELD_LABEL.get(category, "本分野")
    if kind == "law":
        return (
            f"「{term}」は、{merged}。"
            f"{exam_name()}の{field}では、誰が・いつ・何をしなければならないかが、"
            f"正しい選択肢を選ぶうえでの中心になります。"
        )
    if kind == "operation":
        return (
            f"「{term}」は、{merged}。"
            f"取扱い分野では、「いつ行うか」と「やってはいけない操作」をセットで理解することが大切です。"
        )
    if kind == "combustion":
        return (
            f"「{term}」は、{merged}。"
            f"燃焼・排ガス・効率のどれに影響するかを短く言えると、数値の問題にもつながりやすくなります。"
        )
    if kind == "equipment":
        return (
            f"「{term}」は、{merged}。"
            f"系統図のどこにあるか、近くの計器や弁と役割を分担しているかを一緒に整理すると覚えやすいです。"
        )
    return (
        f"「{term}」は、{merged}。"
        f"{field}分野の基本語として、言い換えられた定義文にも対応できるように押さえておきましょう。"
    )


def paragraph_field_context(
    term: str, kind: str, category: str, merged: str, related: list[str]
) -> str:
    rel = related_phrase(term, related)
    if kind == "law" and "検査" in term:
        return (
            f"使用検査・性能検査・定期自主検査など、名前が近い検査は多いです。"
            f"表で「いつ・誰が・何を見るか」を並べてから「{term}」を覚えると、混乱しにくくなります。"
            f"検査証の交付や有効期間も、過去問では一文ずつ言い換えて出題されます。"
        )
    if kind == "law":
        return (
            f"届出・検査・記録は、「誰が行うか」と「期限」をセットで覚えると整理しやすいです。"
            f"「原則として禁止」「例外で認められる」など、語尾の違いに注意しながら、"
            f"{rel}のページと条文の趣旨を往復して読んでください。"
        )
    if kind == "operation" and any(k in term for k in ("水位", "だき", "ブロー", "吹出")):
        return (
            f"安全運転に直結する語句です。異常時に「燃焼を続ける」「急に大量給水する」といった"
            f"危険な対応が誤答になりやすいので、公式テキストの手順どおりに整理してください。"
            f"原因を考えるときは、給水・ブロー・負荷・計器の故障を{rel}と結びつけるとよいです。"
        )
    if kind == "combustion":
        return (
            f"空気量・燃料量・排ガス（O2、CO2、CO）の関係を、ひとつの流れとして覚えましょう。"
            f"「増やすと効率が上がる／下がる」「不完全燃焼になる」など、影響の方向を逆にしないことが重要です。"
            f"{rel}とあわせて、燃焼管理の数値問題を解き直すと定着します。"
        )
    if "弁" in term:
        return (
            f"安全弁・逃がし弁・止弁など、名前が近い弁は「自動で開くか」「人が開閉するか」"
            f"「流れを止めるか」で整理できます。「{term}」の目的を一言で言えないまま暗記すると、"
            f"選択肢の入れ替えに弱くなります。"
        )
    if kind == "boiler_type":
        return (
            f"水量・起動時間・水質管理・適用法令の違いが、構造問題と法令問題の両方に出ます。"
            f"炉筒煙管・水管・貫流の比較表を見ながら、「{term}」を構造・運転・法令の3点で説明できるようにしましょう。"
        )
    if kind == "concept":
        return (
            f"定義だけでなく、数値が変わったときに効率や安全、ほかの用語にどう影響するかまで"
            f"一文で説明できると得点源になります。{rel}との関係や単位もセットで確認してください。"
        )
    return (
        f"現場では「{merged.rstrip('。')}」という理解が、異常判断や日常点検の説明につながります。"
        f"過去問では定義の一部が別の語に置き換えられた選択肢が多いので、{rel}と往復して違いを言葉にしてください。"
    )


def paragraph_exam_trap(term: str, kind: str, category: str, related: list[str]) -> str:
    rel = related_phrase(term, related)
    traps: list[str] = []
    if kind == "law":
        traps.append("届出・検査・記録の要否を逆に覚える")
        traps.append("主体（誰が行うか）と期限を取り違える")
    elif kind == "operation":
        traps.append("手順の前後を逆にする")
        traps.append("異常時の最初の対応を「運転継続」にする記述を選ぶ")
    elif kind == "combustion":
        traps.append("完全燃焼と不完全燃焼の因果を逆に結びつける")
        traps.append("空気比が大きい／小さい場合の影響を混同する")
    elif "弁" in term:
        traps.append("安全弁と逃がし弁・止弁の目的を入れ替える")
    else:
        traps.append("定義だけ暗記し、言い換えに対応できない")
    if related:
        traps.append(f"{rel}との役割の取り違え")
    trap_text = "、".join(traps[:3])
    return (
        f"試験で落としやすいのは、{trap_text}などです。"
        f"選択肢を読むときは、「{term}」の目的と条件が、文全体と一致しているかを確認する習慣をつけましょう。"
    )


def paragraph_on_site(term: str, merged: str, kind: str) -> str:
    if kind == "equipment":
        return (
            f"運転室では、「{term}」の指示や異常の有無が、ほかの計器や弁の操作判断に直結します。"
            f"「今の値・状態は、安全上問題ないか」を確認する視点を持つとよいです。"
        )
    if kind == "operation":
        return (
            f"現場では、手順書どおりの順序が守られているか、記録と実際の操作が一致しているかが重要です。"
            f"「{term}」を単独の作業名として覚えるのではなく、前後の工程とセットで思い出してください。"
        )
    if kind == "combustion":
        return (
            f"燃焼調整では、「{term}」に関わる数値や状態（炎の色、排ガス、圧力）を短時間で確認し、"
            f"変化の方向を判断する力が求められます。"
        )
    return (
        f"試験本番では、「{merged.rstrip('。')}」という一文が、語順や主語を変えた選択肢として出ます。"
        f"「だいたい同じ意味」ではなく、条件の追加・削除がないかを確認する癖をつけましょう。"
    )


def paragraph_study(
    term: str, category: str, related: list[str], has_table: bool
) -> str:
    rel = related_phrase(term, related)
    table_note = "比較・整理表で違いを確認してから、" if has_table else ""
    field = FIELD_LABEL.get(category, "本分野")
    return pick(
        term,
        [
            (
                f"おすすめの学習手順は次のとおりです。"
                f"①「{term}」を一文で説明する → ②{table_note}関連語{rel}のページを読む → "
                f"③過去問形式で正誤を仕分ける → ④間違えた言い回しをメモに残す。"
            ),
            (
                f"復習では、{table_note}関連語{rel}とあわせて「正しい記述／誤った記述」を"
                f"声に出して理由まで言えるようにしてください。"
                f"{field}の弱点リストに「{term}」を必ず入れておくと、直前対策にも使えます。"
            ),
        ],
    )


def compose_body(
    term: str,
    short: str,
    detail: str,
    category: str,
    related: list[str],
    kind: str,
    has_table: bool,
) -> str:
    merged = merge_defs(short, detail)
    parts = [
        paragraph_definition(term, merged, kind, category),
        paragraph_field_context(term, kind, category, merged, related),
        paragraph_on_site(term, merged, kind),
        paragraph_exam_trap(term, kind, category, related),
        paragraph_study(term, category, related, has_table),
    ]
    return "\n\n".join(p for p in parts if p.strip())


def compose_lead(term: str, short: str, detail: str, category: str) -> str:
    core = merge_defs(short, detail).rstrip("。")
    field = FIELD_LABEL.get(category, "本分野")
    return (
        f"このページでは、{exam_name()}の{field}分野で出る「{term}」を、"
        f"初めて学ぶ方にも分かるように説明します。"
        f"意味（{core}）に加え、試験で問われやすいポイント・関連用語・例題もまとめています。"
    )


def compose_title(term: str, category: str) -> str:
    field = FIELD_LABEL.get(category, "本分野")
    return pick(
        term,
        [
            f"{term}とは？2級ボイラー技士【{field}】の意味・例・試験の出方",
            f"{term}の意味と覚え方｜2級ボイラー技士（{field}）",
            f"【{field}】{term}とは？要点・よくある誤り・例題",
        ],
    )


def compose_exam_points(
    term: str, short: str, detail: str, kind: str, category: str, related: list[str]
) -> list[str]:
    core = merge_defs(short, detail).rstrip("。")
    pts = [f"「{core}」を、30秒以内に自分の言葉で説明できる"]
    if kind == "law":
        pts.extend(
            [
                "主体（誰が）・時期（いつ）・要否（届出／検査／記録）を整理できる",
                "「原則／例外」「認められない」の文言に注意して選択肢を読む",
            ]
        )
    elif kind == "operation":
        pts.extend(
            [
                "実施タイミングと、しなかった場合のリスクを結びつけられる",
                "異常時の最初の対応（停止・確認）を手順どおり説明できる",
            ]
        )
    elif kind == "combustion":
        pts.extend(
            [
                "増減・過大／過小の影響を排ガス・効率・安全に結びつけられる",
                "数値（空気比・発熱量・成分）と現象説明をセットで復習できる",
            ]
        )
    elif "弁" in term:
        pts.append("他の弁との目的・作動（自動／手動）の違いを一言で言える")
    else:
        pts.append(f"{FIELD_LABEL.get(category, '本分野')}の過去問で出た言い換えを1つメモできる")
    if related:
        rel = "・".join(related[:3])
        pts.append(f"関連語（{rel}）との違いを説明できる")
    return pts[:5]


def compose_mistakes(term: str, kind: str, related: list[str]) -> list[str]:
    items: list[str] = []
    if related:
        items.append(
            f"「{related[0]}」と「{term}」の役割や定義を取り違える（それぞれの用語ページで違いを確認）"
        )
    if kind == "law":
        items.append("届出・検査・記録の要否や主体・期限を逆に覚える")
    elif kind == "operation":
        items.append("手順の順序や、異常時の最初の対応を誤る")
    elif kind == "combustion":
        items.append("燃焼の因果（空気・燃料・排ガス）を逆に結びつける")
    elif "弁" in term:
        items.append("名称が近い弁の役割を混同する")
    items.append("定義文を丸暗記し、言い換え・数値条件の選択肢に対応できない")
    return items[:4]


def compose_memory(
    term: str, kind: str, category: str, short: str, related: list[str], has_table: bool
) -> str:
    rel = related_phrase(term, related)
    field = FIELD_LABEL.get(category, "本分野")
    core = merge_defs(short, "").rstrip("。")[:50]
    axes = {
        "law": "覚え方の軸は「誰が／いつ／要否」の3列メモ",
        "operation": "覚え方の軸は「いつ・なぜ・危険（しなかったらどうなるか）」",
        "combustion": "覚え方の軸は「増やす／減らすと、排ガス・効率・安全はどう変わるか」",
        "equipment": "覚え方の軸は「どこにある・何を見る・何を防ぐ」",
        "concept": "覚え方の軸は「定義→単位→ほかの用語への影響」",
        "boiler_type": "覚え方の軸は「構造・水量・法令の違い」",
    }
    axis = axes.get(kind, f"短い定義「{core}」＋{field}分野の言い換え1つ")
    table_line = (
        "比較・整理表で似た用語を横に並べ、違う行だけにマーカーを付ける。"
        if has_table
        else f"関連語{rel}の定義をノートに2列で書き、違う語だけ下線を引く。"
    )
    return (
        f"{axis}。見出しは「{term}」、中身は一文定義＋具体例を書く。\n\n"
        f"整理のコツ：{table_line} "
        f"正しい記述と誤った記述を1組ずつ作り、声に出して理由まで言えるようにする。\n\n"
        f"直前チェック：「{term}」を説明したあと、関連語との違いを10秒以内に言えるか確認する。"
    )


def compose_explanation(term: str, detail: str, short: str, kind: str) -> str:
    base = merge_defs(short, detail).rstrip("。")
    suffix = {
        "law": "数字・主体・期限は、最新の試験要項と公式テキストで必ず照合してください。",
        "operation": "日常手順と異常時の対応を混同しないよう、「いつ行うか」で整理してください。",
        "combustion": "排ガス分析・空気比とセットで復習すると、数値問題にもつながります。",
        "equipment": "系統図上の位置を思い浮かべながら読むと、ほかの装置との違いが分かりやすくなります。",
    }.get(kind, "近い用語との違いを、一言で言えるようにしておきましょう。")
    return f"{base}。{suffix}"


def compose_example(
    term: str, short: str, detail: str, kind: str, category: str
) -> tuple[str, str]:
    q = f"次の記述のうち、「{term}」について最も適切な説明はどれか。（正誤問題を想定）"
    core = merge_defs(short, detail).rstrip("。")
    if kind == "law":
        a = (
            f"正解の考え方：{core}。届出・検査・記録の問題では、"
            f"主体と期限が条文の趣旨と一致しているかを確認します。"
        )
    elif kind == "operation":
        a = (
            f"正解の考え方：{core}。手順問題では、実施タイミングと安全上の目的が"
            f"一致している選択肢を選びます。"
        )
    else:
        a = (
            f"正解の考え方：{core}。定義のキーワードが欠けたり、"
            f"近い用語の説明が混ざった選択肢は誤りになりやすいです。"
        )
    return q, a


def compose_faqs(
    term: str,
    short: str,
    detail: str,
    category: str,
    kind: str,
    related: list[str],
    exam_pts: list[str],
    mistakes: list[str],
) -> tuple[
    tuple[str, str],
    tuple[str, str],
    tuple[str, str],
    tuple[str, str],
]:
    core = merge_defs(short, detail).rstrip("。")
    field = FIELD_LABEL.get(category, category)
    rel = related_phrase(term, related, 2)

    q1 = f"「{term}」とは何ですか？"
    a1 = (
        f"{term}は、{core}。"
        f"{exam_name()}では、定義の言い換えや、近い用語との違いがよく問われます。"
    )

    q2 = f"「{term}」は{exam_name()}でどう出題されますか？"
    pt_hint = exam_pts[1] if len(exam_pts) > 1 else (exam_pts[0] if exam_pts else "")
    a2 = (
        f"主に「{field}」から出題されます。"
        f"正誤問題では、条件や主体だけが入れ替わった選択肢に注意してください。"
        f"{pt_hint}"
    ).strip()

    q3 = f"「{term}」と似た用語との違いは？"
    if related:
        a3 = (
            f"混同しやすいのは{rel}です。"
            f"「{term}」は{core}。"
            f"それぞれの用語ページと比較表で、役割・タイミング・目的の違いを確認してください。"
        )
    else:
        a3 = mistakes[0] if mistakes else (
            f"定義だけを覚え、選択肢の言い換えに対応できないことがあります。"
            f"「{term}」の目的と条件をセットで説明できるようにしてください。"
        )

    q4 = f"「{term}」の覚え方・復習のコツは？"
    a4 = pick(
        term,
        [
            (
                f"①一文定義を声に出す → ②関連語{rel}と違いを比較 → "
                f"③過去問で正誤を仕分ける、の順がおすすめです。"
                f"間違えた言い回しはメモに残し、直前に見返してください。"
            ),
            (
                f"具体例を思い浮かべながら「{core}」を復習すると定着しやすいです。"
                f"弱点リストに「{term}」を入れ、週に1回は関連語とセットで見直しましょう。"
            ),
        ],
    )
    return (q1, a1), (q2, a2), (q3, a3), (q4, a4)

# 用語詳細記事リライト進捗

`data/glossary_terms.csv` の個別用語（頻出テーマ行を除く）について、詳細記事用フィールドを充実させる作業の進捗です。

## 手順（分野ごと）

1. `python3 tools/rewrite_glossary_articles.py --category "〈分野名〉"`
2. `python3 tools/build_glossary_pages.py`
3. `python3 tools/validate_csv.py`（警告の確認）
4. サンプル数件をブラウザで目視

一括: `python3 tools/rewrite_glossary_articles.py --all`

## 進捗（2026-05-22）

| 順 | 分野 | 語数 | 状態 |
|---|------|------|------|
| 1 | ボイラーの構造に関する知識 | 106 | 完了 |
| 2 | ボイラーの取扱いに関する知識 | 87 | 完了 |
| 3 | 燃料及び燃焼に関する知識 | 83 | 完了 |
| 4 | 関係法令 | 66 | 完了 |

**合計 342 語**を `tools/rewrite_glossary_articles.py` でリライト済み。

## 充実させた CSV 列

- `article_title`, `article_lead`
- `term_detail_body`, `exam_points`, `common_mistakes`, `memory_tip`
- `explanation`（汎用テンプレ文の置き換え）
- `faq_1_*` 〜 `faq_3_*`

## 深化作業（2026-05-22 完了）

- `tools/glossary_related_aliases.py` + `fix_glossary_related_terms.py` で `related_terms` を登録済み用語名へ正規化
- `tools/glossary_article_overrides.py` + `apply_glossary_overrides.py` で高頻出15語に比較表・手書き本文を適用
- `comparison_html` 列を CSV / build に追加（比較・整理表セクション）

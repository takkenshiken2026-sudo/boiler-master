# 用語詳細記事リライト進捗

`data/glossary_terms.csv` の個別用語（頻出テーマ行を除く）について、詳細記事用フィールドを充実させる作業の進捗です。

## 手順（分野ごと・手書き品質）

1. `python3 tools/handwrite_glossary_articles.py --all --include-themes --no-snippets`（全件をエンジンで再生成）
2. `python3 tools/build_handwritten_modules.py`（スニペット `.py` を CSV と同期）
3. `python3 tools/build_glossary_pages.py`
4. `python3 tools/validate_csv.py`（警告の確認）
5. `python3 tools/validate_generated_seo.py` / `validate_internal_links.py`
6. サンプル数件をブラウザで目視

一括: 上記 2〜3 を順に実行。

個別語の手直しは `tools/glossary_handwritten/structure.py` など分野別ファイルを直接編集し、再度 2〜3 を実行。

## 進捗（2026-05-24）

| 順 | 分野 | 個別語数 | 状態 |
|---|------|----------|------|
| 1 | ボイラーの構造に関する知識 | 106 | 手書きリライト完了 |
| 2 | ボイラーの取扱いに関する知識 | 87 | 手書きリライト完了 |
| 3 | 燃料及び燃焼に関する知識 | 83 | 手書きリライト完了 |
| 4 | 関係法令 | 66 | 手書きリライト完了 |

**合計 377 行**（個別用語 342 ＋ 頻出テーマ 35）を `handwrite_glossary_articles.py` で全件リライト。  
スニペット本体は `tools/glossary_handwritten/{structure,handling,combustion,law}.py` に分野別保存（編集可能）。

## 充実させた CSV 列

- `article_title`, `article_lead`
- `term_detail_body`, `exam_points`, `common_mistakes`, `memory_tip`
- `explanation`（分野・用語種別に沿った具体文）
- `example_question`, `example_answer`
- `faq_1_*` 〜 `faq_4_*`（よくある質問 3〜4 件）
- `short_def` … ページ上部「まず押さえる要点」（定義＋具体例の2段落）
- `comparison_html`（登録済み比較表・関連用語経由の共有表）

## 読みやすさ・具体例の強化（2026-05-24 追記）

- `tools/glossary_article_compose.py` … 平易な文体、要点の具体例、覚え方3段落、FAQ4件
- `handwrite_glossary_articles.py --no-snippets` … 旧スニペットを無視して全件再生成
- 個別語の手直しはスニペット編集後、`handwrite`（スニペットあり）または `--no-snippets` で反映

## 手書きリライトの内容（2026-05-24）

- `tools/handwrite_glossary_articles.py` … 5段落構成の本文・固有リード・例題・FAQ（スニペット優先）
- `tools/build_handwritten_modules.py` … 全語スニペットを分野別 `.py` に書き出し
- `tools/glossary_handwritten/` … 手編集用のスニペット置き場（342語）
- `tools/glossary_comparison_registry.py` … 比較表
- `tools/build_glossary_pages.py` … 比較・整理表セクションを公開

### 品質指標（個別用語342件・2026-05-24 追記後）

| 指標 | 件数 |
|------|------|
| まず押さえる要点（2段落・具体例付き） | 342 / 342 |
| 覚え方・整理のコツ（3段落） | 342 / 342 |
| FAQ（4問） | 342 / 342 |
| 例題 | 342 / 342 |
| 比較表 | 約335 / 342 |
| 本文（5段落・ですます調） | 全件 |
| 頻出テーマ行 | 35（`--include-themes`） |

語ごとに文章を差し替えるときは `tools/glossary_handwritten/<分野>.py` を編集 → `handwrite_glossary_articles.py --all` → `build_glossary_pages.py`。

## 以前の作業（2026-05-22）

- `tools/rewrite_glossary_articles.py` で初回リライト（342語）
- `tools/glossary_related_aliases.py` + `fix_glossary_related_terms.py` で `related_terms` 正規化
- `tools/glossary_article_overrides.py` で高頻出15語に比較表・手書き本文

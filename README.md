# exam-site-shell

資格学習サイトを短時間で立ち上げるためのテンプレートです。`chintaikanrishi-master` 型の UI と生成フローをもとに、サイト名・試験名・分野名・CSV データを差し替えて使える形にしています。

## 含まれる機能

- 一問一答、過去問、実践演習、記録・分析、復習、集中タイマーを備えた SPA トップ
- `data/*.csv` から演習用 JS を生成
- `q/past/...` の静的過去問ページ生成
- `terms/g-*.html` と `terms/index.html` の用語ページ生成
- `public_site/` への配信用バンドル作成
- GitHub Pages Actions のサンプル

## 初期セットアップ

```bash
python3 tools/build_all.py
python3 -m http.server 8765
```

ローカル確認: `http://127.0.0.1:8765/`

## 差し替えポイント

- `site-config.json`: サイト名・略称・試験名・ドメイン・問い合わせ先・公式リンク・GA4 ID・分野名
- `site-config.json` の `theme`: アクセント色、背景色、角丸、コンテンツ幅
- `site-config.json` の `navigation`: 静的ページのヘッダー/フッターナビ
- `data/past_questions.csv`: 過去問・通常演習データ
- `data/original_questions.csv`: 実践演習データ
- `data/past_questions_marubatsu_all_explanations.csv`: 一問一答データ
- `data/glossary_terms.csv`: 用語集データ
- `tools/build_all.py`: 設定反映、JS生成、静的ページ生成、`public_site/` 作成を一括実行

## CSV の基本列

`past_questions.csv` は、`exam_year`, `exam_wareki`, `question_no`, `category`, `stem`, `choice_1`〜`choice_4`, `correct`, `explanation` を中心に使います。`category` は `site-config.json` の `fields[].name` または `fields[].aliases` に合わせてください。

CSVだけ先に検査したい場合は、次を実行します。

```bash
python3 tools/validate_csv.py
```

検査では、必須列、空の重要項目、未登録カテゴリ、正答番号（1〜4）、一問一答の `○/×`、重複ID、用語の重複などを確認します。`python3 tools/build_all.py` の先頭でも自動実行され、エラーがある場合は生成を止めます。

## 新しい資格サイトを作る手順

1. `site-config.json` の `brandName`, `examName`, `siteOrigin`, `contactUrl`, `fields`, `externalLinks` を編集します。
2. `data/*.csv` を対象資格の問題・一問一答・用語データに差し替えます。
3. `python3 tools/build_all.py` を実行します。
4. `public_site/` をローカルサーバーまたは GitHub Pages で確認します。

## 表示品質チェック

長い試験名・多分野でも生成できるか確認する場合は、次を実行します。実行後、元の `site-config.json` に戻して再ビルドします。

```bash
python3 tools/stress_config_build.py
```

主要ページのスクリーンショットをまとめて確認したい場合は、ローカルサーバーを起動してから次を実行します。Playwright が未導入の場合は、確認対象URLと導入手順だけを表示します。

```bash
python3 -m http.server 8765
python3 tools/visual_smoke_check.py --base-url http://127.0.0.1:8765
```

## 注意

初期データは動作確認用のサンプルです。本番公開前に、プライバシー表記、公式リンク、GA4 ID、問題の権利関係を必ず確認してください。

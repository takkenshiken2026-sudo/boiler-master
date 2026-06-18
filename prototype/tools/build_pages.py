#!/usr/bin/env python3
"""certifications.csv から静的サイト(prototype/site/)を生成する。

- site/index.html        : ファセット検索トップ(大分類・type・フリーワード)
- site/c/<slug>.html     : 資格詳細ページ
- site/data/certifications.json : クライアント検索用データ
- site/assets/app.css, search.js

掲載対象(indexable): is_bucket=0 かつ is_duplicate=0 かつ scope=domestic。
プロトタイプのため全ページ <meta name="robots" content="noindex"> で出力。
事実値(受験料/合格率/公式URL)は未検証なら「公式で確認」を促す。
"""
import csv
import html
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV = ROOT / "data" / "certifications.csv"
SITE = ROOT / "site"

SITE_NAME = "資格カタログ（仮）"
TYPE_BADGE = {
    "国家": ("国家資格", "badge-national"),
    "公的": ("公的資格", "badge-public"),
    "民間": ("民間資格", "badge-private"),
    "要確認": ("区分要確認", "badge-unknown"),
    "海外": ("海外資格", "badge-overseas"),
}


def esc(s: str) -> str:
    return html.escape(s or "", quote=True)


def load_rows():
    with CSV.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def page_shell(title: str, body: str, depth: int) -> str:
    base = "../" * depth
    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex"><!-- prototype -->
<title>{esc(title)}</title>
<link rel="stylesheet" href="{base}assets/app.css">
</head>
<body>
<header class="site-header"><a href="{base}index.html" class="logo">{esc(SITE_NAME)}</a>
<span class="tagline">日本の資格を探せる・絞れる・比べられる</span></header>
<main class="container">
{body}
</main>
<footer class="site-footer">出典: 厚生労働省 ハローワーク 免許・資格コード一覧をシードに作成（プロトタイプ）。
数値・制度は各資格の公式情報で必ずご確認ください。</footer>
</body>
</html>
"""


def build_detail(row) -> str:
    name = row["name"]
    label, cls = TYPE_BADGE.get(row["type"], ("区分要確認", "badge-unknown"))
    major = row["major_category"]
    cat = row["category"]

    def field(v, fallback="公式情報で確認"):
        return esc(v) if v else f'<span class="muted">{fallback}</span>'

    official = ""
    if row["official_url"]:
        u = esc(row["official_url"])
        official = f'<a href="{u}" rel="nofollow noopener" target="_blank">公式サイト</a>'
    else:
        official = '<span class="muted">未登録（一次情報で確認予定）</span>'

    rows_html = "".join(
        f"<tr><th>{esc(k)}</th><td>{v}</td></tr>"
        for k, v in [
            ("資格区分", f'<span class="badge {cls}">{esc(label)}</span>'
                        f' <span class="muted">（{esc(row["type_reason"])}）</span>'),
            ("分野（大分類）", esc(major)),
            ("カテゴリ", esc(cat)),
            ("実施団体", field(row["authority"])),
            ("公式サイト", official),
            ("受験資格", field(row["eligibility"])),
            ("試験形式", field(row["exam_format"])),
            ("受験料", field(row["fee"])),
            ("合格率", field(row["pass_rate"])),
            ("実施頻度", field(row["frequency"])),
            ("ハローワークコード", esc(row["hellowork_code"])),
        ]
    )

    body = f"""<nav class="crumbs"><a href="../index.html">トップ</a> ›
<a href="../index.html?major={esc(major)}">{esc(major)}</a> › {esc(name)}</nav>
<h1>{esc(name)}</h1>
<p class="lead">{esc(name)}は「{esc(major)}」分野の資格です。最新の受験料・日程・合格率は公式情報でご確認ください。</p>
<table class="spec">{rows_html}</table>
<section class="related"><h2>同じカテゴリの資格</h2><ul id="related"></ul></section>
<script>
fetch("../data/certifications.json").then(r=>r.json()).then(all=>{{
  const cat={json.dumps(cat, ensure_ascii=False)}, me={json.dumps(row["slug"], ensure_ascii=False)};
  const ul=document.getElementById("related");
  all.filter(x=>x.category===cat&&x.slug!==me).slice(0,12).forEach(x=>{{
    const li=document.createElement("li");
    li.innerHTML='<a href="'+x.slug+'.html">'+x.name+'</a>';
    ul.appendChild(li);
  }});
  if(!ul.children.length) ul.innerHTML='<li class="muted">なし</li>';
}});
</script>
"""
    return page_shell(f"{name}｜{SITE_NAME}", body, depth=1)


def build_index(rows) -> str:
    body = f"""<h1>日本の資格カタログ</h1>
<p class="lead">資格名で検索、または分野・区分で絞り込めます。現在 <strong id="count">-</strong> 件を収録（プロトタイプ）。</p>
<div class="controls">
  <input id="q" type="search" placeholder="資格名で検索（例: 簿記, 電気, ボイラー）">
  <select id="major"><option value="">分野（すべて）</option></select>
  <select id="type"><option value="">区分（すべて）</option></select>
</div>
<p id="status" class="muted"></p>
<ul id="results" class="results"></ul>
<script src="assets/search.js"></script>
"""
    return page_shell(SITE_NAME, body, depth=0)


SEARCH_JS = """(function(){
  var q=document.getElementById('q'),majorSel=document.getElementById('major'),
      typeSel=document.getElementById('type'),results=document.getElementById('results'),
      status=document.getElementById('status'),count=document.getElementById('count');
  var DATA=[];
  function opt(sel,v){var o=document.createElement('option');o.value=v;o.textContent=v;sel.appendChild(o);}
  function render(){
    var t=(q.value||'').trim().toLowerCase(),mj=majorSel.value,tp=typeSel.value;
    var out=DATA.filter(function(x){
      if(mj&&x.major!==mj)return false;
      if(tp&&x.type!==tp)return false;
      if(t&&x.name.toLowerCase().indexOf(t)<0)return false;
      return true;
    });
    status.textContent=out.length+' 件';
    results.innerHTML=out.slice(0,300).map(function(x){
      return '<li><a href="c/'+x.slug+'.html">'+x.name+'</a>'+
        '<span class="meta"><span class="badge b-'+x.type+'">'+x.type+'</span> '+x.major+' / '+x.category+'</span></li>';
    }).join('')||'<li class="muted">該当なし</li>';
    if(out.length>300) results.innerHTML+='<li class="muted">…他 '+(out.length-300)+' 件（絞り込んでください）</li>';
  }
  fetch('data/certifications.json').then(function(r){return r.json();}).then(function(all){
    DATA=all; count.textContent=all.length;
    var majors={},types={};
    all.forEach(function(x){majors[x.major]=1;types[x.type]=1;});
    Object.keys(majors).sort().forEach(function(v){opt(majorSel,v);});
    ['国家','公的','民間','要確認'].forEach(function(v){if(types[v])opt(typeSel,v);});
    var p=new URLSearchParams(location.search);
    if(p.get('major'))majorSel.value=p.get('major');
    render();
  });
  [q,majorSel,typeSel].forEach(function(el){el.addEventListener('input',render);});
})();
"""

APP_CSS = """*{box-sizing:border-box}body{margin:0;font-family:system-ui,-apple-system,"Hiragino Kaku Gothic ProN",Meiryo,sans-serif;color:#1b2430;line-height:1.7;background:#f7f8fa}
a{color:#1565c0;text-decoration:none}a:hover{text-decoration:underline}
.site-header{background:#0d47a1;color:#fff;padding:14px 20px;display:flex;align-items:baseline;gap:14px;flex-wrap:wrap}
.site-header .logo{color:#fff;font-weight:700;font-size:1.15rem}.tagline{color:#cfe0fb;font-size:.85rem}
.container{max-width:920px;margin:0 auto;padding:22px 18px}
h1{font-size:1.5rem;margin:.2em 0 .4em}.lead{color:#43505f}
.controls{display:flex;gap:10px;flex-wrap:wrap;margin:16px 0}
.controls input,.controls select{padding:10px 12px;border:1px solid #c5ccd6;border-radius:8px;font-size:1rem}
.controls input{flex:1 1 260px}
.results{list-style:none;padding:0;margin:0}
.results li{background:#fff;border:1px solid #e6e9ef;border-radius:10px;padding:12px 14px;margin-bottom:8px}
.results li a{font-weight:600}.results .meta{display:block;color:#6b7682;font-size:.82rem;margin-top:3px}
.badge{display:inline-block;padding:1px 8px;border-radius:999px;font-size:.75rem;font-weight:700;color:#fff;vertical-align:middle}
.badge-national,.b-国家{background:#c62828}.badge-public,.b-公的{background:#1565c0}
.badge-private,.b-民間{background:#2e7d32}.badge-unknown,.b-要確認{background:#8a939e}.badge-overseas{background:#6a1b9a}
.crumbs{font-size:.85rem;color:#6b7682;margin-bottom:8px}
table.spec{width:100%;border-collapse:collapse;background:#fff;border:1px solid #e6e9ef;border-radius:10px;overflow:hidden}
table.spec th,table.spec td{text-align:left;padding:10px 14px;border-bottom:1px solid #eef1f5;vertical-align:top}
table.spec th{width:34%;background:#f2f5fa;color:#3a4757;font-weight:600;white-space:nowrap}
.muted{color:#98a1ad}.related{margin-top:24px}.related ul{padding-left:1.1em}
.site-footer{max-width:920px;margin:30px auto;padding:16px 18px;color:#7a838f;font-size:.8rem;border-top:1px solid #e6e9ef}
"""


def main() -> int:
    rows = load_rows()
    indexable = [r for r in rows
                 if r["is_bucket"] == "0" and r["is_duplicate"] == "0"
                 and r["scope"] == "domestic"]

    if SITE.exists():
        shutil.rmtree(SITE)
    (SITE / "c").mkdir(parents=True)
    (SITE / "data").mkdir()
    (SITE / "assets").mkdir()

    # JSON（検索用に必要列のみ）
    payload = [{
        "slug": r["slug"], "name": r["name"], "major": r["major_category"],
        "category": r["category"], "type": r["type"],
    } for r in indexable]
    payload.sort(key=lambda x: (x["major"], x["category"], x["name"]))
    (SITE / "data" / "certifications.json").write_text(
        json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    (SITE / "assets" / "app.css").write_text(APP_CSS, encoding="utf-8")
    (SITE / "assets" / "search.js").write_text(SEARCH_JS, encoding="utf-8")
    (SITE / "index.html").write_text(build_index(indexable), encoding="utf-8")

    for r in indexable:
        (SITE / "c" / f'{r["slug"]}.html').write_text(build_detail(r), encoding="utf-8")

    print(f"built site at {SITE.relative_to(ROOT)}")
    print(f"  index + {len(indexable)} detail pages")
    print(f"  excluded: bucket/duplicate/overseas = {len(rows)-len(indexable)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

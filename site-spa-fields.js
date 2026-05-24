// SPA bootstrap: site-config.js の直後・データ JS の前に読み込む（defer 順序を維持）
// eisei1-master-data.js 末尾から applyCsvImportedQuestions が呼ばれる
var SITE_CONFIG = window.SITE_CONFIG || {};
var FIELDS = (Array.isArray(SITE_CONFIG.fields) && SITE_CONFIG.fields.length)
  ? SITE_CONFIG.fields.map(function (f) {
      return {
        id: String(f.id),
        name: String(f.name || f.id),
        aliases: Array.isArray(f.aliases) ? f.aliases.map(String) : [],
        legacyGlossaryCat: String(f.legacyGlossaryCat || f.id),
      };
    })
  : [
      { id: "law", name: "法令・制度", aliases: ["法令・制度", "関連法令"], legacyGlossaryCat: "lawN" },
      { id: "rights", name: "契約・実務", aliases: ["契約・実務", "実務"], legacyGlossaryCat: "rightsN" },
      { id: "limit", name: "設備・その他", aliases: ["設備・その他", "その他"], legacyGlossaryCat: "limit" },
    ];
function getFieldLabel(fieldId) {
  var f = FIELDS.find(function (x) {
    return x.id === fieldId;
  });
  return f ? f.name : fieldId || "—";
}
function getFieldIds() {
  return FIELDS.map(function (f) {
    return f.id;
  });
}
function buildEvenFieldDistribution(total) {
  var ids = getFieldIds();
  var dist = {};
  if (!ids.length) return dist;
  ids.forEach(function (id, idx) {
    dist[id] = Math.floor(total / ids.length) + (idx < total % ids.length ? 1 : 0);
  });
  return dist;
}
function getGlossaryCatDefs() {
  return [{ id: "all", label: "すべて", title: "すべて" }].concat(
    FIELDS.map(function (f) {
      return { id: f.legacyGlossaryCat || f.id, label: f.name, title: f.name };
    })
  );
}
function glossaryCatFromName(name) {
  var n = String(name || "").trim();
  for (var i = 0; i < FIELDS.length; i++) {
    var f = FIELDS[i];
    var names = [f.name].concat(f.aliases || []);
    if (names.indexOf(n) !== -1) return f.legacyGlossaryCat || f.id;
  }
  return FIELDS[0] ? FIELDS[0].legacyGlossaryCat || FIELDS[0].id : "all";
}
function applyCsvImportedQuestions() {
  if (typeof CSV_IMPORTED_QUESTIONS === "undefined" || !Array.isArray(CSV_IMPORTED_QUESTIONS)) return;
  var rows = CSV_IMPORTED_QUESTIONS;
  var origSet =
    typeof CSV_IMPORTED_ORIG_POOL_YEARS !== "undefined" && Array.isArray(CSV_IMPORTED_ORIG_POOL_YEARS)
      ? new Set(CSV_IMPORTED_ORIG_POOL_YEARS)
      : new Set();
  BASE_QUESTIONS = rows.filter(function (q) {
    return q && q.year != null && q.year !== "" && !origSet.has(q.year);
  });
  QUESTIONS = rows.slice();
  var yset = new Set();
  BASE_QUESTIONS.forEach(function (q) {
    if (q.year != null && q.year !== "") yset.add(q.year);
  });
  YEARS = Array.from(yset).sort(function (a, b) {
    return b - a;
  });
}

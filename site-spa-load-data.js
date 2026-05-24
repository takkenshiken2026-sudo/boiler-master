// SPA 用データ JS を HTML パース後に順序付きで読み込む（レンダリングブロック回避）
(function (global) {
  var ASSETS = [
    "site-config.js?v=1be2997e8b6b",
    "site-spa-fields.js?v=1be2997e8b6b",
    "eisei1-data-glossary.js?v=1be2997e8b6b",
    "eisei1-data-original.js?v=1be2997e8b6b",
    "eisei1-master-data.js?v=1be2997e8b6b",
    "eisei1-data-ichimon.js?v=1be2997e8b6b",
  ];

  function loadOne(src) {
    return new Promise(function (resolve, reject) {
      var el = document.createElement("script");
      el.src = src;
      el.async = false;
      el.onload = function () {
        resolve();
      };
      el.onerror = function () {
        reject(new Error("Failed to load " + src));
      };
      document.head.appendChild(el);
    });
  }

  global.loadSpaDataAssets = function () {
    if (global.__spaDataLoadPromise) return global.__spaDataLoadPromise;
    global.__spaDataLoadPromise = ASSETS.reduce(function (chain, src) {
      return chain.then(function () {
        return loadOne(src);
      });
    }, Promise.resolve());
    return global.__spaDataLoadPromise;
  };
})(window);

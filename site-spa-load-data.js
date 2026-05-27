// SPA 用データ JS を HTML パース後に順序付きで読み込む（レンダリングブロック回避）
(function (global) {
  var ASSETS = [
    "site-config.js?v=d5f0bcec88da",
    "site-spa-fields.js?v=d5f0bcec88da",
    "eisei1-data-glossary.js?v=d5f0bcec88da",
    "eisei1-data-original.js?v=d5f0bcec88da",
    "eisei1-master-data.js?v=d5f0bcec88da",
    "eisei1-data-ichimon.js?v=d5f0bcec88da",
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

/* One initialization contract for static HTML and the legacy Docsify preview. */
(function () {
  window.Malayalam = {
    plugin: function (initialize) {
      if (window.$docsify) {
        window.$docsify.plugins = (window.$docsify.plugins || []).concat(initialize);
        return;
      }
      const callbacks = [];
      initialize({
        mounted: fn => callbacks.push(fn),
        doneEach: fn => callbacks.push(fn),
        beforeEach: function () { /* Full-page navigation needs no SPA cleanup. */ }
      });
      function run() { callbacks.forEach(fn => fn()); }
      if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', run, { once: true });
      else run();
    }
  };
}());

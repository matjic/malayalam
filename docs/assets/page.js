/* Initialize reading controls on each complete HTML page. */
(function () {
  window.Malayalam = {
    plugin: function (initialize) {
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

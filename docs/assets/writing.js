/* Inline local writing models so strokes, guides, and labels inherit CSS. */
(function () {
  const cache = new Map();
  window.$docsify.plugins = (window.$docsify.plugins || []).concat(function (hook) {
    hook.doneEach(function () {
      document.querySelectorAll('.markdown-section img').forEach(async function (img) {
        const url = new URL(img.src, location.href);
        if (url.origin !== location.origin ||
            !/\/assets\/writing\/(?:front-writing-\d{3}|symbols\/[a-z-]+)\.svg$/.test(url.pathname)) return;
        try {
          if (!cache.has(url.href)) {
            cache.set(url.href, fetch(url.href).then(function (response) {
              if (!response.ok) throw new Error('Writing diagram unavailable');
              return response.text();
            }));
          }
          const source = await cache.get(url.href);
          if (!img.isConnected) return;
          const documentSVG = new DOMParser().parseFromString(source, 'image/svg+xml');
          const svg = documentSVG.documentElement;
          if (svg.localName !== 'svg') throw new Error('Invalid writing diagram');
          svg.classList.add(img.closest('.writing-card') ? 'writing-symbol' : 'writing-table');
          svg.setAttribute('aria-label', img.alt);
          svg.removeAttribute('aria-labelledby');
          // The image already has an accessible label; avoid a tooltip covering guides.
          const title = svg.querySelector('title');
          if (title) title.remove();
          img.replaceWith(document.importNode(svg, true));
        } catch (error) {
          cache.delete(url.href);
          // The standalone SVG image remains usable if inlining fails.
          console.warn('Could not inline writing diagram:', error);
        }
      });
    });
  });
}());

/* Inline local writing models so strokes, guides, and labels inherit CSS. */
(function () {
  const cache = new Map();
  const preferences = { guides: true, weight: '8', size: '17' };
  window.$docsify.plugins = (window.$docsify.plugins || []).concat(function (hook) {
    hook.doneEach(function () {
      const section = document.querySelector('.markdown-section');
      const firstGrid = section.querySelector('.writing-grid');
      if (firstGrid && !section.querySelector('.writing-controls')) {
        const controls = document.createElement('fieldset');
        controls.className = 'writing-controls';
        controls.innerHTML = '<legend>Writing diagrams</legend>' +
          '<label><input type="checkbox" data-writing-guides> Show numbers and arrows</label>' +
          '<label>Line weight <input type="range" min="4" max="12" step="1" data-writing-weight></label>' +
          '<label>Diagram size <input type="range" min="13" max="24" step="1" data-writing-size></label>';
        firstGrid.before(controls);
        const guides = controls.querySelector('[data-writing-guides]');
        const weight = controls.querySelector('[data-writing-weight]');
        const size = controls.querySelector('[data-writing-size]');
        guides.checked = preferences.guides;
        weight.value = preferences.weight;
        size.value = preferences.size;
        function update() {
          preferences.guides = guides.checked;
          preferences.weight = weight.value;
          preferences.size = size.value;
          section.classList.toggle('writing-hide-guides', !preferences.guides);
          section.style.setProperty('--writing-stroke-width', preferences.weight);
          section.style.setProperty('--writing-card-size', preferences.size + 'rem');
        }
        controls.addEventListener('input', update);
        update();
      }
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

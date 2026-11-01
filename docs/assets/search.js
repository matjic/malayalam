/* Use the same search markup and theme as Docsify, with a build-time index. */
window.Malayalam.plugin(function (hook) {
  hook.mounted(function () {
    const search = document.querySelector('.search');
    const input = search.querySelector('input');
    const clear = search.querySelector('.clear-button');
    const panel = search.querySelector('.results-panel');
    let index, pending, timer;
    const normalize = text => text.normalize('NFC').toLowerCase();
    async function getIndex() {
      if (!pending) pending = fetch(document.body.dataset.base + 'assets/search-index.json', { cache: 'no-cache' })
        .then(response => { if (!response.ok) throw new Error('Search unavailable'); return response.json(); })
        .then(entries => entries.map(entry => ({ ...entry, titleText: normalize(entry.title), bodyText: normalize(entry.body) })));
      return pending;
    }
    async function update() {
      const query = input.value.trim();
      panel.replaceChildren();
      panel.classList.toggle('show', !!query);
      clear.classList.toggle('show', !!query);
      if (!query) return;
      try { index = index || await getIndex(); }
      catch (_) { panel.textContent = 'Search is unavailable. Use the Contents or Index links below.'; return; }
      if (input.value.trim() !== query) return;
      const terms = normalize(query).split(/\s+/);
      const matches = index.map(entry => ({ entry, score: terms.reduce((score, term) => score + (entry.titleText.includes(term) ? 3 : entry.bodyText.includes(term) ? 2 : 0), 0) }))
        .filter(({ entry }) => terms.every(term => entry.titleText.includes(term) || entry.bodyText.includes(term)))
        .sort((a, b) => b.score - a.score).slice(0, 30);
      if (!matches.length) { panel.textContent = 'No Results!'; return; }
      for (const { entry } of matches) {
        const result = document.createElement('div'); result.className = 'matching-post';
        const link = document.createElement('a'); link.href = entry.url;
        const title = document.createElement('h2'); title.textContent = entry.title;
        const snippet = document.createElement('p');
        const at = Math.max(0, entry.bodyText.indexOf(terms[0]) - 25);
        snippet.textContent = (at ? '…' : '') + entry.body.slice(at, at + 180) + '…';
        link.append(title, snippet); result.append(link); panel.append(result);
      }
    }
    input.addEventListener('input', function () { clearTimeout(timer); timer = setTimeout(update, 100); });
    clear.addEventListener('click', function () { input.value = ''; update(); input.focus(); });
    input.value = new URL(location.href).searchParams.get('s') || '';
    update();
  });
});

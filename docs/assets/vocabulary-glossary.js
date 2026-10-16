(function () {
  'use strict';
  window.$docsify = window.$docsify || {};
  window.$docsify.plugins = (window.$docsify.plugins || []).concat(function (hook) {
    hook.doneEach(function () {
      const query = document.getElementById('vocabulary-query');
      if (!query) return;
      const chapter = document.getElementById('vocabulary-chapter');
      const count = document.getElementById('vocabulary-count');
      const article = query.closest('.markdown-section');
      const sections = Array.from(article.querySelectorAll('table')).map(function (table) {
        const rows = Array.from(table.querySelectorAll('tbody tr')).map(function (row) {
          const cells = row.querySelectorAll('td');
          return {row: row, text: (cells[0].textContent + ' ' + cells[1].textContent).normalize('NFC').toLowerCase(),
            chapters: Array.from(cells[2].querySelectorAll('a')).map(a => a.textContent.trim())};
        });
        let heading = table.previousElementSibling;
        while (heading && heading.tagName !== 'H2') heading = heading.previousElementSibling;
        return {table: table, heading: heading, rows: rows};
      });
      function filter() {
        const words = query.value.normalize('NFC').toLowerCase().trim().split(/\s+/).filter(Boolean);
        let visible = 0;
        sections.forEach(function (section) {
          let matches = 0;
          section.rows.forEach(function (item) {
            const show = words.every(word => item.text.includes(word)) && (!chapter.value || item.chapters.includes(chapter.value));
            item.row.hidden = !show;
            if (show) matches++;
          });
          section.table.hidden = !matches;
          if (section.heading) section.heading.hidden = !matches;
          visible += matches;
        });
        count.textContent = visible + (visible === 1 ? ' entry' : ' entries') + (visible ? '' : ' — no matches');
      }
      query.addEventListener('input', filter);
      chapter.addEventListener('change', filter);
      filter();
    });
  });
})();

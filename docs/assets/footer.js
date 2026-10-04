(function () {
  window.$docsify.plugins = (window.$docsify.plugins || []).concat(function (hook) {
    hook.doneEach(function () {
      const section = document.querySelector('.markdown-section');
      if (section.querySelector('.site-footer')) return;
      const footer = document.createElement('footer');
      footer.className = 'site-footer';
      footer.innerHTML = 'An open-source digital edition · ' +
        '<a href="https://github.com/matjic/malayalam">Source on GitHub</a> · ' +
        '<a href="https://github.com/matjic/malayalam/blob/main/LICENSE.md">License</a>';
      section.append(footer);
    });
  });
}());

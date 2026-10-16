(function () {
  window.$docsify.plugins = (window.$docsify.plugins || []).concat(function (hook) {
    hook.doneEach(function () {
      const section = document.querySelector('.markdown-section');
      if (section.querySelector('.site-footer')) return;
      const footer = document.createElement('footer');
      footer.className = 'site-footer';
      const supplement = /^#\/practice(?:[-.?]|$)/.test(window.location.hash);
      const license = supplement
        ? 'https://creativecommons.org/licenses/by-sa/4.0/'
        : 'https://github.com/matjic/malayalam/blob/main/LICENSE.md';
      footer.innerHTML = 'An open-source digital edition · ' +
        '<a href="https://github.com/matjic/malayalam">Source on GitHub</a> · ' +
        '<a href="' + license + '">' + (supplement ? 'Supplement license' : 'License') + '</a>';
      section.append(footer);
    });
  });
}());

(function () {
  window.$docsify.plugins = (window.$docsify.plugins || []).concat(function (hook) {
    hook.mounted(function () {
      const button = document.querySelector('.sidebar-toggle');
      const sidebar = document.querySelector('.sidebar');
      const mobile = window.matchMedia('(max-width: 600px)');
      const label = document.createElement('strong');
      const backdrop = document.createElement('div');
      label.textContent = 'Menu';
      button.append(label);
      button.type = 'button';
      button.querySelector('.sidebar-toggle-button').setAttribute('aria-hidden', 'true');
      sidebar.id = 'site-navigation';
      sidebar.setAttribute('aria-label', 'Site navigation');
      button.setAttribute('aria-controls', sidebar.id);
      backdrop.className = 'sidebar-backdrop';
      backdrop.setAttribute('aria-hidden', 'true');
      document.body.append(backdrop);

      function isOpen() {
        return document.body.classList.contains('close') === mobile.matches;
      }
      function sync() {
        const open = isOpen();
        button.setAttribute('aria-expanded', String(open));
        button.setAttribute('aria-label', open ? 'Close navigation menu' : 'Open navigation menu');
        label.textContent = open ? 'Close menu' : 'Menu';
        sidebar.inert = !open;
      }
      function close() {
        document.body.classList.toggle('close', !mobile.matches);
        sync();
      }
      // Own the toggle so Docsify's initial viewport detection cannot go stale.
      button.addEventListener('click', function (event) {
        event.stopImmediatePropagation();
        document.body.classList.toggle('close');
        sync();
      }, true);
      sidebar.addEventListener('click', function (event) {
        event.stopPropagation();
        if (mobile.matches && event.target.closest('a[href]')) close();
      });
      backdrop.addEventListener('click', function (event) {
        event.stopPropagation();
        close();
        button.focus();
      });
      document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape' && isOpen()) {
          close();
          button.focus();
        }
      });
      mobile.addEventListener('change', function () {
        document.body.classList.remove('close');
        sync();
      });
      new MutationObserver(sync).observe(document.body, { attributes: true, attributeFilter: ['class'] });
      sync();
    });
  });
})();

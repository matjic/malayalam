(function () {
  window.$docsify.plugins = (window.$docsify.plugins || []).concat(function (hook) {
    hook.beforeEach(function (content) {
      document.querySelectorAll('.lesson-audio audio').forEach(function (audio) {
        audio.pause();
      });
      return content;
    });
    hook.doneEach(function () {
      const rowButtons = document.querySelectorAll('[data-row-audio-src]');
      function clearRowSelection() {
        rowButtons.forEach(function (button) { button.setAttribute('aria-pressed', 'false'); });
      }
      document.querySelectorAll('.lesson-audio').forEach(function (container) {
        const audio = container.querySelector('audio');
        audio.addEventListener('play', function () {
          document.querySelectorAll('audio').forEach(function (other) {
            if (other !== audio) other.pause();
          });
        });
        container.querySelectorAll('[data-audio-src]').forEach(function (button) {
          button.addEventListener('click', function () {
            clearRowSelection();
            const source = new URL(button.dataset.audioSrc, document.baseURI).href;
            if (audio.src !== source) {
              audio.src = source;
              audio.load();
            } else if (audio.readyState > 0) {
              audio.currentTime = 0;
            }
            container.querySelectorAll('[data-audio-src]').forEach(function (option) {
              option.setAttribute('aria-pressed', String(option === button));
            });
            // Calling play during the click keeps playback a user-initiated action.
            audio.play().catch(function () {
              // Native controls remain available if playback is blocked or fails.
            });
          });
        });
      });
      rowButtons.forEach(function (button) {
        button.addEventListener('click', function () {
          const audio = document.querySelector('[data-table-audio-player]');
          if (!audio) return;
          const source = new URL(button.dataset.rowAudioSrc, document.baseURI).href;
          if (audio.src !== source) { audio.src = source; audio.load(); }
          else if (audio.readyState > 0) audio.currentTime = 0;
          audio.setAttribute('aria-label', 'Selected recording: ' + button.dataset.audioLabel);
          clearRowSelection();
          button.setAttribute('aria-pressed', 'true');
          audio.closest('.lesson-audio').querySelectorAll('[data-audio-src]').forEach(function (other) {
            other.setAttribute('aria-pressed', 'false');
          });
          audio.play().catch(function () { /* Native controls remain available. */ });
        });
      });
    });
  });
})();

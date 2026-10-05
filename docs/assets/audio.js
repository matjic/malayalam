(function () {
  window.$docsify.plugins = (window.$docsify.plugins || []).concat(function (hook) {
    hook.beforeEach(function (content) {
      document.querySelectorAll('.lesson-audio audio').forEach(function (audio) {
        audio.pause();
      });
      return content;
    });
    hook.doneEach(function () {
      document.querySelectorAll('.lesson-audio').forEach(function (container) {
        const audio = container.querySelector('audio');
        audio.addEventListener('play', function () {
          document.querySelectorAll('audio').forEach(function (other) {
            if (other !== audio) other.pause();
          });
        });
        container.querySelectorAll('[data-audio-src]').forEach(function (button) {
          button.addEventListener('click', function () {
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
    });
  });
})();

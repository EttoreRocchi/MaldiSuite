(function () {
  'use strict';

  const navToggle = document.getElementById('nav-toggle');
  const navMenu = document.getElementById('nav-menu');

  if (navToggle && navMenu) {
    const setOpen = function (open) {
      navToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      navMenu.classList.toggle('is-open', open);
    };

    navToggle.addEventListener('click', function () {
      const isOpen = navToggle.getAttribute('aria-expanded') === 'true';
      setOpen(!isOpen);
    });

    navMenu.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', function () { setOpen(false); });
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && navToggle.getAttribute('aria-expanded') === 'true') {
        setOpen(false);
        navToggle.focus();
      }
    });

    const mql = window.matchMedia('(min-width: 769px)');
    const onMqlChange = function () {
      if (mql.matches) setOpen(false);
    };
    if (mql.addEventListener) mql.addEventListener('change', onMqlChange);
    else if (mql.addListener) mql.addListener(onMqlChange);
  }

  const copyToClipboard = function (text) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text);
    }
    return new Promise(function (resolve, reject) {
      const ta = document.createElement('textarea');
      ta.value = text;
      ta.setAttribute('readonly', '');
      ta.style.position = 'absolute';
      ta.style.left = '-9999px';
      document.body.appendChild(ta);
      ta.select();
      try {
        document.execCommand('copy') ? resolve() : reject();
      } catch (err) {
        reject(err);
      } finally {
        document.body.removeChild(ta);
      }
    });
  };

  const status = document.getElementById('copy-status');

  const announce = function (message) {
    if (status) status.textContent = message;
  };

  document.querySelectorAll('.copy-btn').forEach(function (btn) {
    const original = btn.textContent;
    const source = btn.parentElement ? btn.parentElement.querySelector('code') : null;

    btn.addEventListener('click', function () {
      const text = (btn.getAttribute('data-copy') || (source ? source.textContent : '')).trim();
      if (!text) return;
      copyToClipboard(text).then(function () {
        btn.textContent = 'Copied';
        btn.classList.add('is-copied');
        announce(text + ' copied to clipboard');
        setTimeout(function () {
          btn.textContent = original;
          btn.classList.remove('is-copied');
        }, 1500);
      }).catch(function () {
        btn.textContent = 'Error';
        announce('Copy failed, select the command manually');
        setTimeout(function () { btn.textContent = original; }, 1500);
      });
    });
  });

})();

/* MaldiSuite - Landing Page Scripts */

(function () {
  'use strict';

  // ---------- Smooth Scroll for Anchor Links ----------
  // Browser handles most of it via scroll-behavior: smooth in CSS.
  // This fallback ensures old browsers also scroll nicely.
  document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
    anchor.addEventListener('click', function (e) {
      const targetId = this.getAttribute('href');
      if (targetId === '#' || targetId.length < 2) return;

      const target = document.querySelector(targetId);
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

})();

/* Progressive motion: the complete site stays readable without JavaScript. */
(() => {
  const root = document.documentElement;
  const toggle = document.querySelector('[data-motion-toggle]');
  const preference = window.matchMedia('(prefers-reduced-motion: reduce)');
  const targets = Array.from(document.querySelectorAll('.reveal'));
  let paused = preference.matches;
  let observer;
  const showEverything = () => targets.forEach(element => element.classList.add('is-visible'));
  function syncMotion() {
    root.classList.toggle('motion-paused', paused);
    if (toggle) {
      toggle.hidden = false;
      toggle.disabled = preference.matches;
      toggle.textContent = preference.matches ? 'Reduced motion' : paused ? 'Play motion' : 'Pause motion';
      toggle.setAttribute('aria-pressed', String(paused));
    }
    if (paused) showEverything();
  }
  try {
    if (!preference.matches && 'IntersectionObserver' in window) {
      observer = new window.IntersectionObserver(entries => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible');
            observer.unobserve(entry.target);
          }
        });
      }, { threshold: 0.08 });
      targets.forEach(element => observer.observe(element));
      root.classList.add('reveal-ready');
    } else showEverything();
    root.classList.add('motion-ready');
    syncMotion();
    toggle?.addEventListener('click', () => {
      if (preference.matches) return;
      paused = !paused;
      syncMotion();
    });
    preference.addEventListener?.('change', event => {
      paused = event.matches;
      syncMotion();
    });
    window.addEventListener('beforeprint', showEverything);
    document.addEventListener('focusin', event => {
      event.target.closest?.('.reveal')?.classList.add('is-visible');
    });
  } catch (_) {
    root.classList.remove('reveal-ready', 'motion-ready');
    showEverything();
    if (toggle) toggle.hidden = true;
  }
})();

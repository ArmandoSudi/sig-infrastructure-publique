(function () {
  const toggle = document.querySelector('[data-menu-toggle]');
  const nav = document.querySelector('[data-main-nav]');

  if (toggle && nav) {
    toggle.addEventListener('click', () => {
      nav.classList.toggle('show');
    });
  }

  const cards = document.querySelectorAll('.panel, .stat-card');
  if ('IntersectionObserver' in window && cards.length > 0) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.style.transform = 'translateY(0)';
            entry.target.style.opacity = '1';
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.1 }
    );

    cards.forEach((card, idx) => {
      card.style.opacity = '0';
      card.style.transform = 'translateY(10px)';
      card.style.transition = `all 420ms ease ${idx * 28}ms`;
      observer.observe(card);
    });
  }
})();

// OBSIDIAN ARMORY — shared behaviour

document.addEventListener('DOMContentLoaded', () => {

  // ---- loader ----
  const loader = document.getElementById('loader');
  if (loader){
    window.addEventListener('load', () => {
      setTimeout(() => loader.classList.add('hide'), 550);
    });
    // fallback in case load already fired
    setTimeout(() => loader.classList.add('hide'), 2200);
  }

  // ---- scroll reveal ----
  const revealEls = document.querySelectorAll('.reveal');
  const io = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting){
        e.target.classList.add('in');
        io.unobserve(e.target);
      }
    });
  }, { threshold: 0.15 });
  revealEls.forEach(el => io.observe(el));

  // ---- tilt on pointer move (desktop only) ----
  const tilts = document.querySelectorAll('.tilt-wrap');
  if (window.matchMedia('(hover:hover)').matches){
    tilts.forEach(wrap => {
      const card = wrap.querySelector('.tilt');
      if(!card) return;
      wrap.addEventListener('mousemove', (e) => {
        const r = wrap.getBoundingClientRect();
        const x = (e.clientX - r.left) / r.width - 0.5;
        const y = (e.clientY - r.top) / r.height - 0.5;
        card.style.transform = `rotateY(${x*14}deg) rotateX(${-y*14}deg) translateZ(10px)`;
      });
      wrap.addEventListener('mouseleave', () => {
        card.style.transform = `rotateY(0deg) rotateX(0deg) translateZ(0px)`;
      });
    });
  }

  // ---- ambient parallax diamonds ----
  const diamondField = document.querySelector('.diamond-field');
  if (diamondField){
    window.addEventListener('scroll', () => {
      const y = window.scrollY * 0.06;
      diamondField.style.transform = `translateY(${y}px)`;
    }, { passive: true });
  }

  // ---- section rail (index page) ----
  const railDots = document.querySelectorAll('.rail span');
  if (railDots.length){
    const sections = document.querySelectorAll('[data-section]');
    const railIo = new IntersectionObserver((entries) => {
      entries.forEach(e => {
        if (e.isIntersecting){
          const id = e.target.getAttribute('data-section');
          railDots.forEach(d => d.classList.toggle('active', d.dataset.target === id));
        }
      });
    }, { threshold: 0.5 });
    sections.forEach(s => railIo.observe(s));
  }

});
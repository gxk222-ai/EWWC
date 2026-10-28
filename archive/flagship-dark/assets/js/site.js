/* eWorldwide flagship: interactions and motion.
   Content is fully visible without JS; motion classes are only added once GSAP has loaded. */
(function () {
  var root = document.documentElement;
  var MOTION_KEY = 'ewwc-reduce-motion';
  var mqReduce = window.matchMedia('(prefers-reduced-motion: reduce)');
  var mqFine = window.matchMedia('(pointer: fine)');

  function storedReduce() {
    try { return localStorage.getItem(MOTION_KEY) === '1'; } catch (e) { return false; }
  }
  if (storedReduce()) root.classList.add('reduce-motion');
  var reduce = mqReduce.matches || storedReduce();
  var hasGsap = !!(window.gsap && window.ScrollTrigger);
  var motion = hasGsap && !reduce;

  var yearEl = document.getElementById('year');
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  /* ---------- Smooth scroll ---------- */
  var lenis = null;
  if (motion) {
    gsap.registerPlugin(ScrollTrigger);
    root.classList.add('js-motion');
    if (window.Lenis && !('ontouchstart' in window)) {
      lenis = new Lenis({ lerp: 0.08, wheelMultiplier: 0.9 });
      lenis.on('scroll', ScrollTrigger.update);
      gsap.ticker.add(function (t) { lenis.raf(t * 1000); });
      gsap.ticker.lagSmoothing(0);
    }
  }

  function scrollToTarget(target) {
    if (lenis) lenis.scrollTo(target, { offset: 0, duration: 1.4 });
    else target.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth' });
    if (!target.hasAttribute('tabindex')) target.setAttribute('tabindex', '-1');
    target.focus({ preventScroll: true });
  }
  document.addEventListener('click', function (e) {
    var a = e.target.closest('a[href^="#"]');
    if (!a) return;
    var id = a.getAttribute('href');
    var target = id.length > 1 ? document.querySelector(id) : null;
    if (!target) return;
    e.preventDefault();
    closeMenu();
    scrollToTarget(target);
  });

  /* ---------- Header: glass after 80px, hide on scroll down ---------- */
  var header = document.getElementById('header');
  var lastY = window.scrollY;
  function onScroll() {
    var y = window.scrollY;
    header.classList.toggle('is-glass', y > 80);
    if (!root.classList.contains('menu-open')) header.classList.toggle('is-hidden', y > 400 && y > lastY);
    lastY = y;
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* ---------- Overlay menu ---------- */
  var toggle = document.getElementById('menuToggle');
  var overlay = document.getElementById('overlay');
  var ctx = document.getElementById('overlayCtx');
  var ctxDefault = ctx ? ctx.textContent : '';
  function openMenu() {
    root.classList.add('menu-open');
    toggle.setAttribute('aria-expanded', 'true');
    overlay.setAttribute('aria-hidden', 'false');
    header.classList.remove('is-hidden');
    if (lenis) lenis.stop();
    var first = overlay.querySelector('a');
    if (first) setTimeout(function () { first.focus(); }, 50);
  }
  function closeMenu() {
    if (!root.classList.contains('menu-open')) return;
    root.classList.remove('menu-open');
    toggle.setAttribute('aria-expanded', 'false');
    overlay.setAttribute('aria-hidden', 'true');
    if (lenis) lenis.start();
    toggle.focus({ preventScroll: true });
  }
  toggle.addEventListener('click', function () {
    root.classList.contains('menu-open') ? closeMenu() : openMenu();
  });
  document.addEventListener('keydown', function (e) {
    if (!root.classList.contains('menu-open')) return;
    if (e.key === 'Escape') { closeMenu(); return; }
    if (e.key === 'Tab') {
      var items = [toggle].concat(Array.prototype.slice.call(overlay.querySelectorAll('a')));
      var i = items.indexOf(document.activeElement);
      if (e.shiftKey && i <= 0) { e.preventDefault(); items[items.length - 1].focus(); }
      else if (!e.shiftKey && i === items.length - 1) { e.preventDefault(); items[0].focus(); }
    }
  });
  overlay.querySelectorAll('.overlay-list a').forEach(function (a) {
    function show() { if (ctx) ctx.textContent = a.dataset.ctx || ctxDefault; }
    a.addEventListener('mouseenter', show);
    a.addEventListener('focus', show);
  });

  /* ---------- Platform tabs and nodes ---------- */
  var tabs = Array.prototype.slice.call(document.querySelectorAll('[role="tab"]'));
  function selectTab(tab) {
    tabs.forEach(function (t) {
      var on = t === tab;
      t.classList.toggle('is-active', on);
      t.setAttribute('aria-selected', on);
      t.tabIndex = on ? 0 : -1;
      var panel = document.getElementById(t.getAttribute('aria-controls'));
      panel.hidden = !on;
      panel.classList.toggle('is-active', on);
      if (on) drawSvgs(panel.querySelectorAll('svg.draw'), true);
    });
  }
  tabs.forEach(function (t, i) {
    t.addEventListener('click', function () { selectTab(t); });
    t.addEventListener('keydown', function (e) {
      var d = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0;
      if (!d) return;
      var next = tabs[(i + d + tabs.length) % tabs.length];
      next.focus(); selectTab(next);
    });
  });
  document.querySelectorAll('.panel').forEach(function (panel) {
    var nodes = panel.querySelectorAll('.node');
    var sch = panel.querySelectorAll('.sch-node');
    function activate(idx) {
      nodes.forEach(function (n) { n.classList.toggle('is-active', n.dataset.node === idx); n.setAttribute('aria-expanded', n.dataset.node === idx); });
      sch.forEach(function (s) { s.classList.toggle('is-active', s.dataset.node === idx); });
    }
    nodes.forEach(function (n) {
      ['mouseenter', 'focus', 'click'].forEach(function (ev) { n.addEventListener(ev, function () { activate(n.dataset.node); }); });
    });
    activate('0');
  });

  /* ---------- Governance rings follow the pillar in view ---------- */
  var pillars = document.querySelectorAll('.pillar');
  var rings = document.querySelectorAll('.rings [data-ring]');
  function setRing(idx) {
    pillars.forEach(function (p) { p.classList.toggle('is-active', p.dataset.ring === idx); });
    rings.forEach(function (r) { r.classList.toggle('is-active', r.dataset.ring === idx); });
  }
  setRing('0');
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) setRing(en.target.dataset.ring); });
    }, { rootMargin: '-45% 0px -45% 0px' });
    pillars.forEach(function (p) { io.observe(p); });
  }

  /* ---------- Office clocks ---------- */
  var clocks = document.querySelectorAll('[data-tz]');
  function tick() {
    var now = new Date();
    clocks.forEach(function (c) {
      try {
        c.textContent = new Intl.DateTimeFormat('en-GB', { hour: '2-digit', minute: '2-digit', hour12: false, timeZone: c.dataset.tz }).format(now);
      } catch (e) { c.textContent = '--:--'; }
    });
  }
  tick();
  setInterval(tick, 30000);

  /* ---------- Concierge form (local preview: nothing is sent) ---------- */
  var form = document.getElementById('portal');
  if (form) {
    var err = document.getElementById('formError');
    var ok = document.getElementById('formSuccess');
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var invalid = [];
      form.querySelectorAll('[required]').forEach(function (f) {
        var bad = f.type === 'checkbox' ? !f.checked : !f.value.trim() || (f.type === 'email' && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(f.value));
        f.classList.toggle('is-invalid', bad);
        f.setAttribute('aria-invalid', bad);
        if (bad) invalid.push(f);
      });
      if (invalid.length) {
        err.textContent = 'Please complete the highlighted fields.';
        err.hidden = false;
        invalid[0].focus();
        return;
      }
      err.hidden = true;
      document.getElementById('successRegion').textContent = form.region.value;
      form.querySelectorAll('.field, .check, button[type="submit"]').forEach(function (el) { el.hidden = true; });
      ok.hidden = false;
    });
  }

  /* ---------- Reduce-motion toggle ---------- */
  var mt = document.getElementById('motionToggle');
  if (mt) {
    mt.setAttribute('aria-pressed', storedReduce());
    mt.addEventListener('click', function () {
      var on = !storedReduce();
      try { localStorage.setItem(MOTION_KEY, on ? '1' : '0'); } catch (e) {}
      location.reload();
    });
  }

  /* ---------- SVG line drawing ---------- */
  function drawSvgs(list, immediate) {
    Array.prototype.forEach.call(list, function (svg) {
      svg.style.visibility = 'visible';
      if (!motion) return;
      var shapes = svg.querySelectorAll('path, circle, rect');
      shapes.forEach(function (s) {
        var len = 0;
        try { len = s.getTotalLength(); } catch (e) {}
        if (!len) return;
        s.style.strokeDasharray = len;
        s.style.strokeDashoffset = len;
      });
      var tween = { strokeDashoffset: 0, duration: 2, ease: 'power2.inOut', stagger: 0.08 };
      if (immediate) gsap.to(shapes, tween);
      else gsap.to(shapes, Object.assign(tween, { scrollTrigger: { trigger: svg, start: 'top 85%', once: true } }));
    });
  }

  if (!motion) {
    drawSvgs(document.querySelectorAll('svg.draw'));
    return;
  }

  /* ========== Motion-only below ========== */

  // Initial draw for visible SVGs (hidden tab panels draw when selected)
  drawSvgs(Array.prototype.filter.call(document.querySelectorAll('svg.draw'), function (s) { return !s.closest('[hidden]'); }));

  // Headline line reveals
  document.querySelectorAll('.split').forEach(function (el) {
    var lines = el.querySelectorAll('.line > span');
    var inHero = !!el.closest('.hero');
    gsap.to(lines, {
      y: 0, duration: 1.2, ease: 'expo.out', stagger: 0.08, delay: inHero ? 0.2 : 0,
      scrollTrigger: inHero ? null : { trigger: el, start: 'top 85%', once: true }
    });
  });
  // Fades (body copy fades only, no movement)
  document.querySelectorAll('.reveal-fade').forEach(function (el) {
    var inHero = !!el.closest('.hero');
    gsap.to(el, { opacity: 1, duration: 1.2, ease: 'power2.out', delay: inHero ? 0.7 : 0,
      scrollTrigger: inHero ? null : { trigger: el, start: 'top 90%', once: true } });
  });
  document.querySelectorAll('.reveal-up').forEach(function (el) {
    gsap.fromTo(el, { opacity: 0, y: 24 }, { opacity: 1, y: 0, duration: 1.1, ease: 'expo.out',
      scrollTrigger: { trigger: el, start: 'top 90%', once: true } });
  });

  // Pinned horizontal case studies (desktop and tablet)
  var mm = gsap.matchMedia();
  mm.add('(min-width: 768px)', function () {
    var pin = document.getElementById('casesPin');
    var track = document.getElementById('casesTrack');
    var count = document.getElementById('caseCount');
    var bar = document.getElementById('caseBar');
    var total = track.children.length;
    function dist() { return Math.max(0, track.scrollWidth - window.innerWidth); }
    gsap.to(track, {
      x: function () { return -dist(); },
      ease: 'none',
      scrollTrigger: {
        trigger: pin, start: 'top top', end: function () { return '+=' + dist(); },
        pin: true, scrub: 1, invalidateOnRefresh: true,
        onUpdate: function (self) {
          var idx = Math.min(total, Math.floor(self.progress * total) + 1);
          count.textContent = ('0' + idx).slice(-2) + ' / ' + ('0' + total).slice(-2);
          bar.style.transform = 'scaleX(' + Math.max(1 / total, self.progress) + ')';
        }
      }
    });
  });

  // Fonts change line lengths; refresh trigger positions once they load
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(function () { ScrollTrigger.refresh(); });

  /* ---------- Fine-pointer extras: magnetic buttons and custom cursor ---------- */
  if (!mqFine.matches) return;

  document.querySelectorAll('.magnetic').forEach(function (btn) {
    var label = btn.querySelector('span');
    var xTo = gsap.quickTo(btn, 'x', { duration: 0.6, ease: 'elastic.out(1, 0.6)' });
    var yTo = gsap.quickTo(btn, 'y', { duration: 0.6, ease: 'elastic.out(1, 0.6)' });
    var lxTo = label && gsap.quickTo(label, 'x', { duration: 0.6, ease: 'elastic.out(1, 0.6)' });
    var lyTo = label && gsap.quickTo(label, 'y', { duration: 0.6, ease: 'elastic.out(1, 0.6)' });
    var RADIUS = 90, MAX = 8;
    window.addEventListener('pointermove', function (e) {
      var r = btn.getBoundingClientRect();
      var cx = r.left + r.width / 2, cy = r.top + r.height / 2;
      var dx = e.clientX - cx, dy = e.clientY - cy;
      var near = Math.abs(dx) < r.width / 2 + RADIUS && Math.abs(dy) < r.height / 2 + RADIUS;
      var mx = near ? Math.max(-MAX, Math.min(MAX, dx * 0.2)) : 0;
      var my = near ? Math.max(-MAX, Math.min(MAX, dy * 0.3)) : 0;
      xTo(mx); yTo(my);
      if (label) { lxTo(mx * 0.4); lyTo(my * 0.4); }
    }, { passive: true });
  });

  root.classList.add('has-cursor');
  var dot = document.querySelector('.cursor-dot');
  var ring = document.querySelector('.cursor-ring');
  var ringLabel = document.querySelector('.cursor-label');
  var mx = -100, my = -100, rx = -100, ry = -100;
  window.addEventListener('pointermove', function (e) {
    mx = e.clientX; my = e.clientY;
    dot.style.transform = 'translate(' + mx + 'px,' + my + 'px)';
  }, { passive: true });
  gsap.ticker.add(function () {
    rx += (mx - rx) * 0.15; ry += (my - ry) * 0.15;
    ring.style.transform = 'translate(' + rx + 'px,' + ry + 'px)';
  });
  document.addEventListener('pointerover', function (e) {
    var t = e.target.closest('[data-cursor], a, button');
    var text = t && t.dataset.cursor;
    ring.classList.toggle('is-active', !!(t && (text || t.matches('a, button'))));
    ringLabel.textContent = text || '';
  });
})();

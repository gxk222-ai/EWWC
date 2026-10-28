/* E Worldwide Consulting: progressive enhancement. Every page works without this script. */
(function () {
  'use strict';
  var root = document.documentElement;
  root.classList.add('js');

  /* ---------- Header shadow on scroll ---------- */
  var header = document.querySelector('[data-header]');
  function onScroll() { header.classList.toggle('is-scrolled', window.scrollY > 8); }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* ---------- Mobile navigation ---------- */
  var navToggle = document.querySelector('[data-nav-toggle]');
  var nav = document.getElementById('site-nav');
  function setNav(open) {
    navToggle.setAttribute('aria-expanded', String(open));
    document.body.classList.toggle('nav-open', open);
  }
  navToggle.addEventListener('click', function () {
    setNav(navToggle.getAttribute('aria-expanded') !== 'true');
  });

  /* ---------- Dropdown menus ---------- */
  var subToggles = Array.prototype.slice.call(document.querySelectorAll('.nav-sub-toggle'));
  function closeSubs(except) {
    subToggles.forEach(function (t) { if (t !== except) t.setAttribute('aria-expanded', 'false'); });
  }
  subToggles.forEach(function (t) {
    t.addEventListener('click', function (e) {
      e.stopPropagation();
      var open = t.getAttribute('aria-expanded') !== 'true';
      closeSubs(t);
      t.setAttribute('aria-expanded', String(open));
    });
  });
  document.addEventListener('click', function (e) {
    if (!e.target.closest('.has-sub')) closeSubs();
  });
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    var openSub = subToggles.filter(function (t) { return t.getAttribute('aria-expanded') === 'true'; })[0];
    if (openSub) { closeSubs(); openSub.focus(); return; }
    if (document.body.classList.contains('nav-open')) { setNav(false); navToggle.focus(); }
  });
  nav.addEventListener('focusout', function (e) {
    var item = e.target.closest('.has-sub');
    if (item && !item.contains(e.relatedTarget)) {
      var t = item.querySelector('.nav-sub-toggle');
      if (t) t.setAttribute('aria-expanded', 'false');
    }
  });

  /* ---------- Reveal on scroll ---------- */
  var reveals = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add('is-visible'); io.unobserve(en.target); }
      });
    }, { rootMargin: '0px 0px -8% 0px' });
    reveals.forEach(function (el, i) {
      el.style.transitionDelay = (i % 4) * 60 + 'ms';
      io.observe(el);
    });
  } else {
    reveals.forEach(function (el) { el.classList.add('is-visible'); });
  }

  /* ---------- Case study region filter ---------- */
  var filter = document.querySelector('[data-filter]');
  if (filter) {
    var buttons = filter.querySelectorAll('button');
    filter.addEventListener('click', function (e) {
      var btn = e.target.closest('button');
      if (!btn) return;
      var value = btn.getAttribute('data-filter-value');
      buttons.forEach(function (b) { b.setAttribute('aria-pressed', String(b === btn)); });
      document.querySelectorAll('[data-filter-target] [data-region]').forEach(function (card) {
        card.hidden = value !== 'all' && card.getAttribute('data-region') !== value;
      });
    });
  }

  /* ---------- Contact form ---------- */
  var form = document.querySelector('[data-contact-form]');
  if (!form) return;
  var success = document.querySelector('[data-form-success]');
  var errorBox = document.querySelector('[data-form-error]');
  var errorText = document.querySelector('[data-form-error-text]');
  var submit = form.querySelector('[data-submit]');
  var started = form.querySelector('[data-started]');
  started.value = String(Date.now());

  // Result of a no-JS submission redirected back by the server
  var params = new URLSearchParams(location.search);
  if (params.get('status') === 'sent') showSuccess();
  if (params.get('status') === 'error') showError('We could not send your message. Please check the form and try again.');

  var messages = {
    name: 'Enter your full name.',
    email: 'Enter a valid business email address, like name@company.com.',
    company: 'Enter your company name.',
    region: 'Select your country or region.',
    service: 'Select the service you are interested in.',
    message: 'Describe your project in at least 20 characters.',
    consent: 'Please agree to the privacy notice so we can respond.'
  };

  function setFieldError(field, msg) {
    var err = document.getElementById(field.id + '-error');
    field.setAttribute('aria-invalid', msg ? 'true' : 'false');
    if (err) { err.textContent = msg || ''; err.hidden = !msg; }
  }
  function validateField(field) {
    var valid = field.type === 'checkbox' ? field.checked : field.checkValidity() && field.value.trim() !== '';
    if (field.type === 'email' && valid) valid = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(field.value.trim());
    setFieldError(field, valid ? '' : messages[field.name]);
    return valid;
  }
  form.querySelectorAll('[required]').forEach(function (f) {
    f.addEventListener('blur', function () { if (f.getAttribute('aria-invalid') === 'true' || f.value) validateField(f); });
    f.addEventListener('change', function () { if (f.getAttribute('aria-invalid') === 'true') validateField(f); });
  });

  function showSuccess() {
    form.hidden = true;
    errorBox.hidden = true;
    success.hidden = false;
    success.focus();
  }
  function showError(msg) {
    errorText.textContent = msg;
    errorBox.hidden = false;
    errorBox.focus();
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var invalid = [];
    form.querySelectorAll('[required]').forEach(function (f) { if (!validateField(f)) invalid.push(f); });
    if (invalid.length) {
      showError(invalid.length === 1 ? '1 field needs your attention.' : invalid.length + ' fields need your attention.');
      invalid[0].focus();
      return;
    }
    errorBox.hidden = true;
    submit.disabled = true;
    submit.textContent = 'Sending…';

    var data = {};
    new FormData(form).forEach(function (v, k) { data[k] = v; });
    fetch(form.action, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body: JSON.stringify(data)
    }).then(function (res) {
      return res.json().catch(function () { return {}; }).then(function (body) { return { ok: res.ok, body: body }; });
    }).then(function (r) {
      if (r.ok) { showSuccess(); return; }
      var errs = (r.body && r.body.errors) || {};
      Object.keys(errs).forEach(function (name) {
        var f = form.elements[name];
        if (f) setFieldError(f, errs[name]);
      });
      showError((r.body && r.body.message) || 'We could not send your message. Please try again.');
    }).catch(function () {
      showError('We could not reach the server. Please check your connection and try again.');
    }).then(function () {
      submit.disabled = false;
      submit.textContent = 'Discuss Your Project';
    });
  });
})();

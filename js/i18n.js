/**
 * AlphaCouncil i18n runtime (Phase O1/O4).
 *
 * Self-bootstrapping: on load it auto-tags the shared nav (.app-nav-links a) by its
 * English text, auto-wires any .lang-toggle (EN/AR) buttons, sets <html lang>+dir
 * ('ar' ⇒ rtl), and honors the signed-in user's preferred_language. So a page only has
 * to include this script — no per-page wiring. Pages add their own strings with
 * data-i18n / data-i18n-attr and AC_I18N.add({...}).
 *
 * Translates:
 *   data-i18n="key"                      -> textContent
 *   data-i18n-attr="placeholder:key,..." -> the named attribute(s)
 *
 * Language: saved localStorage('ac.lang') → user's preferred_language → 'en'.
 * User-initiated switches persist to localStorage AND best-effort PUT /api/account/profile.
 * Fires 'ac:langchange' so pages can re-render dynamic content.
 *
 * Additive + opt-in: untagged pages are unaffected; EN (dir=ltr) is the default, so
 * nothing changes for a user who hasn't chosen Arabic.
 */
(function (global) {
  'use strict';
  var STORAGE_KEY = 'ac.lang';

  function forEach(list, fn) { Array.prototype.forEach.call(list, fn); }

  // Shared chrome dictionary. EN is the source of truth; AR is the human translation.
  var DICT = {
    'nav.dashboard':       { en: 'Dashboard',        ar: 'لوحة التحكم' },
    'nav.portfolio':       { en: 'Portfolio',        ar: 'المحفظة' },
    'nav.markets':         { en: 'Markets',          ar: 'الأسواق' },
    'nav.screener':        { en: 'Screener',         ar: 'الفرز' },
    'nav.news':            { en: 'News',             ar: 'الأخبار' },
    'nav.watchlist':       { en: 'Watchlist',        ar: 'قائمة المتابعة' },
    'nav.alerts':          { en: 'Alerts',           ar: 'التنبيهات' },
    'nav.settings':        { en: 'Settings',         ar: 'الإعدادات' },
    'nav.compare':         { en: 'Compare',          ar: 'المقارنة' },
    'nav.council':         { en: 'Council',          ar: 'المجلس' },
    'nav.scenarios':       { en: 'Scenarios',        ar: 'السيناريوهات' },
    'action.add_holding':  { en: 'Add Holding',      ar: 'إضافة مركز' },
    'action.sign_out':     { en: 'Sign out',         ar: 'تسجيل الخروج' },
    'action.save':         { en: 'Save',             ar: 'حفظ' },
    'action.cancel':       { en: 'Cancel',           ar: 'إلغاء' },
    'action.upgrade':      { en: 'Upgrade',          ar: 'الترقية' },
    'common.loading':      { en: 'Loading…',         ar: 'جارٍ التحميل…' },
    'common.search':       { en: 'Search',           ar: 'بحث' },
    'a11y.toggle_adviser': { en: 'Toggle AI Adviser', ar: 'إظهار/إخفاء المستشار الذكي' },
    'a11y.notifications':  { en: 'Notifications',     ar: 'الإشعارات' }
  };

  var current = 'en';

  function t(key, lang) {
    var l = lang || current;
    var entry = DICT[key];
    if (!entry) return null;
    return entry[l] != null ? entry[l] : entry.en;
  }

  function _applyNode(node) {
    var key = node.getAttribute('data-i18n');
    if (key) { var v = t(key); if (v != null) node.textContent = v; }
    var attrSpec = node.getAttribute('data-i18n-attr');
    if (attrSpec) {
      attrSpec.split(',').forEach(function (pair) {
        var bits = pair.split(':');
        if (bits.length === 2) { var av = t(bits[1].trim()); if (av != null) node.setAttribute(bits[0].trim(), av); }
      });
    }
  }

  function apply(lang) {
    if (lang) current = (lang === 'ar' ? 'ar' : 'en');
    forEach(document.querySelectorAll('[data-i18n],[data-i18n-attr]'), _applyNode);
    var html = document.documentElement;
    html.setAttribute('lang', current);
    html.setAttribute('dir', current === 'ar' ? 'rtl' : 'ltr');
    syncToggles(current);
    try { localStorage.setItem(STORAGE_KEY, current); } catch (e) {}
    try { global.dispatchEvent(new CustomEvent('ac:langchange', { detail: { lang: current } })); } catch (e) {}
  }

  // User-initiated switch: apply + persist to the account (best-effort) for signed-in users.
  function set(lang, opts) {
    apply(lang);
    if (!(opts && opts.noPersist) && global.API && API.updateProfile) {
      try { API.updateProfile({ preferred_language: current }).catch(function () {}); } catch (e) {}
    }
  }

  function toggle() { set(current === 'ar' ? 'en' : 'ar'); }

  function init(userLang) {
    var saved = null; try { saved = localStorage.getItem(STORAGE_KEY); } catch (e) {}
    var lang = saved || (userLang === 'ar' ? 'ar' : (userLang === 'en' ? 'en' : null)) || 'en';
    apply(lang); // init never re-persists to the server
  }

  // ── Auto-bootstrap: tag the shared nav by text, wire the toggle, resolve language ──
  function autoTagNav() {
    var rev = {};
    for (var k in DICT) { if (k.indexOf('nav.') === 0) rev[DICT[k].en.toLowerCase()] = k; }
    forEach(document.querySelectorAll('.app-nav-links a'), function (a) {
      if (a.getAttribute('data-i18n')) return;
      var key = rev[(a.textContent || '').trim().toLowerCase()];
      if (key) a.setAttribute('data-i18n', key);
    });
  }

  function syncToggles(lang) {
    forEach(document.querySelectorAll('.lang-toggle button[data-lang]'), function (b) {
      b.classList.toggle('active', b.getAttribute('data-lang') === lang);
    });
  }

  function autoWireToggle() {
    forEach(document.querySelectorAll('.lang-toggle'), function (box) {
      if (box.__acWired) return; box.__acWired = true;
      forEach(box.querySelectorAll('button'), function (b) {
        if (!b.getAttribute('data-lang')) {
          var x = (b.textContent || '').trim().toLowerCase();
          if (x === 'en' || x === 'english') b.setAttribute('data-lang', 'en');
          else if (x === 'ar' || x === 'العربية' || x === 'عربي') b.setAttribute('data-lang', 'ar');
        }
      });
      box.addEventListener('click', function (e) {
        var b = e.target.closest('button[data-lang]'); if (b) set(b.getAttribute('data-lang'));
      });
    });
  }

  function bootstrap() {
    autoTagNav();
    autoWireToggle();
    var saved = null; try { saved = localStorage.getItem(STORAGE_KEY); } catch (e) {}
    if (saved) {
      apply(saved);
    } else {
      apply('en'); // default until the server answers
      if (global.API && API.me) {
        API.me().then(function (u) { if (u && u.preferred_language) apply(u.preferred_language); }).catch(function () {});
      }
    }
  }

  global.AC_I18N = {
    t: t, apply: apply, set: set, toggle: toggle, init: init, retag: autoTagNav,
    get lang() { return current; },
    dict: DICT,
    add: function (extra) { for (var k in extra) if (Object.prototype.hasOwnProperty.call(extra, k)) DICT[k] = extra[k]; }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bootstrap);
  } else {
    bootstrap();
  }
})(window);

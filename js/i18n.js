/**
 * AlphaCouncil i18n runtime (Phase O1).
 *
 * Translates any element that carries:
 *   data-i18n="key"                        -> sets textContent
 *   data-i18n-attr="placeholder:key,..."   -> sets the named attribute(s) (placeholder/title/aria-label/…)
 *
 * Language resolution order: saved localStorage('ac.lang') → the signed-in user's
 * preferred_language (passed to AC_I18N.init) → 'en'. apply() swaps all tagged nodes,
 * sets <html lang> + dir ('ar' ⇒ rtl), persists the choice (localStorage + best-effort
 * PUT /api/account/profile when signed in), and dispatches 'ac:langchange' so pages can
 * re-render dynamic content in the new language.
 *
 * Opt-in: pages include this script and tag strings. Untagged pages are unaffected, so
 * this is safe to add site-wide before every page is fully tagged.
 */
(function (global) {
  'use strict';
  var STORAGE_KEY = 'ac.lang';

  // Shared chrome dictionary. EN is the source of truth; AR is the human translation.
  // Per-page strings are merged in via AC_I18N.add({ ... }) from each page.
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
    'action.add_holding':  { en: 'Add Holding',      ar: 'إضافة مركز' },
    'action.sign_out':     { en: 'Sign out',         ar: 'تسجيل الخروج' },
    'action.save':         { en: 'Save',             ar: 'حفظ' },
    'action.cancel':       { en: 'Cancel',           ar: 'إلغاء' },
    'action.upgrade':      { en: 'Upgrade',          ar: 'الترقية' },
    'common.loading':      { en: 'Loading…',         ar: 'جارٍ التحميل…' },
    'common.search':       { en: 'Search',           ar: 'بحث' },
    'a11y.toggle_adviser': { en: 'Toggle AI Adviser', ar: 'إظهار/إخفاء المستشار الذكي' },
    'a11y.notifications':  { en: 'Notifications',     ar: 'الإشعارات' },
    // The language toggle shows the language you'd switch TO.
    'lang.switch':         { en: 'العربية',          ar: 'English' }
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
    if (key) {
      var v = t(key);
      if (v != null) node.textContent = v;
    }
    var attrSpec = node.getAttribute('data-i18n-attr');
    if (attrSpec) {
      attrSpec.split(',').forEach(function (pair) {
        var bits = pair.split(':');
        if (bits.length === 2) {
          var av = t(bits[1].trim());
          if (av != null) node.setAttribute(bits[0].trim(), av);
        }
      });
    }
  }

  function apply(lang) {
    if (lang) current = (lang === 'ar' ? 'ar' : 'en');
    var nodes = document.querySelectorAll('[data-i18n],[data-i18n-attr]');
    Array.prototype.forEach.call(nodes, _applyNode);
    var html = document.documentElement;
    html.setAttribute('lang', current);
    html.setAttribute('dir', current === 'ar' ? 'rtl' : 'ltr');
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

  // Initialise from saved choice, falling back to the user's stored preference, then EN.
  function init(userLang) {
    var saved = null;
    try { saved = localStorage.getItem(STORAGE_KEY); } catch (e) {}
    var lang = saved || (userLang === 'ar' ? 'ar' : (userLang === 'en' ? 'en' : null)) || 'en';
    apply(lang); // init never re-persists to the server
  }

  global.AC_I18N = {
    t: t, apply: apply, set: set, toggle: toggle, init: init,
    get lang() { return current; },
    dict: DICT,
    add: function (extra) { for (var k in extra) if (Object.prototype.hasOwnProperty.call(extra, k)) DICT[k] = extra[k]; }
  };

  // Auto-init from localStorage on load; pages refine via AC_I18N.init(user.preferred_language) after /auth/me.
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { init(); });
  } else {
    init();
  }
})(window);

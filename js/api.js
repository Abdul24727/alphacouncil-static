// =============================================================================
// AlphaCouncil API client — talks to the LIVE FastAPI backend, same-origin.
// This REPLACES all simulated data in the static prototype with real,
// database-backed calls. Every page includes this before adviser-core.js.
//
// Routing (matches the deployed nginx on alphacouncil.tech):
//   /api/auth/*  -> nginx rewrites to backend /auth/*  (login, register, me, ...)
//   /api/*       -> backend /api/*  (portfolio, screening, news, ticker, adviser, council, thesis)
//
// Auth model (same as the production app): an HttpOnly session cookie set by
// /auth/login, plus a readable `ac_csrf` twin cookie that must be echoed in an
// `X-CSRF-Token` header on writes. A legacy Bearer token (localStorage
// `ac.auth.token`) is also accepted as a fallback.
// =============================================================================
(function (global) {
  'use strict';

  function getCookie(name) {
    const m = document.cookie.match(new RegExp('(?:^|;\\s*)' + name + '=([^;]+)'));
    return m ? decodeURIComponent(m[1]) : null;
  }

  function ApiError(status, message, detail) {
    this.name = 'ApiError';
    this.status = status;
    this.message = message || 'Request failed';
    this.detail = detail;
  }
  ApiError.prototype = Object.create(Error.prototype);

  async function request(path, opts) {
    opts = opts || {};
    const method = (opts.method || 'GET').toUpperCase();
    const headers = Object.assign({ Accept: 'application/json' }, opts.headers || {});
    const init = { method, credentials: 'include', headers };

    if (opts.body !== undefined) {
      headers['Content-Type'] = 'application/json';
      init.body = JSON.stringify(opts.body);
    }
    // CSRF double-submit on cookie-authed writes
    if (['POST', 'PUT', 'PATCH', 'DELETE'].indexOf(method) !== -1) {
      const csrf = getCookie('ac_csrf');
      if (csrf) headers['X-CSRF-Token'] = csrf;
    }
    // Legacy Bearer fallback
    const tok = (function () { try { return localStorage.getItem('ac.auth.token'); } catch (e) { return null; } })();
    if (tok && !headers.Authorization) headers.Authorization = 'Bearer ' + tok;

    let resp;
    try {
      resp = await fetch(path, init);
    } catch (e) {
      throw new ApiError(0, 'Network error — could not reach the server.', e);
    }
    const text = await resp.text();
    let data = null;
    try { data = text ? JSON.parse(text) : null; } catch (e) { data = text; }
    if (!resp.ok) {
      let detail = (data && data.detail) || resp.statusText;
      if (typeof detail !== 'string') detail = JSON.stringify(detail);
      throw new ApiError(resp.status, detail, data);
    }
    return data;
  }

  const API = {
    ApiError: ApiError,
    getCookie: getCookie,
    get: function (p) { return request(p, { method: 'GET' }); },
    post: function (p, body) { return request(p, { method: 'POST', body: body }); },
    put: function (p, body) { return request(p, { method: 'PUT', body: body }); },
    del: function (p) { return request(p, { method: 'DELETE' }); },

    // ---- Auth ----
    login: function (email, password, remember) { return API.post('/api/auth/login', { email: email, password: password, remember: !!remember }); },
    register: function (email, password, opts) {
      opts = (opts && typeof opts === 'object') ? opts : { lang: opts };  // back-compat: 3rd arg used to be lang
      return API.post('/api/auth/register', {
        email: email, password: password,
        preferred_language: opts.lang || 'en',
        first_name: opts.firstName || '', last_name: opts.lastName || '', market: opts.market || ''
      });
    },
    me: function () { return API.get('/api/auth/me'); },
    logout: function () { return API.post('/api/auth/logout', {}); },
    forgotPassword: function (email) { return API.post('/api/auth/forgot-password', { email: email }); },
    resetPassword: function (token, newPassword) { return API.post('/api/auth/reset-password', { token: token, new_password: newPassword }); },

    // ---- Portfolio ----
    portfolio: function () { return API.get('/api/portfolio/holdings'); },
    addHolding: function (ticker, shares, avgCost, notes) {
      return API.post('/api/portfolio/holdings', { ticker: ticker, shares: shares, avg_cost: avgCost, notes: notes || undefined });
    },
    // Vision-extract holdings from an uploaded statement image/PDF (writes nothing; returns rows matched to real ticker_keys).
    importExtract: function (contentType, dataBase64, filename) {
      return API.post('/api/portfolio/import-extract', { content_type: contentType, data_base64: dataBase64, filename: filename });
    },
    importConfirm: function (holdings) { return API.post('/api/portfolio/import-confirm', { holdings: holdings }); },
    deleteHolding: function (tickerKey) { return API.del('/api/portfolio/holdings/' + encodeURIComponent(tickerKey)); },

    // ---- Watchlist (per-user; star a stock to track it) ----
    watchlist: function () { return API.get('/api/watchlist'); },
    addToWatchlist: function (ticker) { return API.post('/api/watchlist', { ticker: ticker }); },
    removeFromWatchlist: function (tickerKey) { return API.del('/api/watchlist/' + encodeURIComponent(tickerKey)); },

    // ---- Screening / market ----
    screening: function (limit) { return API.get('/api/screening' + (limit ? ('?limit=' + limit) : '')); },
    ticker: function (key) { return API.get('/api/ticker/' + encodeURIComponent(key)); },
    tickerNews: function (key) { return API.get('/api/ticker/' + encodeURIComponent(key) + '/news?limit=12'); },
    marketIndices: function () { return API.get('/api/market-indices'); },
    tickerTape: function () { return API.get('/api/ticker-tape'); },
    movers: function () { return API.get('/api/movers'); },
    calendar: function () { return API.get('/api/calendar'); },

    // ---- News ----
    latestNews: function (limit) { return API.get('/api/news/latest?limit=' + (limit || 12)); },
    holdingsNews: function (limit) { return API.get('/api/news/for-holdings?limit=' + (limit || 12)); },
    newsItem: function (id) { return API.get('/api/news/item/' + encodeURIComponent(id)); },

    // ---- Alerts / notifications (real, per-user) ----
    alerts: function (limit, before) {
      var q = [];
      if (limit) q.push('limit=' + limit);
      if (before) q.push('before=' + before);
      return API.get('/api/alerts' + (q.length ? ('?' + q.join('&')) : ''));
    },
    alertsUnread: function () { return API.get('/api/alerts/unread-count'); },
    markAlertsRead: function (ids) { return API.post('/api/alerts/mark-read', (ids && ids.length) ? { ids: ids } : {}); },

    // ---- Adviser & Council ----
    askAdviser: function (question, ticker) { return API.post('/api/adviser/ask', { question: question, ticker: ticker || undefined }); },
    marketBrief: function (market) { return API.get('/api/adviser/market-brief' + (market ? ('?market=' + encodeURIComponent(market)) : '')); },
    askCouncil: function (question, ticker) { return API.post('/api/adviser/council/ask', { question: question, ticker: ticker || undefined }); },
    riskProfile: function () { return API.get('/api/adviser/risk-profile'); },
    saveRiskProfile: function (p) { return API.put('/api/adviser/risk-profile', p); },

    // ---- Thesis (11-dimension score matrix) ----
    thesis: function (key) { return API.post('/api/thesis/' + encodeURIComponent(key), {}); },
  };

  // Auth guard for protected pages. Resolves to the user object, or redirects
  // to login.html on 401 and resolves null.
  API.requireAuth = async function () {
    try {
      return await API.me();
    } catch (e) {
      if (e && e.status === 401) { window.location.href = 'login.html'; return null; }
      throw e;
    }
  };

  // Current user cache for the session (avoids refetching /auth/me on every page bit).
  API.user = null;
  API.loadUser = async function () {
    try { API.user = await API.me(); } catch (e) { API.user = null; }
    return API.user;
  };

  global.API = API;
})(window);

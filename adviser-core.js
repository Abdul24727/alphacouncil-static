// =============================================
// AlphaCouncil Core v2.1 — Single Source of Truth
// Handles: Sidebar toggle + content shift, Chat, Toasts,
// Council Modal, Loading/Empty/Error states, Keyboard shortcuts
// All pages must include this file and call: AlphaCouncil.init('page-name')
// =============================================
// FINAL CLEANUP: Core JS consolidation + shared toast system | 2026-06-17

/**
 * AlphaCouncil - Global Adviser & Interactivity Core
 * Shared module for sidebar, modals, toasts, and cross-page functionality
 */

const AlphaCouncil = (function() {
  'use strict';

  // ============================================
  // STATE MANAGEMENT
  // ============================================
  const state = {
    currentPage: 'dashboard',
    currentStock: null,
    currentNewsContext: null,
    sidebarOpen: false,
    user: null,        // loaded from /api/auth/me
    holdings: [],      // REAL holdings from /api/portfolio/holdings (loadPortfolio)
    portfolioReady: false
  };

  // Load the signed-in user's REAL holdings from the live backend and normalise
  // them to the shape the UI expects (ticker_key -> short ticker, native value,
  // P&L, weight). Replaces the former hardcoded demo array entirely.
  async function loadPortfolio() {
    if (!window.API) return state.holdings;
    try {
      const rows = await API.portfolio();
      const totalSar = rows.reduce(function (s, r) { return s + (r.market_value_sar || 0); }, 0);
      state.holdings = rows.map(function (r) {
        const value = r.market_value_native != null ? r.market_value_native : (r.shares * (r.last_price || 0));
        const cost = r.cost_basis_native != null ? r.cost_basis_native : (r.shares * (r.avg_cost || 0));
        return {
          tickerKey: r.ticker,
          ticker: r.ticker_short || (String(r.ticker).split('_')[0]),
          name: r.name_en || r.ticker_short || String(r.ticker).split('_')[0],
          shares: r.shares,
          avgCost: r.avg_cost,
          currentPrice: r.last_price,
          currency: r.currency || 'SAR',
          value: value,
          cost: cost,
          pnl: value - cost,
          pnlPct: cost > 0 ? ((value - cost) / cost) * 100 : 0,
          dayChange: r.day_change_pct,
          weight: totalSar > 0 ? ((r.market_value_sar || 0) / totalSar) * 100 : 0,
          valueSar: r.market_value_sar || 0,
          costSar: r.cost_basis_sar || 0,
          divYield: r.dividend_yield_pct,
          sector: r.sector_en,
          exchange: r.exchange
        };
      });
      state.portfolioReady = true;
    } catch (e) {
      state.holdings = [];
      state.portfolioReady = false;
    }
    return state.holdings;
  }

  // ============================================
  // TOAST NOTIFICATIONS
  // ============================================
  function showToast(title, text, type = 'success') {
    // Inject toast styles if not present
    if (!document.getElementById('toastStyles')) {
      const styleEl = document.createElement('style');
      styleEl.id = 'toastStyles';
      styleEl.textContent = `
        .global-toast { position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%) translateY(20px); background: rgba(17, 26, 43, 0.95); backdrop-filter: blur(16px); border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; padding: 14px 20px; display: flex; align-items: center; gap: 14px; z-index: 9999; opacity: 0; pointer-events: none; transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1); min-width: 280px; max-width: 420px; box-shadow: 0 8px 32px rgba(0,0,0,0.3); }
        .global-toast.show { transform: translateX(-50%) translateY(0); opacity: 1; pointer-events: auto; }
        .global-toast .toast-icon { width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
        .global-toast .toast-icon svg { width: 18px; height: 18px; }
        .global-toast .toast-icon.success { background: rgba(16, 185, 129, 0.15); color: #10B981; }
        .global-toast .toast-icon.info { background: rgba(39, 211, 195, 0.15); color: #27D3C3; }
        .global-toast .toast-icon.warning { background: rgba(245, 158, 11, 0.15); color: #F59E0B; }
        .global-toast .toast-icon.error { background: rgba(239, 68, 68, 0.15); color: #EF4444; }
        .global-toast .toast-content { flex: 1; min-width: 0; }
        .global-toast .toast-title { font-size: 13px; font-weight: 600; color: #F8FAFC; margin-bottom: 2px; }
        .global-toast .toast-text { font-size: 12px; color: #AAB6C5; line-height: 1.4; }
        .global-toast .toast-close { width: 24px; height: 24px; background: transparent; border: none; border-radius: 6px; display: flex; align-items: center; justify-content: center; cursor: pointer; color: #6B7A8F; transition: all 0.2s; flex-shrink: 0; }
        .global-toast .toast-close:hover { background: rgba(255,255,255,0.05); color: #AAB6C5; }
        .global-toast .toast-close svg { width: 14px; height: 14px; }
      `;
      document.head.appendChild(styleEl);
    }

    let toast = document.getElementById('globalToast');
    if (!toast) {
      toast = document.createElement('div');
      toast.id = 'globalToast';
      toast.className = 'global-toast';
      toast.innerHTML = `
        <div class="toast-icon success">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
        </div>
        <div class="toast-content">
          <div class="toast-title"></div>
          <div class="toast-text"></div>
        </div>
        <button class="toast-close" onclick="this.parentElement.classList.remove('show')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
        </button>
      `;
      document.body.appendChild(toast);
    }

    const iconSvgs = {
      success: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>',
      info: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>',
      warning: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>',
      error: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M15 9l-6 6M9 9l6 6"/></svg>'
    };

    toast.querySelector('.toast-icon').className = `toast-icon ${type}`;
    toast.querySelector('.toast-icon').innerHTML = iconSvgs[type] || iconSvgs.success;
    toast.querySelector('.toast-title').textContent = title;
    toast.querySelector('.toast-text').textContent = text;

    // Clear any existing timeout
    if (toast._timeout) clearTimeout(toast._timeout);

    toast.classList.add('show');
    // Consistent 3-second display for all toasts
    toast._timeout = setTimeout(() => toast.classList.remove('show'), 3000);
  }

  // ============================================
  // ADVISER SIDEBAR
  // ============================================
  function toggleSidebar() {
    const sidebar = document.getElementById('adviserSidebar');
    const toggle = document.getElementById('adviserToggle');

    if (sidebar) {
      state.sidebarOpen = !state.sidebarOpen;
      sidebar.classList.toggle('open', state.sidebarOpen);
      if (toggle) toggle.classList.toggle('active', state.sidebarOpen);
      document.body.classList.toggle('sidebar-open', state.sidebarOpen);
    }
  }

  function openSidebar() {
    if (!state.sidebarOpen) toggleSidebar();
  }

  function closeSidebar() {
    if (state.sidebarOpen) toggleSidebar();
  }

  function setPageContext(page, stock = null, newsContext = null) {
    state.currentPage = page;
    state.currentStock = stock;
    state.currentNewsContext = newsContext;
    updateSidebarContext();
  }

  function updateSidebarContext() {
    const contextEl = document.querySelector('.sidebar-context');
    const questionsEl = document.querySelector('.suggested-questions');

    if (!contextEl) return;

    let contextHtml = '';
    let questions = [];

    if (state.currentStock) {
      contextHtml = `
        <div class="context-label">Viewing</div>
        <div class="context-stock">${state.currentStock.ticker} <span>· ${state.currentStock.name}</span></div>
      `;
      questions = [
        `Explain the current thesis score for ${state.currentStock.name}`,
        `Compare ${state.currentStock.ticker} to stronger GCC peers`,
        `What would trimming 10% of ${state.currentStock.ticker} do to my portfolio?`,
        `What are the key risks for ${state.currentStock.name}?`
      ];
    } else if (state.currentNewsContext) {
      contextHtml = `
        <div class="context-label">Discussing</div>
        <div class="context-story">${state.currentNewsContext.headline}</div>
        <button class="context-clear" onclick="AlphaCouncil.clearNewsContext()">Clear context</button>
      `;
      questions = [
        'How does this news affect my portfolio?',
        'What holdings are impacted by this development?',
        'Should I review my position based on this?',
        'What are analysts saying about this?'
      ];
    } else if (state.currentPage === 'portfolio') {
      contextHtml = `
        <div class="context-label">Context</div>
        <div class="context-stock">Portfolio Management</div>
      `;
      questions = [
        'What is my weakest thesis score?',
        'Help me trim 15% of Al Rajhi',
        'Show lot-level P&L for Aramco',
        'How can I reduce banking concentration?'
      ];
    } else if (state.currentPage === 'dashboard') {
      contextHtml = `
        <div class="context-label">Context</div>
        <div class="context-stock">Portfolio Overview</div>
      `;
      questions = [
        'Summarize my portfolio health',
        'What moved my portfolio today?',
        'Which holdings need attention?',
        'What does the Council recommend?'
      ];
    } else if (state.currentPage === 'news') {
      contextHtml = `
        <div class="context-label">Context</div>
        <div class="context-stock">GCC Market News</div>
      `;
      questions = [
        'Summarize today\'s news for my holdings',
        'What news affects my positions?',
        'Are there any earnings surprises?',
        'What should I monitor this week?'
      ];
    } else if (state.currentPage === 'alerts') {
      contextHtml = `
        <div class="context-label">Context</div>
        <div class="context-stock">Portfolio Alerts</div>
      `;
      questions = [
        'What triggered my latest alerts?',
        'Which holdings need immediate attention?',
        'Explain this thesis change alert',
        'How should I respond to these alerts?'
      ];
    } else if (state.currentPage === 'council-history') {
      contextHtml = `
        <div class="context-label">Context</div>
        <div class="context-stock">Council Reviews</div>
      `;
      questions = [
        'Summarize recent council findings',
        'What patterns emerge from past reviews?',
        'Which holdings get frequent attention?',
        'Show thesis changes over time'
      ];
    } else if (state.currentPage === 'settings') {
      contextHtml = `
        <div class="context-label">Context</div>
        <div class="context-stock">App Settings</div>
      `;
      questions = [
        'How do alert thresholds work?',
        'What is the AI Council?',
        'How is the thesis score calculated?',
        'Explain position monitoring settings'
      ];
    } else if (state.currentPage === 'scenarios') {
      contextHtml = `
        <div class="context-label">Context</div>
        <div class="context-stock">Portfolio Scenarios</div>
      `;
      questions = [
        'What scenario poses the biggest risk?',
        'How diversified am I against oil shock?',
        'Model a 20% market correction',
        'Which positions add the most risk?'
      ];
    } else if (state.currentPage === 'stock-detail') {
      contextHtml = `
        <div class="context-label">Context</div>
        <div class="context-stock">Stock Analysis</div>
      `;
      questions = [
        'Break down this thesis score',
        'Compare to sector peers',
        'What are the key risks?',
        'Show recent analyst changes'
      ];
    } else {
      contextHtml = `
        <div class="context-label">Context</div>
        <div class="context-stock">GCC Markets</div>
      `;
      questions = [
        'How are GCC markets performing?',
        'What sectors are leading today?',
        'Any significant market moves?',
        'What is driving oil prices?'
      ];
    }

    contextEl.innerHTML = contextHtml;

    if (questionsEl) {
      questionsEl.innerHTML = questions.map(q =>
        `<button class="suggested-question" onclick="AlphaCouncil.askQuestion('${q.replace(/'/g, "\\'")}')">${q}</button>`
      ).join('');
    }
  }

  function clearNewsContext() {
    state.currentNewsContext = null;
    updateSidebarContext();
  }

  function askQuestion(question) {
    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
      chatInput.value = question;
      processChat();
    }
  }

  function addChatMessage(text, isUser = false) {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;

    const message = document.createElement('div');
    message.className = `chat-message ${isUser ? 'user' : 'adviser'}`;
    const time = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    message.innerHTML = `
      <div class="chat-avatar">${isUser ? (initialsFromUser(state.user) || 'You') : 'AC'}</div>
      <div>
        <div class="chat-bubble">${text}</div>
        <div class="chat-time">${time}</div>
      </div>
    `;
    chatMessages.appendChild(message);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  // REAL adviser: POST /api/adviser/ask (portfolio-aware server-side, 10/day).
  async function processChat() {
    const chatInput = document.getElementById('chatInput');
    if (!chatInput) return;
    const text = chatInput.value.trim();
    if (!text) return;

    addChatMessage(text, true);
    chatInput.value = '';

    const typing = addTypingIndicator();
    const ticker = state.currentStock && state.currentStock.tickerKey ? state.currentStock.tickerKey : undefined;
    try {
      const res = await API.askAdviser(text, ticker);
      removeTypingIndicator(typing);
      addChatMessage(formatAdviserAnswer(res.answer, res.disclaimer));
    } catch (e) {
      removeTypingIndicator(typing);
      addChatMessage(adviserErrorMessage(e));
    }
  }

  // Honest error mapping (mirrors backend status codes — never a fabricated answer).
  function adviserErrorMessage(e) {
    const s = e && e.status;
    if (s === 401) return 'Please <a href="login.html" style="color:var(--accent-primary,#27D3C3);">sign in</a> to ask the Adviser.';
    if (s === 429) return "You've reached today's limit (10 questions/day). It resets tomorrow.";
    if (s === 503) return 'The Adviser is temporarily unavailable. Please try again in a moment.';
    if (s === 0) return "Couldn't reach the server. Check your connection and try again.";
    return (e && e.message) ? e.message : 'Something went wrong. Please try again.';
  }

  // Render the real LLM answer (light markdown) as safe HTML, with the mandatory
  // disclaimer appended verbatim and muted.
  function formatAdviserAnswer(answer, disclaimer) {
    let body = escapeHtml(answer || '')
      .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
      .replace(/\n{2,}/g, '<br><br>')
      .replace(/\n/g, '<br>');
    if (disclaimer) {
      body += '<br><br><span style="font-size:11px;color:var(--fg-dim,#6B7A8F);line-height:1.5;display:block;border-top:1px solid var(--border,rgba(255,255,255,0.08));padding-top:8px;margin-top:4px;">' + escapeHtml(disclaimer) + '</span>';
    }
    return body;
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function addTypingIndicator() {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return null;
    const el = document.createElement('div');
    el.className = 'chat-message adviser';
    el.innerHTML = '<div class="chat-avatar">AC</div><div><div class="chat-bubble"><span class="ac-pulse">The Adviser is thinking…</span></div></div>';
    chatMessages.appendChild(el);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return el;
  }
  function removeTypingIndicator(el) { if (el && el.parentNode) el.parentNode.removeChild(el); }

  // ============================================
  // COUNCIL MODAL
  // ============================================
  function openCouncilModal(context = null) {
    let modal = document.getElementById('councilModalOverlay');
    if (!modal) { modal = createCouncilModal(); document.body.appendChild(modal); }

    const tickerKey = context && (context.tickerKey || context.ticker) ? (context.tickerKey || context.ticker) : null;
    const badge = document.getElementById('councilBadge');
    if (badge) {
      if (tickerKey) { badge.textContent = String(tickerKey).split('_')[0] + ' Position'; badge.className = 'council-badge position'; }
      else { badge.textContent = 'Portfolio-Wide'; badge.className = 'council-badge'; }
    }
    modal.classList.add('open');
    document.body.style.overflow = 'hidden';
    runCouncil(tickerKey);
  }

  // REAL convene: POST /api/adviser/council/ask (Pro/Elite, ~90s). Renders the
  // chairman's synthesis + the anonymised committee deliberation, or honest errors.
  async function runCouncil(tickerKey) {
    const body = document.querySelector('#councilModalOverlay .council-body');
    if (!body) return;
    const question = tickerKey
      ? ('Convene the Council on my position in ' + String(tickerKey).split('_')[0] + ': is the thesis intact, what are the key risks, and what should I consider?')
      : 'Convene the Council on my portfolio: concentration, the biggest risks, diversification, and what I should consider next.';
    body.innerHTML = councilLoadingHtml();
    try {
      const res = await API.askCouncil(question, tickerKey || undefined);
      body.innerHTML = councilResultHtml(res);
    } catch (e) {
      body.innerHTML = councilErrorHtml(e);
    }
  }

  function councilLoadingHtml() {
    return '<div style="text-align:center;padding:48px 24px;">'
      + '<div class="ac-spinner lg" style="margin:0 auto 20px;"></div>'
      + '<div style="font-size:15px;font-weight:600;color:#F8FAFC;margin-bottom:8px;">The committee is convening…</div>'
      + '<div style="font-size:13px;color:#AAB6C5;max-width:360px;margin:0 auto;line-height:1.6;">A panel of leading AI models is debating your question, ranking each other, then the chairman synthesises the verdict. This usually takes a minute or two.</div>'
      + '</div>';
  }

  function councilResultHtml(res) {
    const colors = ['#6366f1', '#0ea5e9', '#14b8a6', '#f59e0b', '#a855f7'];
    const idx = {}; (res.analysts || []).forEach(function (a, i) { idx[a.model] = i; });
    const mem = function (i) { return 'Member ' + (i + 1); };
    const rich = function (t) { return escapeHtml(t || '').replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>').replace(/\n{2,}/g, '<br><br>').replace(/\n/g, '<br>'); };

    const detected = (res.tickers_detected || []).map(function (t) {
      return '<span style="border:1px solid var(--border,rgba(255,255,255,0.08));border-radius:5px;padding:2px 6px;font-family:var(--font-mono,monospace);font-size:11px;margin-left:4px;">' + escapeHtml(String(t).split('_')[0]) + '</span>';
    }).join('');

    const analysts = (res.analysts || []).map(function (a, i) {
      return '<div style="border:1px solid var(--border,rgba(255,255,255,0.08));border-radius:12px;padding:14px;margin-bottom:10px;background:#111A2B;">'
        + '<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;"><span style="width:9px;height:9px;border-radius:50%;background:' + colors[i % 5] + ';"></span><span style="font-weight:600;font-size:13px;color:#F8FAFC;">' + mem(i) + '</span><span style="font-size:10px;color:#6B7A8F;text-transform:uppercase;letter-spacing:.04em;">individual take</span></div>'
        + '<div style="font-size:13px;color:#AAB6C5;line-height:1.6;">' + rich(a.response) + '</div></div>';
    }).join('');

    const rankings = (res.rankings || []).map(function (r, i) {
      const mi = idx[r.model] != null ? idx[r.model] : i;
      return '<div style="display:flex;align-items:center;gap:10px;font-size:13px;padding:4px 0;color:#F8FAFC;"><span style="width:16px;text-align:center;color:#6B7A8F;font-family:var(--font-mono,monospace);font-size:11px;">' + (i + 1) + '</span><span style="width:8px;height:8px;border-radius:50%;background:' + colors[mi % 5] + ';"></span><span style="flex:1;font-weight:500;">' + mem(mi) + '</span><span style="font-size:11px;color:#6B7A8F;font-family:var(--font-mono,monospace);">avg ' + (r.average_rank != null ? r.average_rank.toFixed(1) : '—') + '</span></div>';
    }).join('');

    return '<section class="synthesis-section"><div class="synthesis-card">'
      + '<div class="synthesis-header"><span class="synthesis-label">Chairman’s synthesis</span>'
      + '<span class="synthesis-timestamp">' + (res.council_remaining_today != null ? (Math.max(0, res.council_remaining_today) + ' left today') : '') + '</span></div>'
      + (detected ? '<div style="margin-bottom:10px;font-size:11px;color:#6B7A8F;">Real analyst data injected for' + detected + '</div>' : '')
      + '<p class="synthesis-text">' + rich(res.answer) + '</p></div></section>'
      + '<details style="margin-top:6px;"><summary style="cursor:pointer;font-size:13px;color:var(--accent-primary,#27D3C3);font-weight:600;padding:8px 0;list-style:none;">Show committee deliberation</summary>'
      + (rankings ? '<div style="border:1px solid var(--border,rgba(255,255,255,0.08));border-radius:12px;padding:14px;margin:10px 0;background:#111A2B;"><div style="font-size:11px;text-transform:uppercase;letter-spacing:.04em;color:#6B7A8F;font-weight:600;margin-bottom:8px;">Peer ranking</div>' + rankings + '</div>' : '')
      + analysts + '</details>'
      + (res.disclaimer ? '<p style="font-size:11px;color:#6B7A8F;line-height:1.5;margin-top:14px;border-top:1px solid var(--border,rgba(255,255,255,0.08));padding-top:10px;">' + escapeHtml(res.disclaimer) + '</p>' : '');
  }

  function councilErrorHtml(e) {
    const s = e && e.status;
    let msg;
    if (s === 403) msg = 'The Council is a Pro & Elite feature. <a href="pricing.html" style="color:var(--accent-primary,#27D3C3);">Upgrade</a> to convene the committee.';
    else if (s === 429) msg = "You’ve used today’s Council convenings. They reset tomorrow.";
    else if (s === 401) msg = 'Please <a href="login.html" style="color:var(--accent-primary,#27D3C3);">sign in</a> to convene the Council.';
    else msg = "The Council couldn’t convene just now — please try again in a moment.";
    return '<div class="ac-error-state ac-fade-in"><div class="ac-error-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/></svg></div><div class="ac-error-title" style="color:#F8FAFC;">Council unavailable</div><p class="ac-error-text">' + msg + '</p></div>';
  }

  function closeCouncilModal() {
    const modal = document.getElementById('councilModalOverlay');
    if (modal) {
      modal.classList.remove('open');
      document.body.style.overflow = '';
      // Return focus to the trigger element if available
      const trigger = document.querySelector('[data-council-trigger]');
      if (trigger) trigger.focus();
    }
  }

  function createCouncilModal() {
    // Inject modal styles if not present
    if (!document.getElementById('councilModalStyles')) {
      const styleEl = document.createElement('style');
      styleEl.id = 'councilModalStyles';
      styleEl.textContent = `
        .council-modal-overlay { position: fixed; inset: 0; background: rgba(7, 17, 31, 0.9); backdrop-filter: blur(8px); z-index: 300; display: flex; align-items: center; justify-content: center; opacity: 0; pointer-events: none; transition: opacity 0.3s; }
        .council-modal-overlay.open { opacity: 1; pointer-events: auto; }
        .council-modal { width: 90%; max-width: 900px; max-height: 90vh; background: #0B1120; border: 1px solid rgba(255,255,255,0.08); border-radius: 20px; overflow: hidden; display: flex; flex-direction: column; transform: scale(0.95) translateY(20px); transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1); }
        .council-modal-overlay.open .council-modal { transform: scale(1) translateY(0); }
        .council-header { padding: 20px 24px; background: linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(39, 211, 195, 0.05)); border-bottom: 1px solid rgba(255,255,255,0.08); display: flex; align-items: center; justify-content: space-between; }
        .council-header-left { display: flex; align-items: center; gap: 16px; }
        .council-icon { width: 48px; height: 48px; background: linear-gradient(135deg, #8B5CF6, #27D3C3); border-radius: 14px; display: flex; align-items: center; justify-content: center; }
        .council-icon svg { width: 24px; height: 24px; color: #07111F; }
        .council-title { font-size: 20px; font-weight: 700; display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
        .council-badge { padding: 4px 10px; background: rgba(139, 92, 246, 0.2); border: 1px solid #8B5CF6; border-radius: 6px; font-size: 10px; font-weight: 700; color: #8B5CF6; text-transform: uppercase; }
        .council-badge.position { background: rgba(39, 211, 195, 0.2); border-color: #27D3C3; color: #27D3C3; }
        .council-subtitle { font-size: 12px; color: #AAB6C5; display: flex; align-items: center; gap: 6px; margin-top: 4px; }
        .council-subtitle svg { width: 14px; height: 14px; }
        .council-close { width: 40px; height: 40px; background: #111A2B; border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; display: flex; align-items: center; justify-content: center; cursor: pointer; color: #6B7A8F; transition: all 0.2s; }
        .council-close:hover { border-color: #EF4444; color: #EF4444; }
        .council-close svg { width: 20px; height: 20px; }
        .council-body { flex: 1; overflow-y: auto; padding: 24px; }
        .synthesis-section { margin-bottom: 24px; }
        .synthesis-card { background: linear-gradient(135deg, rgba(139, 92, 246, 0.08), rgba(39, 211, 195, 0.05)); border: 1px solid rgba(139, 92, 246, 0.3); border-radius: 16px; padding: 20px; }
        .synthesis-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; flex-wrap: wrap; gap: 12px; }
        .synthesis-label { font-size: 12px; font-weight: 700; color: #8B5CF6; text-transform: uppercase; letter-spacing: 0.05em; display: flex; align-items: center; gap: 8px; }
        .synthesis-label svg { width: 16px; height: 16px; }
        .synthesis-timestamp { font-size: 11px; color: #6B7A8F; }
        .synthesis-text { font-size: 14px; color: #AAB6C5; line-height: 1.7; }
        .synthesis-text strong { color: #F8FAFC; }
        .synthesis-text .highlight { color: #27D3C3; font-weight: 600; }
        .synthesis-text .caution { color: #F59E0B; }
        .recommendations-section { margin-bottom: 24px; }
        .section-header { margin-bottom: 16px; }
        .section-title { font-size: 14px; font-weight: 600; display: flex; align-items: center; gap: 8px; }
        .section-title svg { width: 18px; height: 18px; color: #10B981; }
        .recommendations-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
        @media (max-width: 768px) { .recommendations-grid { grid-template-columns: 1fr; } }
        .recommendation-card { background: #111A2B; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 16px; display: flex; gap: 14px; transition: all 0.2s; }
        .recommendation-card:hover { border-color: rgba(255,255,255,0.12); }
        .recommendation-number { width: 28px; height: 28px; background: rgba(39, 211, 195, 0.15); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; color: #27D3C3; flex-shrink: 0; }
        .recommendation-title { font-size: 13px; font-weight: 600; margin-bottom: 4px; }
        .recommendation-detail { font-size: 12px; color: #6B7A8F; line-height: 1.5; }
        .council-footer { padding: 16px 24px; background: #0B1120; border-top: 1px solid rgba(255,255,255,0.08); display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
        .footer-left, .footer-right { display: flex; gap: 10px; flex-wrap: wrap; }
        .footer-btn { padding: 10px 18px; font-size: 13px; font-weight: 600; border-radius: 10px; cursor: pointer; display: inline-flex; align-items: center; gap: 8px; transition: all 0.2s; }
        .footer-btn svg { width: 16px; height: 16px; }
        .footer-btn.primary { background: #27D3C3; border: none; color: #07111F; }
        .footer-btn.primary:hover { transform: translateY(-1px); box-shadow: 0 4px 16px rgba(39, 211, 195, 0.2); }
        .footer-btn.secondary { background: #111A2B; border: 1px solid rgba(255,255,255,0.08); color: #F8FAFC; }
        .footer-btn.secondary:hover { border-color: rgba(255,255,255,0.12); }
        .footer-btn.ghost { background: transparent; border: 1px solid rgba(255,255,255,0.08); color: #AAB6C5; }
        .footer-btn.ghost:hover { border-color: rgba(255,255,255,0.12); color: #F8FAFC; }
        .modal-overlay { position: fixed; inset: 0; background: rgba(7, 17, 31, 0.9); backdrop-filter: blur(8px); z-index: 250; display: flex; align-items: center; justify-content: center; opacity: 0; pointer-events: none; transition: opacity 0.3s; }
        .modal-overlay.open { opacity: 1; pointer-events: auto; }
        .modal { background: #0B1120; border: 1px solid rgba(255,255,255,0.08); border-radius: 16px; width: 90%; overflow: hidden; transform: scale(0.95); transition: transform 0.3s; }
        .modal-overlay.open .modal { transform: scale(1); }
        .modal-header { padding: 20px; border-bottom: 1px solid rgba(255,255,255,0.08); display: flex; align-items: flex-start; justify-content: space-between; }
        .modal-title { display: flex; align-items: flex-start; gap: 14px; }
        .modal-icon { width: 44px; height: 44px; border-radius: 12px; display: flex; align-items: center; justify-content: center; }
        .modal-icon svg { width: 22px; height: 22px; }
        .modal-title h2 { font-size: 18px; font-weight: 700; }
        .modal-title p { font-size: 12px; color: #6B7A8F; margin-top: 2px; }
        .modal-close { width: 32px; height: 32px; background: #111A2B; border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; display: flex; align-items: center; justify-content: center; cursor: pointer; color: #6B7A8F; }
        .modal-close:hover { color: #EF4444; border-color: #EF4444; }
        .modal-close svg { width: 16px; height: 16px; }
        .modal-body { padding: 20px; }
        .form-group { margin-bottom: 16px; }
        .form-label { display: block; font-size: 12px; font-weight: 600; color: #AAB6C5; margin-bottom: 6px; }
        .form-input { width: 100%; padding: 12px 14px; background: #111A2B; border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; font-size: 14px; color: #F8FAFC; outline: none; }
        .form-input:focus { border-color: #27D3C3; }
        .form-input::placeholder { color: #6B7A8F; }
        .btn { padding: 10px 20px; border-radius: 10px; font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.2s; }
        .btn-secondary { background: #111A2B; border: 1px solid rgba(255,255,255,0.08); color: #F8FAFC; }
        .btn-primary { background: #27D3C3; border: none; color: #07111F; }
        .btn-primary:hover { transform: translateY(-1px); box-shadow: 0 4px 16px rgba(39, 211, 195, 0.2); }
      `;
      document.head.appendChild(styleEl);
    }

    const modal = document.createElement('div');
    modal.className = 'council-modal-overlay';
    modal.id = 'councilModalOverlay';
    modal.innerHTML = `
      <div class="council-modal" id="councilModal">
        <header class="council-header">
          <div class="council-header-left">
            <div class="council-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
            </div>
            <div class="council-title-group">
              <h1 class="council-title">AI Analyst Council Review <span class="council-badge" id="councilBadge">Portfolio-Wide</span></h1>
              <p class="council-subtitle"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>7 specialized perspectives • One synthesized view</p>
            </div>
          </div>
          <button class="council-close" onclick="AlphaCouncil.closeCouncilModal()">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
          </button>
        </header>
        <div class="council-body">
          <section class="synthesis-section">
            <div class="synthesis-card">
              <div class="synthesis-header">
                <span class="synthesis-label"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/></svg>Strategic Synthesis</span>
                <span class="synthesis-timestamp">Generated ${new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })} at ${new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })} GST</span>
              </div>
              <p class="synthesis-text">
                Data suggests reviewing <strong>portfolio concentration in the banking sector</strong> (<span class="highlight">32.2% weight</span>). While recent performance appears strong with Al Rajhi and QNB leading gains, valuation metrics indicate <span class="caution">some names may be stretched</span> relative to historical averages. Consider whether <strong>Materials exposure (7.2%)</strong> aligns with your target allocation given current commodity pricing dynamics.
              </p>
            </div>
          </section>
          <section class="recommendations-section">
            <div class="section-header"><h2 class="section-title"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>Actionable Insights</h2></div>
            <div class="recommendations-grid">
              <div class="recommendation-card"><div class="recommendation-number">1</div><div class="recommendation-content"><div class="recommendation-title">Portfolio concentration should be reviewed</div><div class="recommendation-detail">Banking sector at 32.2% exceeds typical 25% concentration threshold.</div></div></div>
              <div class="recommendation-card"><div class="recommendation-number">2</div><div class="recommendation-content"><div class="recommendation-title">Stronger peer opportunity exists</div><div class="recommendation-detail">UAE and Qatari names show relative value with similar dividend characteristics.</div></div></div>
              <div class="recommendation-card"><div class="recommendation-number">3</div><div class="recommendation-content"><div class="recommendation-title">Consider dividend-quality enhancement</div><div class="recommendation-detail">Portfolio yield (3.2%) trails GCC dividend index. Higher-quality income names available.</div></div></div>
              <div class="recommendation-card"><div class="recommendation-number">4</div><div class="recommendation-content"><div class="recommendation-title">Monitor oil beta exposure</div><div class="recommendation-detail">Energy weighting appropriate, but oil price volatility warrants ongoing review.</div></div></div>
            </div>
          </section>
        </div>
        <footer class="council-footer">
          <div class="footer-left">
            <button class="footer-btn secondary" onclick="AlphaCouncil.saveReport()"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/></svg>Save to Reports</button>
            <button class="footer-btn secondary" onclick="AlphaCouncil.askAboutReview()"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>Ask Adviser</button>
          </div>
          <div class="footer-right">
            <button class="footer-btn ghost" onclick="AlphaCouncil.showToast('Refreshing', 'Running updated analysis...', 'info')"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 4v6h-6"/><path d="M1 20v-6h6"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>Run Again</button>
            <button class="footer-btn primary" onclick="AlphaCouncil.closeCouncilModal()">Close Review</button>
          </div>
        </footer>
      </div>
    `;

    modal.addEventListener('click', (e) => {
      if (e.target === modal) closeCouncilModal();
    });

    return modal;
  }

  function saveReport() {
    showToast('Report Saved', 'Council review saved to your reports library', 'success');
  }

  function askAboutReview() {
    closeCouncilModal();
    openSidebar();
    // Route to the REAL adviser (portfolio-aware) instead of a canned summary.
    askQuestion('Summarize the key recommendations from my latest AI Analyst Council review and what I should consider doing next.');
  }

  // ============================================
  // QUICK ACTIONS
  // ============================================
  function openAddHoldingModal() {
    const modal = document.getElementById('addHoldingModal');
    if (modal) { modal.classList.add('open'); return; }
    // Fallback quick-add (the portfolio page provides a richer modal). A real
    // holding needs the ticker_key + shares + native average cost.
    const ticker = prompt('Stock ticker key (e.g. 1120_TADAWUL, 2222_TADAWUL, EMAAR_DFM):');
    if (!ticker) return;
    const shares = prompt('Number of shares:');
    if (!shares) return;
    const cost = prompt("Average cost per share (in the stock's native currency):");
    if (!cost) return;
    addHolding(ticker.trim().toUpperCase(), shares, cost);
  }

  // REAL add: POST /api/portfolio/holdings, then reload from the DB.
  async function addHolding(tickerKey, shares, avgCost) {
    if (!tickerKey) return;
    try {
      await API.addHolding(tickerKey, Number(shares), Number(avgCost));
      showToast('Holding added', String(tickerKey).split('_')[0] + ' was added to your portfolio', 'success');
      await loadPortfolio();
      if (typeof window.onPortfolioReady === 'function') window.onPortfolioReady(state.holdings);
    } catch (e) {
      showToast('Could not add holding', (e && e.message) || 'Please try again.', 'error');
    }
  }

  // REAL remove: DELETE /api/portfolio/holdings/{key}, then reload from the DB.
  async function removeHolding(tickerKey) {
    if (!confirm('Remove ' + String(tickerKey).split('_')[0] + ' from your portfolio?')) return false;
    try {
      await API.deleteHolding(tickerKey);
      showToast('Holding removed', String(tickerKey).split('_')[0] + ' was removed', 'success');
      await loadPortfolio();
      if (typeof window.onPortfolioReady === 'function') window.onPortfolioReady(state.holdings);
      return true;
    } catch (e) {
      showToast('Could not remove holding', (e && e.message) || 'Please try again.', 'error');
      return false;
    }
  }

  function openAlertModal(ticker = null) {
    let modal = document.getElementById('alertModal');
    if (!modal) {
      modal = createAlertModal();
      document.body.appendChild(modal);
    }

    if (ticker) {
      const input = modal.querySelector('#alertTicker');
      if (input) input.value = ticker;
    }

    modal.classList.add('open');
  }

  function closeAlertModal() {
    const modal = document.getElementById('alertModal');
    if (modal) modal.classList.remove('open');
  }

  function createAlertModal() {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.id = 'alertModal';
    modal.innerHTML = `
      <div class="modal" style="max-width: 480px;">
        <div class="modal-header">
          <div class="modal-title">
            <div class="modal-icon" style="background: var(--accent-primary-glow);">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color: var(--accent-primary);"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
            </div>
            <div><h2>Set Price Alert</h2><p>Get notified when conditions are met</p></div>
          </div>
          <button class="modal-close" onclick="AlphaCouncil.closeAlertModal()">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
          </button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">Stock</label>
            <input type="text" class="form-input" id="alertTicker" placeholder="e.g., 2222, ARAMCO">
          </div>
          <div class="form-group">
            <label class="form-label">Alert Type</label>
            <select class="form-input" id="alertType">
              <option value="above">Price goes above</option>
              <option value="below">Price goes below</option>
              <option value="change">Price changes by %</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Target Value</label>
            <input type="number" class="form-input" id="alertValue" placeholder="Enter target price or %">
          </div>
          <div class="modal-actions" style="display: flex; gap: 12px; margin-top: 24px;">
            <button class="btn btn-secondary" style="flex: 1;" onclick="AlphaCouncil.closeAlertModal()">Cancel</button>
            <button class="btn btn-primary" style="flex: 1;" onclick="AlphaCouncil.createAlert()">Create Alert</button>
          </div>
        </div>
      </div>
    `;

    modal.addEventListener('click', (e) => {
      if (e.target === modal) closeAlertModal();
    });

    return modal;
  }

  function createAlert() {
    const ticker = document.getElementById('alertTicker')?.value;
    const type = document.getElementById('alertType')?.value;
    const value = document.getElementById('alertValue')?.value;

    if (ticker && value) {
      closeAlertModal();
      showToast('Alert Created', `You'll be notified when ${ticker} ${type === 'above' ? 'rises above' : type === 'below' ? 'falls below' : 'changes by'} ${value}`, 'success');
    } else {
      showToast('Missing Fields', 'Please fill in all fields', 'warning');
    }
  }

  // ============================================
  // NEWS CONTEXT
  // ============================================
  function askAboutNews(newsId, headline, tickers = []) {
    state.currentNewsContext = { id: newsId, headline, tickers };
    openSidebar();
    updateSidebarContext();
    // Route to the REAL adviser (/api/adviser/ask) — no canned templates.
    const subject = (tickers && tickers.length) ? tickers.join(', ') : 'my holdings';
    askQuestion('What does this news mean for ' + subject + '? "' + headline + '"');
  }

  // ============================================
  // GLOBAL STYLES INJECTION
  // ============================================
  function injectGlobalStyles() {
    if (document.getElementById('alphaCouncilGlobalStyles')) return;

    const styleEl = document.createElement('style');
    styleEl.id = 'alphaCouncilGlobalStyles';
    styleEl.textContent = `
      /* Global Focus States for Accessibility */
      *:focus { outline: none; }
      *:focus-visible { outline: 2px solid #27D3C3; outline-offset: 2px; border-radius: 4px; }
      button:focus-visible, .btn:focus-visible, a:focus-visible { box-shadow: 0 0 0 3px rgba(39, 211, 195, 0.3); }

      /* Consistent Button Transitions */
      button, .btn, [role="button"] { transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1); }
      button:active, .btn:active { transform: scale(0.98); }
      button:disabled, .btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }

      /* Card Hover Enhancement */
      .card, .metric-card, .method-card, .news-card { transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1); }

      /* Loading States */
      .loading { pointer-events: none; opacity: 0.7; position: relative; }
      .loading::after { content: ''; position: absolute; inset: 0; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.05), transparent); animation: shimmer 1.5s infinite; }
      @keyframes shimmer { 0% { transform: translateX(-100%); } 100% { transform: translateX(100%); } }

      /* Premium Loading Spinner */
      .ac-spinner { width: 40px; height: 40px; border: 3px solid rgba(255,255,255,0.08); border-top-color: #27D3C3; border-radius: 50%; animation: ac-spin 0.8s linear infinite; }
      .ac-spinner.sm { width: 20px; height: 20px; border-width: 2px; }
      .ac-spinner.lg { width: 56px; height: 56px; border-width: 4px; }
      @keyframes ac-spin { to { transform: rotate(360deg); } }

      /* Loading Overlay */
      .ac-loading-overlay { position: absolute; inset: 0; background: rgba(7, 17, 31, 0.85); backdrop-filter: blur(8px); display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 16px; z-index: 50; border-radius: inherit; opacity: 0; visibility: hidden; transition: all 0.3s ease; }
      .ac-loading-overlay.active { opacity: 1; visibility: visible; }
      .ac-loading-text { font-size: 14px; color: #AAB6C5; text-align: center; }
      .ac-loading-text strong { color: #F8FAFC; }

      /* Empty State Styling */
      .ac-empty-state { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 48px 24px; text-align: center; }
      .ac-empty-icon { width: 64px; height: 64px; margin-bottom: 20px; background: linear-gradient(135deg, rgba(39, 211, 195, 0.15), rgba(139, 92, 246, 0.15)); border: 1px solid rgba(255,255,255,0.08); border-radius: 16px; display: flex; align-items: center; justify-content: center; }
      .ac-empty-icon svg { width: 28px; height: 28px; color: #6B7A8F; }
      .ac-empty-title { font-size: 18px; font-weight: 600; color: #F8FAFC; margin-bottom: 8px; }
      .ac-empty-text { font-size: 14px; color: #6B7A8F; max-width: 320px; line-height: 1.6; margin-bottom: 20px; }

      /* Error State Styling */
      .ac-error-state { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 32px 24px; text-align: center; background: rgba(239, 68, 68, 0.05); border: 1px solid rgba(239, 68, 68, 0.2); border-radius: 12px; }
      .ac-error-icon { width: 48px; height: 48px; margin-bottom: 16px; background: rgba(239, 68, 68, 0.15); border-radius: 12px; display: flex; align-items: center; justify-content: center; }
      .ac-error-icon svg { width: 24px; height: 24px; color: #EF4444; }
      .ac-error-title { font-size: 16px; font-weight: 600; color: #EF4444; margin-bottom: 6px; }
      .ac-error-text { font-size: 13px; color: #AAB6C5; margin-bottom: 16px; }
      .ac-error-retry { padding: 10px 20px; background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px; color: #EF4444; font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.2s; }
      .ac-error-retry:hover { background: #EF4444; color: white; }

      /* Skeleton Loading */
      .ac-skeleton { background: linear-gradient(90deg, #111A2B 25%, #1a2438 50%, #111A2B 75%); background-size: 200% 100%; animation: ac-skeleton-shimmer 1.5s infinite; border-radius: 6px; }
      .ac-skeleton-text { height: 14px; margin-bottom: 8px; }
      .ac-skeleton-text.sm { height: 12px; width: 60%; }
      .ac-skeleton-text.lg { height: 20px; }
      .ac-skeleton-circle { border-radius: 50%; }
      .ac-skeleton-card { height: 120px; border-radius: 12px; }
      @keyframes ac-skeleton-shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }

      /* Smooth Scroll Behavior */
      html { scroll-behavior: smooth; }

      /* Selection Color */
      ::selection { background: rgba(39, 211, 195, 0.3); color: #F8FAFC; }

      /* Reduced Motion Support */
      @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after { animation-duration: 0.01ms !important; animation-iteration-count: 1 !important; transition-duration: 0.01ms !important; }
        .ac-spinner { animation: none; border-top-color: #27D3C3; }
      }

      /* Logo Consistency */
      .app-logo { display: flex; align-items: center; }
      .app-logo img { height: 28px; width: auto; }

      /* Skip Link for Accessibility */
      .ac-skip-link { position: absolute; top: -100px; left: 50%; transform: translateX(-50%); padding: 12px 24px; background: #27D3C3; color: #07111F; font-weight: 600; border-radius: 0 0 8px 8px; z-index: 9999; transition: top 0.2s; }
      .ac-skip-link:focus { top: 0; }

      /* ARIA Live Region */
      .ac-live-region { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0; }

      /* Mobile Drawer Overlay */
      .ac-drawer-overlay { position: fixed; inset: 0; background: rgba(0, 0, 0, 0.6); z-index: 140; opacity: 0; visibility: hidden; transition: all 0.3s ease; }
      .ac-drawer-overlay.active { opacity: 1; visibility: visible; }

      /* Improved Table Responsiveness */
      @media (max-width: 768px) {
        .ac-responsive-table { display: block; overflow-x: auto; -webkit-overflow-scrolling: touch; }
        .ac-responsive-table table { min-width: 600px; }
        .ac-stack-mobile { display: flex; flex-direction: column; gap: 8px; }
        .ac-hide-mobile { display: none !important; }
      }
      @media (min-width: 769px) {
        .ac-hide-desktop { display: none !important; }
      }

      /* Micro-interactions */
      .ac-pulse { animation: ac-pulse 2s ease-in-out infinite; }
      @keyframes ac-pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
      .ac-bounce { animation: ac-bounce 0.5s ease; }
      @keyframes ac-bounce { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-4px); } }
      .ac-fade-in { animation: ac-fade-in 0.3s ease forwards; }
      @keyframes ac-fade-in { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }

      /* Progress Bar */
      .ac-progress { height: 4px; background: rgba(255,255,255,0.08); border-radius: 2px; overflow: hidden; }
      .ac-progress-bar { height: 100%; background: linear-gradient(90deg, #27D3C3, #8B5CF6); border-radius: 2px; transition: width 0.3s ease; }
      .ac-progress-bar.indeterminate { width: 30%; animation: ac-progress-indeterminate 1.5s infinite; }
      @keyframes ac-progress-indeterminate { 0% { transform: translateX(-100%); } 100% { transform: translateX(400%); } }
    `;
    document.head.appendChild(styleEl);
  }

  // ============================================
  // LOADING STATE HELPERS
  // ============================================
  function showLoading(container, message = 'Loading...') {
    if (!container) return;
    container.style.position = 'relative';

    let overlay = container.querySelector('.ac-loading-overlay');
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.className = 'ac-loading-overlay';
      overlay.innerHTML = `
        <div class="ac-spinner"></div>
        <div class="ac-loading-text">${message}</div>
      `;
      container.appendChild(overlay);
    } else {
      overlay.querySelector('.ac-loading-text').innerHTML = message;
    }

    requestAnimationFrame(() => overlay.classList.add('active'));
    return overlay;
  }

  function hideLoading(container) {
    if (!container) return;
    const overlay = container.querySelector('.ac-loading-overlay');
    if (overlay) {
      overlay.classList.remove('active');
      setTimeout(() => overlay.remove(), 300);
    }
  }

  function showSkeleton(container, count = 3) {
    if (!container) return;
    container.innerHTML = Array(count).fill('').map(() => `
      <div class="ac-skeleton ac-skeleton-card" style="margin-bottom: 12px;"></div>
    `).join('');
  }

  // ============================================
  // EMPTY STATE HELPERS
  // ============================================
  function showEmptyState(container, options = {}) {
    const {
      icon = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>',
      title = 'No Data',
      text = 'There is nothing to display yet.',
      action = null,
      actionText = 'Get Started'
    } = options;

    container.innerHTML = `
      <div class="ac-empty-state ac-fade-in">
        <div class="ac-empty-icon">${icon}</div>
        <h3 class="ac-empty-title">${title}</h3>
        <p class="ac-empty-text">${text}</p>
        ${action ? `<button class="btn btn-primary" onclick="${action}">${actionText}</button>` : ''}
      </div>
    `;
  }

  // ============================================
  // ERROR STATE HELPERS
  // ============================================
  function showErrorState(container, options = {}) {
    const {
      title = 'Something went wrong',
      text = 'We couldn\'t load the data. Please try again.',
      retryFn = null
    } = options;

    container.innerHTML = `
      <div class="ac-error-state ac-fade-in">
        <div class="ac-error-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M15 9l-6 6M9 9l6 6"/></svg>
        </div>
        <h3 class="ac-error-title">${title}</h3>
        <p class="ac-error-text">${text}</p>
        ${retryFn ? `<button class="ac-error-retry" onclick="${retryFn}">Try Again</button>` : ''}
      </div>
    `;
  }

  // ============================================
  // ACCESSIBILITY HELPERS
  // ============================================
  function announceToScreenReader(message) {
    let liveRegion = document.getElementById('acLiveRegion');
    if (!liveRegion) {
      liveRegion = document.createElement('div');
      liveRegion.id = 'acLiveRegion';
      liveRegion.className = 'ac-live-region';
      liveRegion.setAttribute('aria-live', 'polite');
      liveRegion.setAttribute('aria-atomic', 'true');
      document.body.appendChild(liveRegion);
    }
    liveRegion.textContent = message;
  }

  function trapFocus(element) {
    const focusableElements = element.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const firstFocusable = focusableElements[0];
    const lastFocusable = focusableElements[focusableElements.length - 1];

    function handleTab(e) {
      if (e.key !== 'Tab') return;

      if (e.shiftKey && document.activeElement === firstFocusable) {
        e.preventDefault();
        lastFocusable.focus();
      } else if (!e.shiftKey && document.activeElement === lastFocusable) {
        e.preventDefault();
        firstFocusable.focus();
      }
    }

    element.addEventListener('keydown', handleTab);
    firstFocusable?.focus();

    return () => element.removeEventListener('keydown', handleTab);
  }

  // ============================================
  // TOP NAVIGATION  (search modal, alerts + user dropdowns, settings)
  // Wired once here and applied to every page that includes this core, so the
  // header is interactive app-wide. Each piece is guarded — pages missing an
  // element are simply skipped.
  // ============================================

  // Bell dropdown is populated from the REAL per-user alerts API (/api/alerts) —
  // no hardcoded alerts. A user with no qualifying events sees an empty state.
  let _navAlerts = null;   // last fetched alert list (null = not loaded yet)

  let _navStylesInjected = false;
  function injectNavStyles() {
    if (_navStylesInjected) return;
    _navStylesInjected = true;
    const el = document.createElement('style');
    el.id = 'acNavStyles';
    el.textContent = `
      .ac-dropdown { position: fixed; min-width: 280px; max-width: 360px; background: #0B1120; border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; box-shadow: 0 16px 48px rgba(0,0,0,0.45); z-index: 400; opacity: 0; transform: translateY(-8px); pointer-events: none; transition: opacity .16s ease, transform .16s ease; overflow: hidden; }
      .ac-dropdown.open { opacity: 1; transform: translateY(0); pointer-events: auto; }
      .ac-dd-head { padding: 13px 16px; border-bottom: 1px solid rgba(255,255,255,0.08); display: flex; align-items: center; justify-content: space-between; }
      .ac-dd-head .t { font-size: 13px; font-weight: 700; color: #F8FAFC; }
      .ac-dd-head .a { font-size: 12px; color: #27D3C3; text-decoration: none; cursor: pointer; }
      .ac-dd-head .a:hover { text-decoration: underline; }
      .ac-dd-alerts { max-height: 360px; overflow-y: auto; }
      .ac-dd-alert { display: flex; gap: 11px; padding: 12px 16px; border-bottom: 1px solid rgba(255,255,255,0.05); text-decoration: none; }
      .ac-dd-alert:last-child { border-bottom: none; }
      .ac-dd-alert:hover { background: rgba(255,255,255,0.03); }
      .ac-dd-ai { width: 30px; height: 30px; border-radius: 8px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; }
      .ac-dd-ai svg { width: 16px; height: 16px; }
      .ac-dd-ai.growth { background: rgba(16,185,129,0.15); color: #10B981; }
      .ac-dd-ai.risk { background: rgba(239,68,68,0.15); color: #EF4444; }
      .ac-dd-ai.macro { background: rgba(39,211,195,0.15); color: #27D3C3; }
      .ac-dd-ai.technical { background: rgba(139,92,246,0.15); color: #8B5CF6; }
      .ac-dd-ai.value { background: rgba(245,158,11,0.15); color: #F59E0B; }
      .ac-dd-ac { min-width: 0; }
      .ac-dd-src { font-size: 12px; font-weight: 600; color: #F8FAFC; margin-bottom: 2px; display: flex; align-items: center; gap: 6px; }
      .ac-dd-src .new { font-size: 9px; font-weight: 700; text-transform: uppercase; letter-spacing: .03em; color: #27D3C3; background: rgba(39,211,195,0.15); padding: 1px 6px; border-radius: 100px; }
      .ac-dd-txt { font-size: 12px; color: #AAB6C5; line-height: 1.45; }
      .ac-dd-time { font-size: 11px; color: #6B7A8F; margin-top: 4px; }
      .ac-dd-empty { padding: 26px 16px; text-align: center; font-size: 13px; color: #6B7A8F; }
      .ac-dd-user { padding: 14px 16px; border-bottom: 1px solid rgba(255,255,255,0.08); }
      .ac-dd-user .nm { font-size: 14px; font-weight: 700; color: #F8FAFC; }
      .ac-dd-user .em { font-size: 12px; color: #6B7A8F; margin-top: 2px; word-break: break-all; }
      .ac-dd-menu { padding: 6px; }
      .ac-dd-mi { display: flex; align-items: center; gap: 12px; padding: 10px 12px; border-radius: 10px; font-size: 13px; color: #F8FAFC; text-decoration: none; cursor: pointer; background: none; border: none; width: 100%; text-align: left; font-family: inherit; }
      .ac-dd-mi:hover { background: rgba(255,255,255,0.05); }
      .ac-dd-mi svg { width: 16px; height: 16px; color: #6B7A8F; flex-shrink: 0; }
      .ac-dd-mi.danger { color: #EF4444; } .ac-dd-mi.danger svg { color: #EF4444; }
      .ac-dd-sep { height: 1px; background: rgba(255,255,255,0.08); margin: 6px 0; }
      .ac-search-overlay { position: fixed; inset: 0; background: rgba(7,17,31,0.82); backdrop-filter: blur(8px); z-index: 500; display: flex; align-items: flex-start; justify-content: center; padding-top: 12vh; opacity: 0; pointer-events: none; transition: opacity .2s; }
      .ac-search-overlay.open { opacity: 1; pointer-events: auto; }
      .ac-search-box { width: 92%; max-width: 600px; background: #0B1120; border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; box-shadow: 0 24px 64px rgba(0,0,0,0.5); overflow: hidden; transform: translateY(-12px) scale(0.98); transition: transform .2s; }
      .ac-search-overlay.open .ac-search-box { transform: translateY(0) scale(1); }
      .ac-search-top { display: flex; align-items: center; gap: 12px; padding: 16px 18px; border-bottom: 1px solid rgba(255,255,255,0.08); }
      .ac-search-top > svg { width: 20px; height: 20px; color: #6B7A8F; flex-shrink: 0; }
      .ac-search-input { flex: 1; background: none; border: none; outline: none; font-size: 16px; color: #F8FAFC; font-family: inherit; }
      .ac-search-input::placeholder { color: #6B7A8F; }
      .ac-search-kbd { font-size: 11px; color: #6B7A8F; border: 1px solid rgba(255,255,255,0.12); border-radius: 6px; padding: 2px 7px; }
      .ac-search-results { max-height: 52vh; overflow-y: auto; }
      .ac-search-result { display: flex; align-items: center; gap: 12px; padding: 12px 18px; cursor: pointer; border-bottom: 1px solid rgba(255,255,255,0.04); }
      .ac-search-result:last-child { border-bottom: none; }
      .ac-search-result:hover, .ac-search-result.active { background: rgba(39,211,195,0.08); }
      .ac-search-logo { width: 34px; height: 34px; border-radius: 9px; background: #111A2B; border: 1px solid rgba(255,255,255,0.08); display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: 700; color: #AAB6C5; flex-shrink: 0; }
      .ac-search-info { flex: 1; min-width: 0; }
      .ac-search-name { font-size: 14px; font-weight: 600; color: #F8FAFC; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
      .ac-search-tk { font-size: 12px; color: #6B7A8F; }
      .ac-search-ex { font-size: 11px; color: #27D3C3; background: rgba(39,211,195,0.1); padding: 2px 8px; border-radius: 5px; flex-shrink: 0; }
      .ac-search-msg { padding: 28px 18px; text-align: center; font-size: 13px; color: #6B7A8F; }
    `;
    document.head.appendChild(el);
  }

  // ---- dropdowns (bell + user) ----
  function acCloseDropdowns() {
    document.querySelectorAll('.ac-dropdown.open').forEach(function (d) { d.classList.remove('open'); });
  }
  function acToggleDropdown(panel, trigger) {
    const willOpen = !panel.classList.contains('open');
    acCloseDropdowns();
    if (willOpen) {
      const r = trigger.getBoundingClientRect();
      panel.style.top = (r.bottom + 8) + 'px';
      panel.style.right = Math.max(12, window.innerWidth - r.right) + 'px';
      panel.style.left = 'auto';
      panel.classList.add('open');
    }
  }

  function acAlertIcon(kind) {
    const icons = {
      growth: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 6l-9.5 9.5-5-5L1 18"/><path d="M17 6h6v6"/></svg>',
      risk: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
      technical: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20V10M18 20V4M6 20v-4"/></svg>',
      macro: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>',
      value: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>'
    };
    return icons[kind] || icons.macro;
  }

  // "x ago" from an ISO timestamp (browser-side; Date is fine here)
  function acTimeAgo(iso) {
    if (!iso) return '';
    const t = Date.parse(iso);
    if (isNaN(t)) return '';
    let s = Math.max(0, Math.floor((Date.now() - t) / 1000));
    if (s < 60) return 'just now';
    const m = Math.floor(s / 60); if (m < 60) return m + 'm ago';
    const h = Math.floor(m / 60); if (h < 24) return h + 'h ago';
    const d = Math.floor(h / 24); if (d < 30) return d + 'd ago';
    return Math.floor(d / 30) + 'mo ago';
  }

  // Bell badge — driven by the REAL unread count (hidden at 0 / signed out / error).
  function setAlertBadge(n) {
    const badge = document.querySelector('#notificationsBtn .badge');
    const bell = document.getElementById('notificationsBtn');
    if (badge) {
      if (n && n > 0) { badge.textContent = n > 99 ? '99+' : String(n); badge.style.display = ''; }
      else { badge.style.display = 'none'; }
    }
    if (bell) bell.setAttribute('aria-label', (n && n > 0) ? ('Notifications, ' + n + ' unread') : 'Notifications');
  }
  function refreshAlertBadge() {
    const badge = document.querySelector('#notificationsBtn .badge');
    if (badge) badge.style.display = 'none';  // hide the static placeholder until the real count loads
    if (!window.API || !API.alertsUnread) return;
    API.alertsUnread().then(function (r) { setAlertBadge(r && r.unread ? r.unread : 0); })
      .catch(function () { setAlertBadge(0); });
  }

  // Real avatar initials from the signed-in user (no display name yet → derive from
  // email local-part). Never a hardcoded "SK".
  function initialsFromUser(u) {
    u = u || {};
    let src = String(u.name || u.username || u.full_name || '').trim();
    if (!src) src = String(u.email || '').split('@')[0];
    if (!src) return '';
    const parts = src.split(/[\s._-]+/).filter(Boolean);
    const ini = parts.length >= 2 ? (parts[0][0] + parts[1][0]) : src.slice(0, 2);
    return ini.toUpperCase();
  }
  // Set the top-bar avatar to the real user's initials + an honest aria-label.
  function setNavIdentity(u) {
    const menu = document.getElementById('userMenu');
    if (!menu) return;
    const ini = initialsFromUser(u);
    menu.textContent = ini;
    menu.setAttribute('aria-label', u && u.email ? ('User menu for ' + u.email) : 'User menu');
  }

  function renderNavAlerts(list) {
    const box = document.getElementById('acAlertsList');
    if (!box) return;
    if (list === null) { box.innerHTML = '<div class="ac-dd-empty">Couldn’t load alerts.</div>'; return; }
    if (!list.length) {
      box.innerHTML = '<div class="ac-dd-empty">No alerts yet. We’ll flag notable moves, signals and news on your holdings here.</div>';
      return;
    }
    box.innerHTML = list.slice(0, 8).map(function (a) {
      const href = a.url || 'alerts.html';
      return '<a class="ac-dd-alert" href="' + escapeHtml(href) + '">'
        + '<div class="ac-dd-ai ' + escapeHtml(a.kind || 'macro') + '">' + acAlertIcon(a.kind) + '</div>'
        + '<div class="ac-dd-ac"><div class="ac-dd-src">' + escapeHtml(a.source || 'Alert') + (a.read ? '' : '<span class="new">New</span>') + '</div>'
        + '<div class="ac-dd-txt">' + escapeHtml(a.title || a.body || '') + '</div>'
        + '<div class="ac-dd-time">' + escapeHtml(acTimeAgo(a.created_at)) + '</div></div></a>';
    }).join('');
  }

  function buildAlertsDropdown() {
    let panel = document.getElementById('acAlertsDropdown');
    if (panel) return panel;
    panel = document.createElement('div');
    panel.className = 'ac-dropdown';
    panel.id = 'acAlertsDropdown';
    panel.setAttribute('role', 'menu');
    panel.innerHTML = '<div class="ac-dd-head"><span class="t">Alerts</span><a class="a" href="alerts.html">View all</a></div>'
      + '<div class="ac-dd-alerts" id="acAlertsList"><div class="ac-dd-empty">Loading…</div></div>';
    panel.addEventListener('click', function (e) { e.stopPropagation(); });
    document.body.appendChild(panel);
    return panel;
  }

  // Open the bell dropdown: fetch the real alerts, render them, and mark them
  // read (which clears the badge — "they disappear when the user checks them").
  function openAlertsDropdown(bell) {
    const panel = buildAlertsDropdown();
    const wasOpen = panel.classList.contains('open');
    acToggleDropdown(panel, bell);
    if (wasOpen) return;                       // we just closed it
    if (!window.API || !API.alerts) { renderNavAlerts(null); return; }
    if (_navAlerts) renderNavAlerts(_navAlerts);   // show cached instantly if we have it
    API.alerts(8).then(function (r) {
      _navAlerts = (r && r.alerts) ? r.alerts : [];
      const hadUnread = _navAlerts.some(function (a) { return !a.read; });
      renderNavAlerts(_navAlerts);
      // opening the bell = seen → mark read + clear the badge
      if (hadUnread && API.markAlertsRead) {
        API.markAlertsRead().then(function () { setAlertBadge(0); }).catch(function () {});
      } else {
        setAlertBadge(0);
      }
    }).catch(function () { renderNavAlerts(_navAlerts || null); });
  }

  function buildUserDropdown() {
    let panel = document.getElementById('acUserDropdown');
    if (!panel) {
      panel = document.createElement('div');
      panel.className = 'ac-dropdown';
      panel.id = 'acUserDropdown';
      panel.style.minWidth = '240px';
      panel.setAttribute('role', 'menu');
      panel.addEventListener('click', function (e) { e.stopPropagation(); });
      document.body.appendChild(panel);
    }
    const u = state.user || {};
    const name = u.username || u.name || u.full_name || 'Your account';
    const email = u.email || '';
    panel.innerHTML =
      '<div class="ac-dd-user"><div class="nm">' + escapeHtml(name) + '</div>' + (email ? '<div class="em">' + escapeHtml(email) + '</div>' : '') + '</div>'
      + '<div class="ac-dd-menu">'
      + '<a class="ac-dd-mi" href="settings.html" role="menuitem"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>Profile &amp; Account</a>'
      + '<a class="ac-dd-mi" href="settings.html" role="menuitem"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>Settings</a>'
      + '<div class="ac-dd-sep"></div>'
      + '<button class="ac-dd-mi danger" type="button" role="menuitem" onclick="AlphaCouncil.logout()"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>Log out</button>'
      + '</div>';
    return panel;
  }

  function logout() {
    acCloseDropdowns();
    const done = function () { window.location.href = 'index.html'; };
    if (window.API && API.logout) { API.logout().then(done).catch(done); } else { done(); }
  }

  // ---- search modal (live stock search → stock-detail) ----
  let _searchUniverse = null;
  let _searchLoading = false;
  function buildSearchModal() {
    let overlay = document.getElementById('acSearchOverlay');
    if (overlay) return overlay;
    overlay = document.createElement('div');
    overlay.className = 'ac-search-overlay';
    overlay.id = 'acSearchOverlay';
    overlay.innerHTML =
      '<div class="ac-search-box" role="dialog" aria-label="Search stocks">'
      + '<div class="ac-search-top">'
      + '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>'
      + '<input type="text" class="ac-search-input" id="acSearchInput" placeholder="Search GCC stocks (e.g., Aramco, Al Rajhi, QNB...)" autocomplete="off" aria-label="Search stocks">'
      + '<kbd class="ac-search-kbd">ESC</kbd>'
      + '</div>'
      + '<div class="ac-search-results" id="acSearchResults"><div class="ac-search-msg">Start typing to search GCC stocks…</div></div>'
      + '</div>';
    overlay.addEventListener('click', function (e) { if (e.target === overlay) closeSearchModal(); });
    const input = overlay.querySelector('#acSearchInput');
    input.addEventListener('input', function () { renderSearchResults(input.value); });
    input.addEventListener('keydown', function (e) { if (e.key === 'Enter') { e.preventDefault(); goToFirstSearchResult(); } });
    document.body.appendChild(overlay);
    return overlay;
  }
  function openSearchModal() {
    const overlay = buildSearchModal();
    overlay.classList.add('open');
    document.body.style.overflow = 'hidden';
    const input = document.getElementById('acSearchInput');
    setTimeout(function () { if (input) input.focus(); }, 30);
    loadSearchUniverse();
  }
  function closeSearchModal() {
    const overlay = document.getElementById('acSearchOverlay');
    if (overlay) { overlay.classList.remove('open'); document.body.style.overflow = ''; }
  }
  async function loadSearchUniverse() {
    if (_searchUniverse || _searchLoading || !window.API) return;
    _searchLoading = true;
    try {
      const resp = await API.screening();
      const data = (resp && resp.data) ? resp.data : (Array.isArray(resp) ? resp : []);
      _searchUniverse = data.map(function (s) {
        return { ticker: s.ticker, tickerKey: s.ticker_key || s.ticker, name: s.name_en || s.ticker, exchange: s.exchange || '' };
      });
    } catch (e) { _searchUniverse = null; }
    _searchLoading = false;
    const input = document.getElementById('acSearchInput');
    if (input && input.value) renderSearchResults(input.value);
  }
  function searchMatches(q) {
    if (!_searchUniverse) return [];
    q = String(q).trim().toLowerCase();
    if (!q) return [];
    return _searchUniverse.filter(function (s) {
      return (s.name && s.name.toLowerCase().indexOf(q) !== -1)
        || (s.ticker && String(s.ticker).toLowerCase().indexOf(q) !== -1)
        || (s.tickerKey && String(s.tickerKey).toLowerCase().indexOf(q) !== -1);
    }).slice(0, 8);
  }
  function renderSearchResults(q) {
    const box = document.getElementById('acSearchResults');
    if (!box) return;
    const query = (q || '').trim();
    if (!query) { box.innerHTML = '<div class="ac-search-msg">Start typing to search GCC stocks…</div>'; return; }
    if (!_searchUniverse) { box.innerHTML = '<div class="ac-search-msg">' + (_searchLoading ? 'Loading stocks…' : 'Search is unavailable right now — please try again.') + '</div>'; return; }
    const results = searchMatches(query);
    if (!results.length) { box.innerHTML = '<div class="ac-search-msg">No stocks match “' + escapeHtml(query) + '”.</div>'; return; }
    box.innerHTML = results.map(function (s, i) {
      const short = String(s.ticker || s.tickerKey).split('_')[0].split('.')[0].slice(0, 4);
      return '<div class="ac-search-result' + (i === 0 ? ' active' : '') + '" data-ticker="' + escapeHtml(s.tickerKey) + '">'
        + '<div class="ac-search-logo">' + escapeHtml(short) + '</div>'
        + '<div class="ac-search-info"><div class="ac-search-name">' + escapeHtml(s.name) + '</div><div class="ac-search-tk">' + escapeHtml(s.ticker || s.tickerKey) + '</div></div>'
        + (s.exchange ? '<span class="ac-search-ex">' + escapeHtml(s.exchange) + '</span>' : '')
        + '</div>';
    }).join('');
    box.querySelectorAll('.ac-search-result').forEach(function (el) {
      el.addEventListener('click', function () { goToStock(el.getAttribute('data-ticker')); });
    });
  }
  function goToFirstSearchResult() {
    const first = document.querySelector('#acSearchResults .ac-search-result');
    if (first) goToStock(first.getAttribute('data-ticker'));
  }
  function goToStock(tickerKey) {
    if (!tickerKey) return;
    window.location.href = 'stock-detail.html?ticker=' + encodeURIComponent(tickerKey);
  }

  // ---- wire it all up (called from init) ----
  let _navWired = false;
  function initTopNav() {
    if (_navWired) return; // guard against double-init
    _navWired = true;
    injectNavStyles();

    const searchBtn = document.getElementById('searchBtn');
    if (searchBtn) {
      searchBtn.style.cursor = 'pointer';
      searchBtn.setAttribute('role', 'button');
      searchBtn.setAttribute('tabindex', '0');
      searchBtn.setAttribute('aria-label', 'Search stocks');
      searchBtn.addEventListener('click', openSearchModal);
      searchBtn.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openSearchModal(); } });
    }

    const bell = document.getElementById('notificationsBtn');
    if (bell) {
      bell.style.cursor = 'pointer';
      bell.setAttribute('aria-haspopup', 'true');
      bell.addEventListener('click', function (e) { e.stopPropagation(); openAlertsDropdown(bell); });
      refreshAlertBadge();  // load the REAL unread count on every page (hides the static placeholder)
    }

    const settingsBtn = document.getElementById('settingsBtn') || document.querySelector('.app-nav-right button[aria-label="Settings"]');
    if (settingsBtn) {
      settingsBtn.style.cursor = 'pointer';
      settingsBtn.addEventListener('click', function () { window.location.href = 'settings.html'; });
    }

    const userMenu = document.getElementById('userMenu');
    if (userMenu) {
      userMenu.style.cursor = 'pointer';
      userMenu.addEventListener('click', function (e) { e.stopPropagation(); acToggleDropdown(buildUserDropdown(), userMenu); });
    }

    // Close dropdowns on outside click / Escape; "/" focuses search; Esc closes search.
    document.addEventListener('click', acCloseDropdowns);
    window.addEventListener('resize', acCloseDropdowns);
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') { acCloseDropdowns(); closeSearchModal(); return; }
      const tag = (e.target && e.target.tagName ? e.target.tagName : '').toLowerCase();
      const typing = tag === 'input' || tag === 'textarea' || tag === 'select' || (e.target && e.target.isContentEditable);
      if (e.key === '/' && !typing) { e.preventDefault(); openSearchModal(); }
    });
  }

  // ============================================
  // MARKET TAPE — live scrolling ticker (every app page with .indices-bar)
  // Built from the REAL /api/ticker-tape feed: each market's index (TASI/ADX/DFM
  // where we have one) followed by EVERY stock we have a live price for in that
  // market, looping across all markets. Static placeholders are dropped, never
  // scrolled. Seamless right-to-left marquee (tile to ≥ bar width, translateX
  // -50%, infinite, linear, constant px/s, pauses on hover). "—" if the feed is down.
  // ============================================
  let _tickerItems = null;          // array of <div.index-item> built from real data
  let _tickerResizeTimer = null;
  const INDICES_FALLBACK = [{ market: 'TASI' }, { market: 'ADX' }, { market: 'DFM' }];

  function _indexItemEl(d) {
    const item = document.createElement('div');
    item.className = 'index-item';
    const name = document.createElement('span');
    name.className = 'index-name';
    name.textContent = String(d.market || d.name_en || d.name || '');
    const val = document.createElement('span');
    val.className = 'index-value';
    val.textContent = (d.price != null && isFinite(d.price))
      ? Number(d.price).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
      : '—';
    item.appendChild(name);
    item.appendChild(val);
    if (d.change_pct != null && isFinite(d.change_pct)) {
      const up = Number(d.change_pct) >= 0;
      const chg = document.createElement('span');
      chg.className = 'index-change ' + (up ? 'up' : 'down');
      chg.textContent = (up ? '+' : '') + Number(d.change_pct).toFixed(2) + '%';
      item.appendChild(chg);
    }
    return item;
  }

  // One stock cell: ticker + price + day change (same visual style as an index).
  function _stockEl(s) {
    const item = document.createElement('div');
    item.className = 'index-item';
    const name = document.createElement('span');
    name.className = 'index-name';
    name.textContent = String(s.t || '');
    item.appendChild(name);
    if (s.p != null && isFinite(s.p)) {
      const val = document.createElement('span');
      val.className = 'index-value';
      val.textContent = Number(s.p).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
      item.appendChild(val);
    }
    if (s.c != null && isFinite(s.c)) {
      const up = Number(s.c) >= 0;
      const chg = document.createElement('span');
      chg.className = 'index-change ' + (up ? 'up' : 'down');
      chg.textContent = (up ? '+' : '') + Number(s.c).toFixed(2) + '%';
      item.appendChild(chg);
    }
    return item;
  }

  // A market header (accent name + index value/change where we have one), shown
  // before that market's run of stocks so the eye can tell markets apart.
  function _marketHeadEl(g) {
    const item = document.createElement('div');
    item.className = 'index-item index-market';
    const name = document.createElement('span');
    name.className = 'index-name index-market-name';
    name.textContent = String(g.market || '');
    item.appendChild(name);
    const ix = g.index;
    if (ix && ix.price != null && isFinite(ix.price)) {
      const val = document.createElement('span');
      val.className = 'index-value';
      val.textContent = Number(ix.price).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
      item.appendChild(val);
      if (ix.change_pct != null && isFinite(ix.change_pct)) {
        const up = Number(ix.change_pct) >= 0;
        const chg = document.createElement('span');
        chg.className = 'index-change ' + (up ? 'up' : 'down');
        chg.textContent = (up ? '+' : '') + Number(ix.change_pct).toFixed(2) + '%';
        item.appendChild(chg);
      }
    }
    return item;
  }

  // Flatten the tape into ordered cells: [market, ...its stocks, market, ...].
  function _buildItemsFromTape(groups) {
    const items = [];
    groups.forEach(function (g) {
      items.push(_marketHeadEl(g));
      (g.stocks || []).forEach(function (s) { items.push(_stockEl(s)); });
    });
    return items;
  }

  function _buildTicker() {
    const bar = document.querySelector('.indices-bar');
    if (!bar || !_tickerItems || !_tickerItems.length) return;
    const inner = bar.querySelector('.indices-inner');
    if (!inner) return;
    function baseFrag() {
      const frag = document.createDocumentFragment();
      _tickerItems.forEach(function (it) {
        frag.appendChild(it.cloneNode(true));
        const sep = document.createElement('span');
        sep.className = 'index-sep';
        sep.setAttribute('aria-hidden', 'true');
        sep.textContent = '/';
        frag.appendChild(sep);
      });
      return frag;
    }
    const track = document.createElement('div');
    track.className = 'indices-track';
    inner.innerHTML = '';
    inner.appendChild(track);
    bar.classList.add('is-ticker');
    track.appendChild(baseFrag());   // one base copy to measure
    // Measure AFTER layout (rAF) — a synchronous scrollWidth read can return 0
    // before the appended copy is laid out, which would over-tile.
    requestAnimationFrame(function () {
      const baseWidth = Math.max(120, track.scrollWidth || track.getBoundingClientRect().width || 1);
      const barWidth = bar.clientWidth || window.innerWidth || 1;
      // copies per half so each half ≥ bar width (seamless, no gap); capped so a
      // bad measurement can never run away.
      const perHalf = Math.min(8, Math.max(1, Math.ceil(barWidth / baseWidth) + 1));
      for (let i = 1; i < perHalf * 2; i++) track.appendChild(baseFrag());
      // Constant, readable PIXEL speed — the tape can be hundreds of stocks long,
      // so pace by px/s (not a fixed cycle time): each cell stays on screen long
      // enough to read. The full loop just takes as long as it takes.
      const speed = barWidth < 768 ? 85 : 65;   // px per second (a touch faster on mobile)
      track.style.animationDuration = Math.max(20, Math.round((perHalf * baseWidth) / speed)) + 's';
    });
  }

  function initIndicesTicker() {
    const bar = document.querySelector('.indices-bar');
    if (!bar) return;
    const inner = bar.querySelector('.indices-inner');
    if (inner) inner.innerHTML = '';   // drop the static placeholders immediately (no fake flash)

    function apply(tape) {
      const groups = (tape && tape.groups && tape.groups.length) ? tape.groups : null;
      _tickerItems = groups ? _buildItemsFromTape(groups) : INDICES_FALLBACK.map(_indexItemEl);
      _buildTicker();
      // Honest freshness label, kept OUTSIDE the wiped marquee track. The index
      // values come from a periodic fetch, not a live tick — never label it "Live".
      let t = bar.querySelector('.indices-time');
      if (!t || (inner && inner.contains(t))) {
        t = document.createElement('span');
        t.className = 'indices-time';
        bar.appendChild(t);
      }
      let label = 'Market data';
      if (tape && tape.as_of) {
        const d = new Date(tape.as_of);
        if (!isNaN(d.getTime())) label = 'As of ' + d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
      }
      t.textContent = label;
    }
    if (window.API && API.tickerTape) {
      API.tickerTape().then(apply).catch(function () { apply(null); });  // "—" until the real feed returns
    } else {
      apply(null);
    }
    // re-tile when webfonts settle (widths shift) and on viewport changes
    // (reuses _tickerItems — no-ops until the feed has populated them).
    if (document.fonts && document.fonts.ready && document.fonts.ready.then) {
      document.fonts.ready.then(_buildTicker);
    }
    window.addEventListener('resize', function () {
      clearTimeout(_tickerResizeTimer);
      _tickerResizeTimer = setTimeout(_buildTicker, 250);
    });
  }

  // Point the brand logo at the right home: the dashboard when signed in, the
  // marketing index when not. (Clicking the logo on an app page used to drop you
  // onto the logged-out marketing page — which looked like being logged out.)
  // `known` overrides the cookie best-guess once /auth/me has resolved.
  function wireBrandLogo(known) {
    const loggedIn = (known === undefined)
      ? !!(window.API && API.getCookie && API.getCookie('ac_csrf'))
      : !!known;
    const href = loggedIn ? 'dashboard.html' : 'index.html';
    document.querySelectorAll('a.app-logo, a.header-logo, a.footer-logo, a.nav-logo, a.ac-flogo').forEach(function (a) {
      a.setAttribute('href', href);
    });
  }

  // ============================================
  // INITIALIZATION
  // ============================================
  function init(page = 'dashboard') {
    state.currentPage = page;

    // Inject global styles
    injectGlobalStyles();

    // Brand logo → dashboard (signed in) / index (signed out). Best-guess now
    // from the ac_csrf cookie, then confirmed once /auth/me resolves below.
    wireBrandLogo();

    // Load the REAL signed-in user + their holdings from the live backend. Pages
    // that render holdings can define window.onPortfolioReady(holdings) to re-draw
    // once the data arrives (no fake data is ever shown).
    if (window.API) {
      API.loadUser().then(function (u) {
        state.user = u;
        wireBrandLogo(!!u);   // definitive: real auth state
        setNavIdentity(u);    // real avatar initials, never "SK"
        if (typeof window.onUserReady === 'function') window.onUserReady(u);
      });
      loadPortfolio().then(function () {
        if (typeof window.onPortfolioReady === 'function') window.onPortfolioReady(state.holdings);
      });
    }

    // Wire up adviser toggle
    const adviserToggle = document.getElementById('adviserToggle');
    if (adviserToggle) {
      adviserToggle.addEventListener('click', toggleSidebar);
    }

    // Wire up the top navigation (search, alerts bell, settings, user menu)
    initTopNav();

    // Turn the static market-indices row into a live scrolling ticker
    initIndicesTicker();

    // Wire up close sidebar
    const closeSidebar = document.getElementById('closeSidebar');
    if (closeSidebar) {
      closeSidebar.addEventListener('click', toggleSidebar);
    }

    // Wire up chat
    const chatSend = document.getElementById('chatSend');
    const chatInput = document.getElementById('chatInput');
    if (chatSend) {
      chatSend.addEventListener('click', processChat);
    }
    if (chatInput) {
      chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          processChat();
        }
      });
    }

    // Wire up suggested questions
    document.querySelectorAll('.suggested-question').forEach(btn => {
      btn.addEventListener('click', () => {
        const question = btn.dataset?.question || btn.textContent;
        askQuestion(question);
      });
    });

    // Update context
    updateSidebarContext();

    // Keyboard shortcut to close modal
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        closeCouncilModal();
        closeAlertModal();
      }
    });

    console.log('AlphaCouncil initialized for:', page);
  }

  // ============================================
  // DIMENSION EXPLANATIONS (for Stock Detail page)
  // ============================================
  function askAboutDimension(dimensionName, stockName, stockTicker) {
    openSidebar();
    // Route to the REAL adviser — explanations come from live fundamentals, not a map.
    askQuestion('Explain the ' + dimensionName + ' dimension of the investment thesis for ' + stockName + ' (' + stockTicker + ') using its real fundamentals.');
  }

  // ============================================
  // COMPATIBILITY SHIMS (the pages' inline JS expects these globals from the old
  // orphaned core; provide REAL-data-backed equivalents so nothing is fake/broken)
  // ============================================
  function formatCurrency(value, currency) {
    currency = currency || 'SAR';
    const n = Number(value);
    if (!isFinite(n)) return '—';
    return currency + ' ' + n.toLocaleString('en-US', { maximumFractionDigits: 0 });
  }
  function formatPercent(value, includeSign) {
    const n = Number(value);
    if (!isFinite(n)) return '—';
    const sign = (includeSign === false) ? '' : (n >= 0 ? '+' : '');
    return sign + n.toFixed(2) + '%';
  }
  if (typeof window !== 'undefined') {
    if (!window.$) window.$ = function (s, c) { return (c || document).querySelector(s); };
    if (!window.$$) window.$$ = function (s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); };
    window.openSidebar = openSidebar;
    window.closeSidebar = closeSidebar;
    window.askQuestion = askQuestion;
    window.formatCurrency = formatCurrency;
    window.formatPercent = formatPercent;
    window.openModal = function (sel) { const m = typeof sel === 'string' ? document.querySelector(sel) : sel; if (m) { m.classList.add('open'); document.body.style.overflow = 'hidden'; } };
    window.closeModal = function (sel) { const m = typeof sel === 'string' ? document.querySelector(sel) : sel; if (m) { m.classList.remove('open'); document.body.style.overflow = ''; } };
    // Real-data-backed DemoData shim (reads the loaded holdings; never fabricates).
    window.DemoData = {
      getHoldings: function () { return state.holdings; },
      getHolding: function (t) { return state.holdings.filter(function (h) { return h.ticker === t || h.tickerKey === t; })[0] || null; },
      seed: function () {}, addHolding: function () {}, updateHolding: function () {}, removeHolding: function () {}
    };
  }

  // ============================================
  // PUBLIC API
  // ============================================
  return {
    init,
    state,
    formatCurrency,
    formatPercent,
    showToast,
    toggleSidebar,
    openSidebar,
    closeSidebar,
    setPageContext,
    setStockContext: (stock) => {
      state.currentStock = stock;
      updateSidebarContext();
    },
    clearNewsContext,
    askQuestion,
    addChatMessage,
    processChat,
    openCouncilModal,
    closeCouncilModal,
    saveReport,
    askAboutReview,
    openAddHoldingModal,
    addHolding,
    removeHolding,
    openAlertModal,
    closeAlertModal,
    createAlert,
    // Top nav
    openSearchModal,
    closeSearchModal,
    logout,
    askAboutNews,
    askAboutDimension,
    getHoldings: () => state.holdings,
    getUser: () => state.user,
    loadPortfolio,
    runCouncil,
    // Loading, Empty, Error state helpers
    showLoading,
    hideLoading,
    showSkeleton,
    showEmptyState,
    showErrorState,
    // Accessibility helpers
    announceToScreenReader,
    trapFocus
  };
})();

// Make it globally available
window.AlphaCouncil = AlphaCouncil;

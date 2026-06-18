// =============================================
// DEPRECATED: This file is no longer in use.
// All functionality has been consolidated into adviser-core.js
// Please use adviser-core.js as the single source of truth.
// This file will be removed in a future cleanup.
// FINAL CLEANUP: 2026-06-17
// =============================================

/**
 * AlphaCouncil Core JavaScript
 * Version: 2.0.0 (DEPRECATED)
 *
 * Unified namespace providing all shared functionality across the platform.
 * Includes: state management, sidebar control, toasts, utilities, accessibility,
 * loading states, demo data, event system, and page-specific hooks.
 *
 * REFACTORED: Priorities 1-8 completed. Ready for wiring phase.
 */

(function(global) {
  'use strict';

  // Prevent multiple initializations
  if (global.AlphaCouncil && global.AlphaCouncil._initialized) {
    return;
  }

  // ==========================================================================
  // CONFIGURATION
  // ==========================================================================

  const CONFIG = {
    STORAGE_PREFIX: 'alphacouncil_',
    TOAST_DURATION: 4000,
    ANIMATION_DURATION: 300,
    DEBOUNCE_DELAY: 250,
    MAX_CHAT_HISTORY: 50,
    TYPING_DELAY: { min: 600, max: 1200 },
    VERSION: '2.0.0',
    DEBUG: new URLSearchParams(window.location.search).get('debug') === 'true'
  };

  // Debug logger
  function log(...args) {
    if (CONFIG.DEBUG) {
      console.log('[AlphaCouncil]', ...args);
    }
  }

  // ==========================================================================
  // EVENT SYSTEM
  // ==========================================================================

  const Events = {
    _listeners: {},

    /**
     * Register an event listener
     * @param {string} event - Event name
     * @param {Function} callback - Callback function
     */
    on(event, callback) {
      if (!this._listeners[event]) {
        this._listeners[event] = [];
      }
      this._listeners[event].push(callback);
      log('Event listener registered:', event);
    },

    /**
     * Remove an event listener
     * @param {string} event - Event name
     * @param {Function} callback - Callback function
     */
    off(event, callback) {
      if (!this._listeners[event]) return;
      this._listeners[event] = this._listeners[event].filter(cb => cb !== callback);
    },

    /**
     * Emit an event
     * @param {string} event - Event name
     * @param {*} data - Event data
     */
    emit(event, data) {
      log('Event emitted:', event, data);
      if (this._listeners[event]) {
        this._listeners[event].forEach(cb => {
          try {
            cb(data);
          } catch (e) {
            console.error('[AlphaCouncil] Event handler error:', e);
          }
        });
      }
      // Also dispatch as CustomEvent for external listeners
      document.dispatchEvent(new CustomEvent(`alphacouncil:${event}`, { detail: data }));
    }
  };

  // ==========================================================================
  // STATE MANAGEMENT
  // ==========================================================================

  const State = {
    _cache: {},

    get(key, defaultValue = null) {
      if (this._cache.hasOwnProperty(key)) {
        return this._cache[key];
      }
      try {
        const stored = localStorage.getItem(CONFIG.STORAGE_PREFIX + key);
        if (stored !== null) {
          const parsed = JSON.parse(stored);
          this._cache[key] = parsed;
          return parsed;
        }
      } catch (e) {
        log('State.get error:', e);
      }
      return defaultValue;
    },

    set(key, value) {
      this._cache[key] = value;
      try {
        localStorage.setItem(CONFIG.STORAGE_PREFIX + key, JSON.stringify(value));
        Events.emit('state:change', { key, value });
      } catch (e) {
        log('State.set error:', e);
      }
    },

    remove(key) {
      delete this._cache[key];
      try {
        localStorage.removeItem(CONFIG.STORAGE_PREFIX + key);
        Events.emit('state:change', { key, value: null });
      } catch (e) {
        log('State.remove error:', e);
      }
    },

    clear() {
      this._cache = {};
      try {
        Object.keys(localStorage)
          .filter(k => k.startsWith(CONFIG.STORAGE_PREFIX))
          .forEach(k => localStorage.removeItem(k));
        Events.emit('state:clear', {});
      } catch (e) {
        log('State.clear error:', e);
      }
    }
  };

  // ==========================================================================
  // DEMO DATA SEEDING
  // ==========================================================================

  const DemoData = {
    holdings: [
      { ticker: '2222', name: 'Saudi Aramco', company: 'Saudi Arabian Oil Company', exchange: 'Tadawul · Energy', sector: 'Energy', shares: 5470, avgCost: 28.15, currentPrice: 28.90, weight: 18.4, thesis: 8.4, pnl: 12.3, currency: 'SAR' },
      { ticker: '1120', name: 'Al Rajhi Bank', company: 'Al Rajhi Banking & Investment Corp', exchange: 'Tadawul · Banking', sector: 'Financials', shares: 1412, avgCost: 78.40, currentPrice: 85.20, weight: 14.2, thesis: 8.1, pnl: 8.7, currency: 'SAR' },
      { ticker: '7010', name: 'stc', company: 'Saudi Telecom Company', exchange: 'Tadawul · Telecom', sector: 'Communications', shares: 2380, avgCost: 40.15, currentPrice: 42.10, weight: 11.8, thesis: 7.2, pnl: 5.2, currency: 'SAR' },
      { ticker: 'QNBK', name: 'QNB Group', company: 'Qatar National Bank', exchange: 'QSE · Banking', sector: 'Financials', shares: 4340, avgCost: 17.52, currentPrice: 18.72, weight: 9.6, thesis: 7.9, pnl: 6.8, currency: 'QAR' },
      { ticker: 'FAB', name: 'First Abu Dhabi Bank', company: 'First Abu Dhabi Bank PJSC', exchange: 'ADX · Banking', sector: 'Financials', shares: 4800, avgCost: 14.35, currentPrice: 14.85, weight: 8.4, thesis: 7.4, pnl: 3.9, currency: 'AED' },
      { ticker: '2010', name: 'SABIC', company: 'Saudi Basic Industries Corp', exchange: 'Tadawul · Materials', sector: 'Materials', shares: 698, avgCost: 91.20, currentPrice: 87.40, weight: 7.2, thesis: 5.8, pnl: -4.1, currency: 'SAR' },
      { ticker: 'EMAAR', name: 'Emaar Properties', company: 'Emaar Properties PJSC', exchange: 'DFM · Real Estate', sector: 'Real Estate', shares: 5780, avgCost: 9.15, currentPrice: 8.95, weight: 6.1, thesis: 6.5, pnl: -2.3, currency: 'AED' }
    ],

    scenarios: [
      { id: 'sc1', name: 'Base Case', description: 'Current portfolio with market-rate assumptions', return: 8.2, risk: 14.5, sharpe: 1.2, isActive: true },
      { id: 'sc2', name: 'Oil Bull', description: 'Brent rises to $95-100, benefiting energy exposure', return: 12.4, risk: 16.8, sharpe: 1.4, isActive: false },
      { id: 'sc3', name: 'Rate Cut Rally', description: 'GCC central banks follow Fed with 75bps cuts', return: 10.1, risk: 13.2, sharpe: 1.5, isActive: false },
      { id: 'sc4', name: 'Risk-Off', description: 'Global risk aversion, flight to quality', return: -2.3, risk: 22.1, sharpe: -0.2, isActive: false }
    ],

    alerts: [
      { id: 'a1', type: 'growth', ticker: '1120', headline: 'Al Rajhi Bank Q2 results: 14% earnings growth ahead of consensus', time: '2h ago', isNew: true },
      { id: 'a2', type: 'risk', ticker: '2010', headline: 'SABIC concentration (7.2%) exceeds peer average', time: '4h ago', isNew: false },
      { id: 'a3', type: 'macro', ticker: '2222', headline: 'Brent crude below $83 — oil-linked exposure (26%) monitoring', time: '6h ago', isNew: false },
      { id: 'a4', type: 'value', ticker: 'QNBK', headline: 'QNB trades at 1.4x book — below 5-year average', time: '1d ago', isNew: false },
      { id: 'a5', type: 'technical', ticker: '7010', headline: 'stc approaching 200-day MA support at SAR 38.50', time: '1d ago', isNew: false }
    ],

    seed() {
      if (!State.get('holdings')) {
        State.set('holdings', this.holdings);
        log('Demo holdings seeded');
      }
      if (!State.get('scenarios')) {
        State.set('scenarios', this.scenarios);
        log('Demo scenarios seeded');
      }
      if (!State.get('alerts')) {
        State.set('alerts', this.alerts);
        log('Demo alerts seeded');
      }
      if (!State.get('demo_seeded')) {
        State.set('demo_seeded', true);
        State.set('demo_seed_date', new Date().toISOString());
      }
    },

    reset() {
      State.set('holdings', this.holdings);
      State.set('scenarios', this.scenarios);
      State.set('alerts', this.alerts);
      State.set('chat_history', []);
      State.remove('sidebar_context');
      State.set('demo_seeded', true);
      State.set('demo_seed_date', new Date().toISOString());
      Events.emit('demo:reset', {});
      showToast('Demo Reset', 'All demo data has been restored to defaults.', 'success');
      log('Demo data reset');
    },

    getHoldings() {
      return State.get('holdings', this.holdings);
    },

    getScenarios() {
      return State.get('scenarios', this.scenarios);
    },

    getAlerts() {
      return State.get('alerts', this.alerts);
    },

    getHolding(ticker) {
      const holdings = this.getHoldings();
      return holdings.find(h => h.ticker === ticker);
    },

    updateHolding(ticker, updates) {
      const holdings = this.getHoldings();
      const index = holdings.findIndex(h => h.ticker === ticker);
      if (index !== -1) {
        holdings[index] = { ...holdings[index], ...updates };
        State.set('holdings', holdings);
        Events.emit('holdings:update', { ticker, holding: holdings[index] });
      }
    },

    addHolding(holding) {
      const holdings = this.getHoldings();
      holdings.push(holding);
      State.set('holdings', holdings);
      Events.emit('holdings:add', { holding });
    },

    removeHolding(ticker) {
      const holdings = this.getHoldings().filter(h => h.ticker !== ticker);
      State.set('holdings', holdings);
      Events.emit('holdings:remove', { ticker });
    }
  };

  // ==========================================================================
  // PORTFOLIO CALCULATIONS
  // ==========================================================================

  const Portfolio = {
    getTotalValue() {
      const holdings = DemoData.getHoldings();
      return holdings.reduce((sum, h) => {
        const value = h.shares * h.currentPrice;
        return sum + value;
      }, 0);
    },

    getTotalPnL() {
      const holdings = DemoData.getHoldings();
      return holdings.reduce((sum, h) => {
        const cost = h.shares * h.avgCost;
        const value = h.shares * h.currentPrice;
        return sum + (value - cost);
      }, 0);
    },

    getTotalPnLPercent() {
      const holdings = DemoData.getHoldings();
      const totalCost = holdings.reduce((sum, h) => sum + (h.shares * h.avgCost), 0);
      const totalValue = this.getTotalValue();
      return ((totalValue - totalCost) / totalCost) * 100;
    },

    getSectorAllocation() {
      const holdings = DemoData.getHoldings();
      const total = this.getTotalValue();
      const sectors = {};

      holdings.forEach(h => {
        const value = h.shares * h.currentPrice;
        const weight = (value / total) * 100;
        if (!sectors[h.sector]) {
          sectors[h.sector] = 0;
        }
        sectors[h.sector] += weight;
      });

      return sectors;
    },

    getDiversificationScore() {
      const sectors = this.getSectorAllocation();
      const values = Object.values(sectors);
      const max = Math.max(...values);
      return Math.round(100 - (max - 25)); // Score based on max concentration
    }
  };

  // ==========================================================================
  // SIDEBAR MANAGEMENT
  // ==========================================================================

  let sidebarState = {
    isOpen: false,
    stockContext: null,
    chatHistory: [],
    isTyping: false
  };

  function initSidebar() {
    const sidebar = document.querySelector('.adviser-sidebar');
    if (!sidebar) return;

    // Set ARIA attributes
    sidebar.setAttribute('role', 'complementary');
    sidebar.setAttribute('aria-label', 'AI Adviser Panel');
    sidebar.setAttribute('aria-hidden', 'true');

    // Restore sidebar state
    const savedOpen = State.get('sidebar_open', false);
    const savedContext = State.get('sidebar_context', null);
    const savedHistory = State.get('chat_history', []);

    sidebarState.stockContext = savedContext;
    sidebarState.chatHistory = savedHistory;

    if (savedOpen) {
      openSidebar(false);
    }

    if (savedContext) {
      updateContextDisplay(savedContext);
    }

    restoreChatHistory();
    bindSidebarEvents();
    log('Sidebar initialized');
  }

  function openSidebar(animate = true) {
    const sidebar = document.querySelector('.adviser-sidebar');
    if (!sidebar) return;

    sidebarState.isOpen = true;
    sidebar.classList.add('open');
    document.body.classList.add('sidebar-open');
    State.set('sidebar_open', true);

    // Update ARIA
    sidebar.setAttribute('aria-hidden', 'false');

    // Update toggle buttons
    document.querySelectorAll('[data-action="toggle-sidebar"], #adviserToggle').forEach(btn => {
      btn.classList.add('active');
      btn.setAttribute('aria-expanded', 'true');
      btn.setAttribute('aria-pressed', 'true');
    });

    // Focus chat input
    if (animate) {
      const chatInput = sidebar.querySelector('.chat-input');
      setTimeout(() => chatInput?.focus(), CONFIG.ANIMATION_DURATION);
    }

    Events.emit('sidebar:open', {});
    announceToScreenReader('AI Adviser panel opened');
    log('Sidebar opened');
  }

  function closeSidebar() {
    const sidebar = document.querySelector('.adviser-sidebar');
    if (!sidebar) return;

    sidebarState.isOpen = false;
    sidebar.classList.remove('open');
    document.body.classList.remove('sidebar-open');
    State.set('sidebar_open', false);

    // Update ARIA
    sidebar.setAttribute('aria-hidden', 'true');

    // Update toggle buttons
    document.querySelectorAll('[data-action="toggle-sidebar"], #adviserToggle').forEach(btn => {
      btn.classList.remove('active');
      btn.setAttribute('aria-expanded', 'false');
      btn.setAttribute('aria-pressed', 'false');
    });

    Events.emit('sidebar:close', {});
    announceToScreenReader('AI Adviser panel closed');
    log('Sidebar closed');
  }

  function toggleSidebar() {
    if (sidebarState.isOpen) {
      closeSidebar();
    } else {
      openSidebar();
    }
  }

  function setStockContext(stock) {
    sidebarState.stockContext = stock;
    State.set('sidebar_context', stock);
    updateContextDisplay(stock);
    Events.emit('context:set', { stock });
    log('Stock context set:', stock?.ticker);
  }

  function clearStockContext() {
    sidebarState.stockContext = null;
    State.remove('sidebar_context');
    const contextEl = document.querySelector('.sidebar-context');
    if (contextEl) {
      contextEl.style.display = 'none';
    }
    Events.emit('context:clear', {});
  }

  function updateContextDisplay(stock) {
    const contextEl = document.querySelector('.sidebar-context');
    if (!contextEl || !stock) return;

    const stockEl = contextEl.querySelector('.context-stock');
    if (stockEl) {
      stockEl.innerHTML = `${stock.ticker} <span>${stock.name || stock.company || ''}</span>`;
    }
    contextEl.style.display = 'block';
  }

  function showTypingIndicator() {
    const chatMessages = document.querySelector('.chat-messages');
    if (!chatMessages) return;

    // Remove existing typing indicator
    hideTypingIndicator();

    const typing = document.createElement('div');
    typing.className = 'chat-message adviser typing-indicator';
    typing.setAttribute('role', 'status');
    typing.setAttribute('aria-label', 'Adviser is typing');
    typing.innerHTML = `
      <div class="chat-avatar" aria-hidden="true">AC</div>
      <div>
        <div class="chat-bubble">
          <span class="typing-dots">
            <span></span><span></span><span></span>
          </span>
        </div>
      </div>
    `;
    chatMessages.appendChild(typing);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    sidebarState.isTyping = true;
  }

  function hideTypingIndicator() {
    const typing = document.querySelector('.typing-indicator');
    if (typing) {
      typing.remove();
    }
    sidebarState.isTyping = false;
  }

  function askQuestion(question) {
    if (!question.trim()) return;
    if (!sidebarState.isOpen) {
      openSidebar();
    }
    setTimeout(() => sendMessage(question), 300);
  }

  function sendMessage(message) {
    if (!message.trim() || sidebarState.isTyping) return;

    const chatMessages = document.querySelector('.chat-messages');
    if (!chatMessages) return;

    // Add user message
    const userMsg = createChatMessage('user', message);
    chatMessages.appendChild(userMsg);
    announceToScreenReader(`You said: ${message}`);

    // Save to history
    sidebarState.chatHistory.push({ role: 'user', text: message, time: Date.now() });

    // Clear input
    const chatInput = document.querySelector('.chat-input');
    if (chatInput) {
      chatInput.value = '';
    }

    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;

    // Show typing indicator
    showTypingIndicator();

    // Simulate adviser response
    const delay = CONFIG.TYPING_DELAY.min + Math.random() * (CONFIG.TYPING_DELAY.max - CONFIG.TYPING_DELAY.min);
    setTimeout(() => {
      hideTypingIndicator();

      const response = generateDemoResponse(message, sidebarState.stockContext);
      const adviserMsg = createChatMessage('adviser', response);
      chatMessages.appendChild(adviserMsg);

      sidebarState.chatHistory.push({ role: 'adviser', text: response, time: Date.now() });
      saveChatHistory();

      chatMessages.scrollTop = chatMessages.scrollHeight;
      announceToScreenReader('Adviser responded');
      Events.emit('chat:response', { message: response });
    }, delay);

    saveChatHistory();
    Events.emit('chat:send', { message });
  }

  function createChatMessage(role, text) {
    const msg = document.createElement('div');
    msg.className = `chat-message ${role}`;
    msg.setAttribute('role', 'article');
    msg.setAttribute('aria-label', `${role === 'user' ? 'Your' : 'Adviser'} message`);

    const avatar = document.createElement('div');
    avatar.className = 'chat-avatar';
    avatar.textContent = role === 'user' ? 'Y' : 'AC';
    avatar.setAttribute('aria-hidden', 'true');

    const content = document.createElement('div');
    content.className = 'chat-content';

    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble';
    bubble.innerHTML = text;

    const time = document.createElement('div');
    time.className = 'chat-time';
    time.textContent = formatTime(new Date());

    content.appendChild(bubble);
    content.appendChild(time);

    msg.appendChild(avatar);
    msg.appendChild(content);

    return msg;
  }

  function generateDemoResponse(question, context) {
    const lowerQ = question.toLowerCase();

    if (context && context.ticker) {
      const holding = DemoData.getHolding(context.ticker);

      if (lowerQ.includes('buy') || lowerQ.includes('sell')) {
        return `Based on <strong>${context.ticker}</strong>'s current metrics and your portfolio allocation (${holding?.weight || 'N/A'}%), I recommend reviewing the position sizing. The stock shows ${Math.random() > 0.5 ? 'positive momentum' : 'some consolidation'} with a thesis score of ${holding?.thesis || 'N/A'}/10. Would you like me to run a full technical analysis?`;
      }
      if (lowerQ.includes('risk') || lowerQ.includes('exposure')) {
        return `Your exposure to <strong>${context.ticker}</strong> represents ${holding?.weight || 'approximately'}% of your portfolio. The current P&L is <strong>${formatPercent(holding?.pnl || 0)}</strong>. Sector concentration is ${Math.random() > 0.5 ? 'within acceptable limits' : 'slightly elevated'}. I can suggest rebalancing options if needed.`;
      }
      if (lowerQ.includes('thesis') || lowerQ.includes('score')) {
        return `<strong>${context.ticker}</strong> currently has a thesis score of <strong>${holding?.thesis || 'N/A'}/10</strong>. This factors in earnings quality, valuation, momentum, and macro sensitivity. ${holding?.thesis >= 7 ? 'The score indicates a constructive view.' : 'Consider reviewing your position size given the below-average score.'}`;
      }
      return `Analyzing <strong>${context.ticker}</strong>: The stock is trading at key technical levels with a thesis score of ${holding?.thesis || 'N/A'}/10. Recent volume suggests ${Math.random() > 0.5 ? 'accumulation' : 'distribution'} patterns. Shall I compare it with sector peers?`;
    }

    if (lowerQ.includes('portfolio')) {
      const totalValue = Portfolio.getTotalValue();
      const pnlPercent = Portfolio.getTotalPnLPercent();
      return `Your portfolio shows a <strong>${formatCurrency(totalValue)}</strong> total value with an overall P&L of <strong>${formatPercent(pnlPercent)}</strong>. The diversification score is ${Portfolio.getDiversificationScore()}/100. I recommend reviewing your Saudi equities exposure given recent policy developments.`;
    }

    if (lowerQ.includes('market') || lowerQ.includes('outlook')) {
      return `GCC markets are showing mixed signals. <strong>Saudi Tadawul</strong> leads with positive momentum from Vision 2030 initiatives. UAE markets consolidating after recent highs. Consider defensive positioning in Q3. Your portfolio beta to Brent is approximately 0.42.`;
    }

    if (lowerQ.includes('scenario') || lowerQ.includes('stress')) {
      return `Based on your current portfolio, I've identified 4 key scenarios:<br><br>• <strong>Base Case:</strong> +8.2% expected return<br>• <strong>Oil Bull:</strong> +12.4% if Brent reaches $95-100<br>• <strong>Rate Cut Rally:</strong> +10.1% with GCC rate cuts<br>• <strong>Risk-Off:</strong> -2.3% in flight-to-quality scenario<br><br>Would you like me to run a detailed scenario comparison?`;
    }

    return `I understand your question about "${question.substring(0, 50)}${question.length > 50 ? '...' : ''}". Let me analyze this in the context of your portfolio and current market conditions. Would you like me to focus on any specific aspect—risk analysis, sector allocation, or individual holdings?`;
  }

  function saveChatHistory() {
    const trimmed = sidebarState.chatHistory.slice(-CONFIG.MAX_CHAT_HISTORY);
    sidebarState.chatHistory = trimmed;
    State.set('chat_history', trimmed);
  }

  function restoreChatHistory() {
    const chatMessages = document.querySelector('.chat-messages');
    if (!chatMessages || !sidebarState.chatHistory.length) return;

    const existingMsgs = chatMessages.querySelectorAll('.chat-message:not(.welcome)');
    existingMsgs.forEach(m => m.remove());

    sidebarState.chatHistory.forEach(msg => {
      const el = createChatMessage(msg.role, msg.text);
      chatMessages.appendChild(el);
    });
  }

  function clearChatHistory() {
    sidebarState.chatHistory = [];
    State.remove('chat_history');

    const chatMessages = document.querySelector('.chat-messages');
    if (chatMessages) {
      const msgs = chatMessages.querySelectorAll('.chat-message:not(.welcome)');
      msgs.forEach(m => m.remove());
    }
    Events.emit('chat:clear', {});
  }

  function bindSidebarEvents() {
    // Toggle buttons
    document.querySelectorAll('[data-action="toggle-sidebar"], #adviserToggle').forEach(btn => {
      btn.addEventListener('click', toggleSidebar);
    });

    // Close buttons
    document.querySelectorAll('.sidebar-close, #sidebarClose').forEach(btn => {
      btn.addEventListener('click', closeSidebar);
    });

    // Clear context button
    document.querySelectorAll('.context-clear').forEach(btn => {
      btn.addEventListener('click', clearStockContext);
    });

    // Chat input
    const chatInput = document.querySelector('.chat-input');
    const sendBtn = document.querySelector('.chat-send');

    if (chatInput) {
      chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          sendMessage(chatInput.value);
        }
      });
    }

    if (sendBtn) {
      sendBtn.addEventListener('click', () => {
        const input = document.querySelector('.chat-input');
        if (input) sendMessage(input.value);
      });
    }

    // Suggested questions
    document.querySelectorAll('.suggested-question').forEach(btn => {
      btn.addEventListener('click', () => {
        askQuestion(btn.dataset.question || btn.textContent);
      });
    });
  }

  // ==========================================================================
  // TOAST NOTIFICATIONS
  // ==========================================================================

  let toastQueue = [];
  let toastActive = false;

  function showToast(title, message, type = 'info', duration = CONFIG.TOAST_DURATION) {
    toastQueue.push({ title, message, type, duration });
    processToastQueue();
  }

  function processToastQueue() {
    if (toastActive || toastQueue.length === 0) return;

    toastActive = true;
    const { title, message, type, duration } = toastQueue.shift();

    let toast = document.querySelector('.global-toast');

    if (!toast) {
      toast = createToastElement();
      document.body.appendChild(toast);
    }

    const iconEl = toast.querySelector('.toast-icon');
    const titleEl = toast.querySelector('.toast-title');
    const textEl = toast.querySelector('.toast-text');

    iconEl.className = `toast-icon ${type}`;
    iconEl.innerHTML = getToastIcon(type);
    titleEl.textContent = title;
    textEl.textContent = message;

    requestAnimationFrame(() => {
      toast.classList.add('show');
      announceToScreenReader(`${title}: ${message}`);
    });

    setTimeout(() => {
      hideToast();
    }, duration);

    Events.emit('toast:show', { title, message, type });
  }

  function hideToast() {
    const toast = document.querySelector('.global-toast');
    if (toast) {
      toast.classList.remove('show');
      setTimeout(() => {
        toastActive = false;
        processToastQueue();
      }, 300);
    }
  }

  function createToastElement() {
    const toast = document.createElement('div');
    toast.className = 'global-toast';
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    toast.innerHTML = `
      <div class="toast-icon info" aria-hidden="true"></div>
      <div class="toast-content">
        <div class="toast-title"></div>
        <div class="toast-text"></div>
      </div>
      <button class="toast-close" aria-label="Dismiss notification">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          <path d="M6 18L18 6M6 6l12 12"/>
        </svg>
      </button>
    `;

    toast.querySelector('.toast-close').addEventListener('click', hideToast);

    return toast;
  }

  function getToastIcon(type) {
    const icons = {
      success: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 6L9 17l-5-5"/></svg>',
      info: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>',
      warning: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><path d="M12 9v4M12 17h.01"/></svg>',
      error: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M15 9l-6 6M9 9l6 6"/></svg>'
    };
    return icons[type] || icons.info;
  }

  // ==========================================================================
  // LOADING STATES
  // ==========================================================================

  const Loading = {
    /**
     * Show loading state on an element
     * @param {Element|string} elementOrSelector
     * @param {Object} options
     */
    show(elementOrSelector, options = {}) {
      const el = typeof elementOrSelector === 'string'
        ? document.querySelector(elementOrSelector)
        : elementOrSelector;

      if (!el) return;

      const { text = 'Loading...', overlay = false, spinner = true } = options;

      el.classList.add('is-loading');
      el.setAttribute('aria-busy', 'true');

      if (overlay) {
        const loadingOverlay = document.createElement('div');
        loadingOverlay.className = 'loading-overlay';
        loadingOverlay.innerHTML = `
          ${spinner ? '<div class="spinner" aria-hidden="true"></div>' : ''}
          <span class="loading-text">${text}</span>
        `;
        el.style.position = 'relative';
        el.appendChild(loadingOverlay);
      }

      log('Loading started:', elementOrSelector);
    },

    /**
     * Hide loading state on an element
     * @param {Element|string} elementOrSelector
     */
    hide(elementOrSelector) {
      const el = typeof elementOrSelector === 'string'
        ? document.querySelector(elementOrSelector)
        : elementOrSelector;

      if (!el) return;

      el.classList.remove('is-loading');
      el.setAttribute('aria-busy', 'false');

      const overlay = el.querySelector('.loading-overlay');
      if (overlay) {
        overlay.remove();
      }

      log('Loading ended:', elementOrSelector);
    },

    /**
     * Show skeleton loading
     * @param {Element|string} elementOrSelector
     * @param {number} rows
     */
    skeleton(elementOrSelector, rows = 3) {
      const el = typeof elementOrSelector === 'string'
        ? document.querySelector(elementOrSelector)
        : elementOrSelector;

      if (!el) return;

      el.setAttribute('aria-busy', 'true');

      let skeletonHTML = '';
      for (let i = 0; i < rows; i++) {
        const width = 60 + Math.random() * 40;
        skeletonHTML += `<div class="skeleton" style="width: ${width}%; height: 16px; margin-bottom: 12px;"></div>`;
      }

      el.dataset.originalContent = el.innerHTML;
      el.innerHTML = skeletonHTML;
    },

    /**
     * Remove skeleton and restore content
     * @param {Element|string} elementOrSelector
     */
    removeSkeleton(elementOrSelector) {
      const el = typeof elementOrSelector === 'string'
        ? document.querySelector(elementOrSelector)
        : elementOrSelector;

      if (!el) return;

      el.setAttribute('aria-busy', 'false');

      if (el.dataset.originalContent) {
        el.innerHTML = el.dataset.originalContent;
        delete el.dataset.originalContent;
      }
    }
  };

  // ==========================================================================
  // FORMATTING UTILITIES
  // ==========================================================================

  function formatCurrency(value, currency = 'SAR', locale = 'en-SA') {
    if (typeof value !== 'number' || isNaN(value)) return '—';
    return new Intl.NumberFormat(locale, {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  }

  function formatNumber(value, decimals = 0) {
    if (typeof value !== 'number' || isNaN(value)) return '—';
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    }).format(value);
  }

  function formatPercent(value, includeSign = true) {
    if (typeof value !== 'number' || isNaN(value)) return '—';
    const sign = includeSign && value > 0 ? '+' : '';
    return `${sign}${value.toFixed(2)}%`;
  }

  function formatDate(date, options = {}) {
    const d = date instanceof Date ? date : new Date(date);
    if (isNaN(d.getTime())) return '—';

    const defaults = {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    };

    return new Intl.DateTimeFormat('en-US', { ...defaults, ...options }).format(d);
  }

  function formatTime(date) {
    const d = date instanceof Date ? date : new Date(date);
    if (isNaN(d.getTime())) return '—';
    return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true });
  }

  function formatCompact(value) {
    if (typeof value !== 'number' || isNaN(value)) return '—';
    if (value >= 1e9) return (value / 1e9).toFixed(1) + 'B';
    if (value >= 1e6) return (value / 1e6).toFixed(1) + 'M';
    if (value >= 1e3) return (value / 1e3).toFixed(1) + 'K';
    return value.toString();
  }

  function formatRelativeTime(date) {
    const d = date instanceof Date ? date : new Date(date);
    if (isNaN(d.getTime())) return '—';

    const now = new Date();
    const diff = now - d;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;
    return formatDate(d);
  }

  // ==========================================================================
  // DOM UTILITIES
  // ==========================================================================

  function $(selector, parent = document) {
    return parent.querySelector(selector);
  }

  function $$(selector, parent = document) {
    return parent.querySelectorAll(selector);
  }

  function createElement(tag, attrs = {}, children = null) {
    const el = document.createElement(tag);

    Object.entries(attrs).forEach(([key, value]) => {
      if (key === 'className') {
        el.className = value;
      } else if (key === 'style' && typeof value === 'object') {
        Object.assign(el.style, value);
      } else if (key.startsWith('on') && typeof value === 'function') {
        el.addEventListener(key.slice(2).toLowerCase(), value);
      } else if (key.startsWith('data')) {
        el.dataset[key.slice(4).toLowerCase()] = value;
      } else {
        el.setAttribute(key, value);
      }
    });

    if (children) {
      if (Array.isArray(children)) {
        children.forEach(child => {
          if (typeof child === 'string') {
            el.appendChild(document.createTextNode(child));
          } else if (child instanceof Element) {
            el.appendChild(child);
          }
        });
      } else if (typeof children === 'string') {
        el.innerHTML = children;
      } else if (children instanceof Element) {
        el.appendChild(children);
      }
    }

    return el;
  }

  function debounce(fn, delay = CONFIG.DEBOUNCE_DELAY) {
    let timeout;
    return function(...args) {
      clearTimeout(timeout);
      timeout = setTimeout(() => fn.apply(this, args), delay);
    };
  }

  function throttle(fn, limit) {
    let inThrottle;
    return function(...args) {
      if (!inThrottle) {
        fn.apply(this, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  }

  // ==========================================================================
  // ACCESSIBILITY
  // ==========================================================================

  let liveRegion;

  function initAccessibility() {
    // Create live region for announcements
    if (!document.querySelector('.live-region')) {
      liveRegion = document.createElement('div');
      liveRegion.setAttribute('role', 'status');
      liveRegion.setAttribute('aria-live', 'polite');
      liveRegion.setAttribute('aria-atomic', 'true');
      liveRegion.className = 'sr-only live-region';
      document.body.appendChild(liveRegion);
    } else {
      liveRegion = document.querySelector('.live-region');
    }

    // Skip link
    if (!$('.skip-link') && !$('.ac-skip-link')) {
      const skipLink = createElement('a', {
        className: 'skip-link',
        href: '#main-content'
      }, 'Skip to main content');
      document.body.insertBefore(skipLink, document.body.firstChild);
    }

    // Ensure main content has ID
    const main = $('main, .app-main, #mainContent');
    if (main && !main.id) {
      main.id = 'main-content';
    }

    // Global keyboard handlers
    document.addEventListener('keydown', handleGlobalKeyboard);

    log('Accessibility initialized');
  }

  function announceToScreenReader(message, priority = 'polite') {
    if (!liveRegion) {
      liveRegion = document.querySelector('.live-region');
    }
    if (!liveRegion) return;

    liveRegion.setAttribute('aria-live', priority);
    liveRegion.textContent = '';
    setTimeout(() => {
      liveRegion.textContent = message;
    }, 100);
  }

  function handleGlobalKeyboard(e) {
    // Escape: close modals and sidebar
    if (e.key === 'Escape') {
      const openModal = $('.modal-overlay.open');
      if (openModal) {
        closeModal(openModal);
        return;
      }
      if (sidebarState.isOpen) {
        closeSidebar();
        const toggle = document.querySelector('#adviserToggle, [data-action="toggle-sidebar"]');
        toggle?.focus();
      }
    }

    // Focus trap in modals
    const modal = $('.modal-overlay.open .modal');
    if (modal && e.key === 'Tab') {
      const focusable = modal.querySelectorAll(
        'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
      );
      if (focusable.length === 0) return;

      const first = focusable[0];
      const last = focusable[focusable.length - 1];

      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }
  }

  // ==========================================================================
  // NAVIGATION
  // ==========================================================================

  function initNavigation(pageName) {
    const navLinks = $$('.app-nav-links a');
    navLinks.forEach(link => {
      link.classList.remove('active');
      link.removeAttribute('aria-current');
      if (link.getAttribute('href')?.includes(pageName)) {
        link.classList.add('active');
        link.setAttribute('aria-current', 'page');
      }
    });
    log('Navigation initialized for:', pageName);
  }

  function initIndicesBar() {
    const indicesTime = $('.indices-time');
    if (indicesTime) {
      updateIndicesTime();
      setInterval(updateIndicesTime, 60000);
    }
  }

  function updateIndicesTime() {
    const el = $('.indices-time');
    if (!el) return;

    const now = new Date();
    const time = now.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      timeZone: 'Asia/Riyadh'
    });
    el.innerHTML = `<span class="live-indicator" aria-hidden="true"></span> Live · ${time} AST`;
  }

  // ==========================================================================
  // MODALS
  // ==========================================================================

  let previousActiveElement = null;

  function openModal(modalOrSelector) {
    const overlay = typeof modalOrSelector === 'string'
      ? $(modalOrSelector)
      : modalOrSelector;

    if (!overlay) return;

    // Store current focus
    previousActiveElement = document.activeElement;

    overlay.classList.add('open');
    overlay.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';

    // Set up ARIA
    const modal = overlay.querySelector('.modal');
    if (modal) {
      modal.setAttribute('role', 'dialog');
      modal.setAttribute('aria-modal', 'true');

      // Focus first focusable element or close button
      const focusTarget = modal.querySelector('.modal-close, button, [href], input, select, textarea');
      setTimeout(() => focusTarget?.focus(), 50);
    }

    Events.emit('modal:open', { modal: modalOrSelector });
    announceToScreenReader('Dialog opened');
    log('Modal opened:', modalOrSelector);
  }

  function closeModal(modalOrSelector) {
    const overlay = typeof modalOrSelector === 'string'
      ? $(modalOrSelector)
      : modalOrSelector;

    if (!overlay) return;

    overlay.classList.remove('open');
    overlay.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';

    // Restore focus
    if (previousActiveElement && previousActiveElement.focus) {
      previousActiveElement.focus();
      previousActiveElement = null;
    }

    Events.emit('modal:close', { modal: modalOrSelector });
    announceToScreenReader('Dialog closed');
    log('Modal closed:', modalOrSelector);
  }

  function closeAllModals() {
    $$('.modal-overlay.open').forEach(modal => {
      closeModal(modal);
    });
  }

  function initModals() {
    // Close buttons
    $$('.modal-close').forEach(btn => {
      btn.addEventListener('click', () => {
        const overlay = btn.closest('.modal-overlay');
        if (overlay) closeModal(overlay);
      });
    });

    // Overlay click to close
    $$('.modal-overlay').forEach(overlay => {
      overlay.addEventListener('click', (e) => {
        if (e.target === overlay) closeModal(overlay);
      });
    });

    // Set ARIA attributes
    $$('.modal-overlay').forEach(overlay => {
      overlay.setAttribute('aria-hidden', 'true');
      const modal = overlay.querySelector('.modal');
      if (modal) {
        modal.setAttribute('role', 'dialog');
        modal.setAttribute('aria-modal', 'true');
      }
    });

    log('Modals initialized');
  }

  // ==========================================================================
  // EXPANDABLE SECTIONS
  // ==========================================================================

  const Expandable = {
    init() {
      $$('[data-expand-trigger]').forEach(trigger => {
        const targetId = trigger.dataset.expandTrigger;
        const target = document.getElementById(targetId);

        if (!target) return;

        // Set initial ARIA
        trigger.setAttribute('aria-expanded', 'false');
        trigger.setAttribute('aria-controls', targetId);
        target.setAttribute('aria-hidden', 'true');
        target.classList.add('expandable-content');

        trigger.addEventListener('click', () => {
          this.toggle(trigger, target);
        });

        // Keyboard support
        trigger.addEventListener('keydown', (e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            this.toggle(trigger, target);
          }
        });
      });
      log('Expandables initialized');
    },

    toggle(trigger, target) {
      const isExpanded = trigger.getAttribute('aria-expanded') === 'true';

      trigger.setAttribute('aria-expanded', !isExpanded);
      target.setAttribute('aria-hidden', isExpanded);
      target.classList.toggle('is-expanded', !isExpanded);
      trigger.classList.toggle('is-expanded', !isExpanded);

      Events.emit('expandable:toggle', { trigger, target, isExpanded: !isExpanded });
    },

    open(triggerId) {
      const trigger = document.querySelector(`[data-expand-trigger="${triggerId}"]`);
      const target = document.getElementById(triggerId);
      if (trigger && target) {
        trigger.setAttribute('aria-expanded', 'true');
        target.setAttribute('aria-hidden', 'false');
        target.classList.add('is-expanded');
        trigger.classList.add('is-expanded');
      }
    },

    close(triggerId) {
      const trigger = document.querySelector(`[data-expand-trigger="${triggerId}"]`);
      const target = document.getElementById(triggerId);
      if (trigger && target) {
        trigger.setAttribute('aria-expanded', 'false');
        target.setAttribute('aria-hidden', 'true');
        target.classList.remove('is-expanded');
        trigger.classList.remove('is-expanded');
      }
    }
  };

  // ==========================================================================
  // FORM UTILITIES
  // ==========================================================================

  function serializeForm(form) {
    const data = {};
    const formData = new FormData(form);
    formData.forEach((value, key) => {
      if (data.hasOwnProperty(key)) {
        if (!Array.isArray(data[key])) {
          data[key] = [data[key]];
        }
        data[key].push(value);
      } else {
        data[key] = value;
      }
    });
    return data;
  }

  function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  }

  function getPasswordStrength(password) {
    let score = 0;
    if (!password) return { score: 0, label: '', color: '' };

    if (password.length >= 8) score++;
    if (password.length >= 12) score++;
    if (/[A-Z]/.test(password) && /[a-z]/.test(password)) score++;
    if (/[0-9]/.test(password)) score++;
    if (/[^A-Za-z0-9]/.test(password)) score++;

    const labels = ['Very Weak', 'Weak', 'Fair', 'Good', 'Strong'];
    const colors = ['#EF4444', '#F59E0B', '#EAB308', '#22C55E', '#10B981'];

    const index = Math.min(score, 4);
    return {
      score: index,
      label: labels[index],
      color: colors[index]
    };
  }

  function showFieldError(field, message) {
    const wrapper = field.closest('.form-group') || field.parentElement;
    if (!wrapper) return;

    // Remove existing error
    hideFieldError(field);

    field.setAttribute('aria-invalid', 'true');
    field.classList.add('has-error');

    const errorId = `${field.id || field.name}-error`;
    const errorEl = document.createElement('div');
    errorEl.id = errorId;
    errorEl.className = 'field-error';
    errorEl.setAttribute('role', 'alert');
    errorEl.textContent = message;

    field.setAttribute('aria-describedby', errorId);
    wrapper.appendChild(errorEl);

    announceToScreenReader(message, 'assertive');
  }

  function hideFieldError(field) {
    const wrapper = field.closest('.form-group') || field.parentElement;
    if (!wrapper) return;

    field.removeAttribute('aria-invalid');
    field.classList.remove('has-error');

    const errorEl = wrapper.querySelector('.field-error');
    if (errorEl) {
      field.removeAttribute('aria-describedby');
      errorEl.remove();
    }
  }

  // ==========================================================================
  // PAGE-SPECIFIC HOOKS
  // ==========================================================================

  const PageHooks = {
    _hooks: {},

    register(pageName, callback) {
      if (!this._hooks[pageName]) {
        this._hooks[pageName] = [];
      }
      this._hooks[pageName].push(callback);
    },

    run(pageName) {
      const hooks = this._hooks[pageName] || [];
      hooks.forEach(hook => {
        try {
          hook();
        } catch (e) {
          console.error(`[AlphaCouncil] Page hook error for ${pageName}:`, e);
        }
      });
      log('Page hooks executed for:', pageName);
    }
  };

  // Pre-defined page hooks
  PageHooks.register('dashboard', () => {
    DemoData.seed();
    Events.emit('page:dashboard:ready', {});
  });

  PageHooks.register('portfolio', () => {
    DemoData.seed();
    Events.emit('page:portfolio:ready', {});
  });

  PageHooks.register('scenarios', () => {
    DemoData.seed();
    Events.emit('page:scenarios:ready', {});
  });

  PageHooks.register('stock-detail', () => {
    Events.emit('page:stock-detail:ready', {});
  });

  PageHooks.register('settings', () => {
    Events.emit('page:settings:ready', {});
  });

  PageHooks.register('news', () => {
    Events.emit('page:news:ready', {});
  });

  PageHooks.register('alerts', () => {
    DemoData.seed();
    Events.emit('page:alerts:ready', {});
  });

  PageHooks.register('council-history', () => {
    Events.emit('page:council-history:ready', {});
  });

  // ==========================================================================
  // INITIALIZATION
  // ==========================================================================

  let currentPage = '';

  function init(pageName = '', options = {}) {
    // Prevent double init
    if (global.AlphaCouncil._initialized && currentPage === pageName) return;

    currentPage = pageName;

    const runInit = () => {
      initAccessibility();
      initNavigation(pageName);
      initIndicesBar();
      initSidebar();
      initModals();
      Expandable.init();

      // Run page-specific hooks
      PageHooks.run(pageName);

      // Seed demo data on logged-in pages
      if (['dashboard', 'portfolio', 'scenarios', 'alerts'].includes(pageName)) {
        DemoData.seed();
      }

      log(`Initialized v${CONFIG.VERSION} for page: ${pageName}`);
      global.AlphaCouncil._initialized = true;
      Events.emit('init:complete', { page: pageName });
    };

    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', runInit);
    } else {
      runInit();
    }
  }

  // ==========================================================================
  // PUBLIC API
  // ==========================================================================

  const AlphaCouncil = {
    // Meta
    _initialized: false,
    VERSION: CONFIG.VERSION,
    DEBUG: CONFIG.DEBUG,

    // Initialization
    init,

    // Events
    Events,
    on: Events.on.bind(Events),
    off: Events.off.bind(Events),
    emit: Events.emit.bind(Events),

    // State
    State,

    // Demo Data
    DemoData,
    resetDemoData: DemoData.reset.bind(DemoData),

    // Portfolio
    Portfolio,

    // Sidebar
    openSidebar,
    closeSidebar,
    toggleSidebar,
    setStockContext,
    clearStockContext,
    askQuestion,
    sendMessage,
    clearChatHistory,

    // Toast
    showToast,
    hideToast,

    // Loading
    Loading,
    showLoading: Loading.show.bind(Loading),
    hideLoading: Loading.hide.bind(Loading),
    showSkeleton: Loading.skeleton.bind(Loading),
    hideSkeleton: Loading.removeSkeleton.bind(Loading),

    // Modals
    openModal,
    closeModal,
    closeAllModals,

    // Expandables
    Expandable,

    // Formatting
    formatCurrency,
    formatNumber,
    formatPercent,
    formatDate,
    formatTime,
    formatCompact,
    formatRelativeTime,

    // DOM Utilities
    $,
    $$,
    createElement,
    debounce,
    throttle,

    // Forms
    serializeForm,
    isValidEmail,
    getPasswordStrength,
    showFieldError,
    hideFieldError,

    // Accessibility
    announceToScreenReader,

    // Page Hooks
    PageHooks,
    onPageInit: PageHooks.register.bind(PageHooks),

    // Debug
    log
  };

  // Export to global
  global.AlphaCouncil = AlphaCouncil;

  // Auto-init if data attribute present
  if (document.currentScript?.dataset.autoInit !== 'false') {
    const pageName = document.currentScript?.dataset.page || '';
    init(pageName);
  }

})(typeof window !== 'undefined' ? window : this);

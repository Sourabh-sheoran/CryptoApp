/**
 * CryptoPulse AI — Full-Stack Cryptocurrency Trading & ML Prediction Platform
 * Modern Client-side Controller & Charting Engine
 */

// Application State
const state = {
  currentTab: 'markets',
  currency: 'usd',
  currencySymbols: { usd: '$', inr: '₹', eur: '€', gbp: '£' },
  coins: [],
  filteredCoins: [],
  user: null,
  token: localStorage.getItem('crypto_token') || null,
  watchlist: JSON.parse(localStorage.getItem('crypto_watchlist') || '[]'),
  activeChartCoin: 'bitcoin',
  activeChartDays: '30',
  currentTradeCoin: null,
  tradeType: 'BUY',
  charts: {
    market: null,
    prediction: null
  }
};

// Toast Notifications
function showToast(message, type = 'success') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<span>${type === 'success' ? '✅' : '⚠️'}</span> <span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(20px)';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// Currency Formatter
function formatCurrency(val, currency = state.currency) {
  if (val === null || val === undefined || isNaN(val)) return '$0.00';
  const sym = state.currencySymbols[currency.toLowerCase()] || '$';
  if (Math.abs(val) >= 1e12) return `${sym}${(val / 1e12).toFixed(2)}T`;
  if (Math.abs(val) >= 1e9) return `${sym}${(val / 1e9).toFixed(2)}B`;
  if (Math.abs(val) >= 1e6) return `${sym}${(val / 1e6).toFixed(2)}M`;
  if (Math.abs(val) < 0.001) return `${sym}${val.toFixed(6)}`;
  if (Math.abs(val) < 1) return `${sym}${val.toFixed(4)}`;
  return `${sym}${Number(val).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

// Navigation Tabs
function switchTab(tabId) {
  state.currentTab = tabId;
  document.querySelectorAll('.nav-tab').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === tabId);
  });
  document.querySelectorAll('.tab-content').forEach(el => {
    el.classList.toggle('active', el.id === `tab-${tabId}`);
  });

  if (tabId === 'predictions' && !state.predictionLoaded) {
    runAIPrediction();
  } else if (tabId === 'charts') {
    loadTechnicalChart();
  } else if (tabId === 'portfolio') {
    loadPortfolioData();
  } else if (tabId === 'watchlist') {
    renderWatchlist();
  }
}

// Global Stats & Sentiment
async function fetchGlobalStats() {
  try {
    const res = await fetch('/api/market/global');
    if (res.ok) {
      const data = await res.json();
      document.getElementById('global-cryptos').textContent = data.active_cryptocurrencies?.toLocaleString() || '14,280';
      const mcapVal = data.total_market_cap?.[state.currency] || data.total_market_cap?.usd || 3.25e12;
      document.getElementById('global-mcap').textContent = formatCurrency(mcapVal);
      const volVal = data.total_volume?.[state.currency] || data.total_volume?.usd || 1.28e11;
      document.getElementById('global-vol').textContent = formatCurrency(volVal);
      document.getElementById('global-btc-dom').textContent = `${data.market_cap_percentage?.btc?.toFixed(1) || '58.4'}%`;
    }

    const fngRes = await fetch('/api/market/fear-and-greed');
    if (fngRes.ok) {
      const fng = await fngRes.json();
      const val = fng.value || '72';
      const classification = fng.value_classification || 'Greed';
      const el = document.getElementById('global-sentiment');
      el.textContent = `${val} (${classification})`;
      document.getElementById('stat-fng-index').textContent = `${val} / 100 (${classification})`;
    }
  } catch (err) {
    console.error('Error fetching global stats:', err);
  }
}

// Markets Fetch & Render
async function fetchMarketData() {
  try {
    const res = await fetch(`/api/market/coins?currency=${state.currency}&limit=100`);
    if (res.ok) {
      state.coins = await res.json();
      state.filteredCoins = [...state.coins];
      renderMarketTable();
      updateTopBanners();
    }
  } catch (err) {
    console.error('Error fetching market coins:', err);
    showToast('Failed to refresh market prices', 'error');
  }
}

function updateTopBanners() {
  const btc = state.coins.find(c => c.id === 'bitcoin' || c.symbol === 'btc');
  if (btc) document.getElementById('stat-btc-price').textContent = formatCurrency(btc.current_price);

  const eth = state.coins.find(c => c.id === 'ethereum' || c.symbol === 'eth');
  if (eth) document.getElementById('stat-eth-price').textContent = formatCurrency(eth.current_price);

  // Top gainer
  const sortedGainers = [...state.coins].sort((a, b) => (b.price_change_percentage_24h || 0) - (a.price_change_percentage_24h || 0));
  if (sortedGainers.length > 0 && sortedGainers[0]) {
    const g = sortedGainers[0];
    const change = (g.price_change_percentage_24h || 0).toFixed(2);
    document.getElementById('stat-top-gainer').textContent = `${g.symbol.toUpperCase()} (+${change}%)`;
  }
}

function renderMarketTable() {
  const tbody = document.getElementById('market-table-body');
  tbody.innerHTML = '';

  if (state.filteredCoins.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--text-dim); padding: 30px;">No cryptocurrencies match your search.</td></tr>`;
    return;
  }

  state.filteredCoins.forEach((c, idx) => {
    const change24h = c.price_change_percentage_24h || 0;
    const isPositive = change24h >= 0;
    const isStarred = state.watchlist.includes(c.id);

    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td style="color: var(--text-dim); font-size: 12px; font-weight: 600;">${c.market_cap_rank || (idx + 1)}</td>
      <td>
        <div class="coin-cell">
          <button class="btn btn-ghost btn-sm" style="padding: 2px 6px; border: none; font-size: 14px;" onclick="toggleWatchlist('${c.id}', '${c.symbol}', '${c.name.replace(/'/g, "\\'")}')">
            ${isStarred ? '⭐' : '☆'}
          </button>
          <img src="${c.image || 'https://assets.coingecko.com/coins/images/1/large/bitcoin.png'}" class="coin-img" alt="${c.name}">
          <div class="coin-name-block">
            <span class="coin-symbol">${c.symbol.toUpperCase()}</span>
            <span class="coin-full-name">${c.name}</span>
          </div>
        </div>
      </td>
      <td class="mono" style="font-weight: 700; font-size: 14px;">${formatCurrency(c.current_price)}</td>
      <td>
        <span class="${isPositive ? 'badge-positive' : 'badge-negative'}">
          ${isPositive ? '▲ +' : '▼ '}${change24h.toFixed(2)}%
        </span>
      </td>
      <td class="mono" style="font-size: 12.5px; color: var(--text-dim);">
        ${formatCurrency(c.high_24h)} / ${formatCurrency(c.low_24h)}
      </td>
      <td class="mono" style="font-size: 12.5px;">${formatCurrency(c.total_volume)}</td>
      <td class="mono" style="font-size: 12.5px; font-weight: 600;">${formatCurrency(c.market_cap)}</td>
      <td style="text-align: right;">
        <div style="display: inline-flex; gap: 6px;">
          <button class="btn btn-emerald btn-sm" onclick="openTradeModal('${c.id}', '${c.symbol}', '${c.name.replace(/'/g, "\\'")}', ${c.current_price}, 'BUY')">Buy</button>
          <button class="btn btn-primary btn-sm" style="background: rgba(99, 102, 241, 0.2); border: 1px solid rgba(99, 102, 241, 0.4);" onclick="quickPredict('${c.symbol.toUpperCase()}-USD')">Predict 🧠</button>
        </div>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function filterMarketTable() {
  const query = document.getElementById('market-search-input').value.toLowerCase().trim();
  if (!query) {
    state.filteredCoins = [...state.coins];
  } else {
    state.filteredCoins = state.coins.filter(c =>
      c.name.toLowerCase().includes(query) || c.symbol.toLowerCase().includes(query)
    );
  }
  renderMarketTable();
}

function filterCategory(cat) {
  if (cat === 'all') {
    state.filteredCoins = [...state.coins];
  } else if (cat === 'gainers') {
    state.filteredCoins = [...state.coins].filter(c => (c.price_change_percentage_24h || 0) > 0).sort((a, b) => (b.price_change_percentage_24h || 0) - (a.price_change_percentage_24h || 0));
  } else if (cat === 'losers') {
    state.filteredCoins = [...state.coins].filter(c => (c.price_change_percentage_24h || 0) < 0).sort((a, b) => (a.price_change_percentage_24h || 0) - (b.price_change_percentage_24h || 0));
  }
  renderMarketTable();
}

function onCurrencyChange() {
  state.currency = document.getElementById('currency-picker').value;
  fetchMarketData();
  fetchGlobalStats();
  if (state.currentTab === 'charts') loadTechnicalChart();
}

// AI Price Prediction
function setPredictTicker(ticker) {
  document.getElementById('predict-symbol-input').value = ticker;
  runAIPrediction();
}

function quickPredict(ticker) {
  switchTab('predictions');
  document.getElementById('predict-symbol-input').value = ticker;
  runAIPrediction();
}

async function runAIPrediction() {
  const symbol = document.getElementById('predict-symbol-input').value.trim() || 'BTC-USD';
  const days = document.getElementById('predict-days-select').value || '7';
  const btn = document.getElementById('run-predict-btn');

  btn.disabled = true;
  btn.innerHTML = `<span class="spinner"></span> Training ML Model...`;

  try {
    const res = await fetch(`/api/predict/?symbol=${encodeURIComponent(symbol)}&days=${days}`);
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Prediction failed');
    }
    const data = await res.json();
    state.predictionLoaded = true;
    renderPredictionResults(data);
    showToast(`AI forecast completed for ${data.symbol}!`, 'success');
  } catch (err) {
    console.error('Prediction error:', err);
    showToast(err.message, 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<span>⚡</span> Train & Predict Prices`;
  }
}

function renderPredictionResults(data) {
  const currentPrice = data.current_price;
  const predClose = data.predicted_next_day.close;
  const expChange = data.predicted_next_day.expected_change_pct;
  const isPos = expChange >= 0;

  document.getElementById('pred-current-price').textContent = `$${Number(currentPrice).toLocaleString()}`;
  document.getElementById('pred-next-close').textContent = `$${Number(predClose).toLocaleString()}`;
  document.getElementById('pred-next-close').style.color = isPos ? 'var(--emerald)' : 'var(--rose)';

  const pctEl = document.getElementById('pred-pct-change');
  pctEl.textContent = `${isPos ? '+' : ''}${expChange}%`;
  pctEl.style.color = isPos ? 'var(--emerald)' : 'var(--rose)';

  document.getElementById('pred-confidence').textContent = `${data.model_metrics.average_confidence_pct || 96.4}%`;
  document.getElementById('pred-high-low').textContent = `$${data.predicted_next_day.high.toLocaleString()} / $${data.predicted_next_day.low.toLocaleString()}`;

  // AI Signal Badge
  const signal = data.ai_analysis.signal;
  const badgeClass = `signal-${signal.replace(/[^a-zA-Z0-9]/g, '_')}`;
  const badgeContainer = document.getElementById('ai-signal-badge-container');
  badgeContainer.innerHTML = `<span class="ai-signal-badge ${badgeClass}">${signal}</span>`;

  // Reasons list
  const reasonsList = document.getElementById('ai-reasons-list');
  reasonsList.innerHTML = '';
  data.ai_analysis.reasons.forEach(r => {
    const div = document.createElement('div');
    div.className = 'ai-reason-item';
    div.innerHTML = `<span>🔹</span> <span>${r}</span>`;
    reasonsList.appendChild(div);
  });

  // Technical Levels & Stats
  const techList = document.getElementById('technical-stats-list');
  techList.innerHTML = `
    <div class="ai-reason-item"><span>🎯</span> <span><strong>RSI (14):</strong> ${data.technical_indicators.rsi}</span></div>
    <div class="ai-reason-item"><span>📊</span> <span><strong>MACD Momentum:</strong> ${data.technical_indicators.macd}</span></div>
    <div class="ai-reason-item"><span>🛡️</span> <span><strong>Support Level:</strong> $${data.technical_indicators.support_level_1.toLocaleString()}</span></div>
    <div class="ai-reason-item"><span>🚧</span> <span><strong>Resistance Level:</strong> $${data.technical_indicators.resistance_level_1.toLocaleString()}</span></div>
    <div class="ai-reason-item"><span>📏</span> <span><strong>RMSE Accuracy:</strong> ±$${data.model_metrics.RMSE_Close || 0}</span></div>
  `;

  // Render Trajectory Forecast Chart
  renderPredictionChart(data);
}

function renderPredictionChart(data) {
  const ctx = document.getElementById('predictionChart').getContext('2d');
  if (state.charts.prediction) {
    state.charts.prediction.destroy();
  }

  const labels = ['Now', ...data.forecast_trajectory.map(p => `Day +${p.day}`)];
  const projectedPrices = [data.current_price, ...data.forecast_trajectory.map(p => p.projected_price)];
  const upperBounds = [data.current_price, ...data.forecast_trajectory.map(p => p.upper_bound)];
  const lowerBounds = [data.current_price, ...data.forecast_trajectory.map(p => p.lower_bound)];

  state.charts.prediction = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Upper Confidence Bound',
          data: upperBounds,
          borderColor: 'rgba(6, 182, 212, 0.3)',
          borderDash: [5, 5],
          pointRadius: 0,
          fill: '+1',
          backgroundColor: 'rgba(99, 102, 241, 0.08)'
        },
        {
          label: 'XGBoost AI Price Forecast',
          data: projectedPrices,
          borderColor: '#6366f1',
          backgroundColor: 'rgba(99, 102, 241, 0.2)',
          borderWidth: 3,
          pointBackgroundColor: '#818cf8',
          pointRadius: 4,
          fill: false,
          tension: 0.3
        },
        {
          label: 'Lower Confidence Bound',
          data: lowerBounds,
          borderColor: 'rgba(6, 182, 212, 0.3)',
          borderDash: [5, 5],
          pointRadius: 0,
          fill: false
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          display: true,
          labels: { color: '#94a3b8', font: { family: 'Plus Jakarta Sans', size: 11 } }
        },
        tooltip: {
          backgroundColor: '#182236',
          titleFont: { family: 'Plus Jakarta Sans', weight: 'bold' },
          bodyFont: { family: 'JetBrains Mono' },
          callbacks: {
            label: (context) => `${context.dataset.label}: $${Number(context.raw).toLocaleString()}`
          }
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255,255,255,0.04)' },
          ticks: { color: '#64748b', font: { family: 'JetBrains Mono', size: 11 } }
        },
        y: {
          grid: { color: 'rgba(255,255,255,0.04)' },
          ticks: {
            color: '#64748b',
            font: { family: 'JetBrains Mono', size: 11 },
            callback: (v) => '$' + v.toLocaleString()
          }
        }
      }
    }
  });
}

// Technical Chart Tab
function setChartDays(days) {
  state.activeChartDays = days;
  document.querySelectorAll('#tab-charts .btn-ghost').forEach(b => {
    b.classList.toggle('active', b.textContent.includes(days === '1' ? '24H' : `${days}D`) || (days === '365' && b.textContent === '1Y'));
  });
  loadTechnicalChart();
}

async function loadTechnicalChart() {
  const coinId = document.getElementById('chart-coin-select').value;
  state.activeChartCoin = coinId;
  const days = state.activeChartDays;

  try {
    const res = await fetch(`/api/market/coins/${coinId}/historical?days=${days}&currency=${state.currency}`);
    if (!res.ok) throw new Error('Failed to load chart');
    const data = await res.json();
    renderMarketChart(data.prices || []);
  } catch (err) {
    console.error('Chart load error:', err);
  }
}

function renderMarketChart(prices) {
  const ctx = document.getElementById('marketChart').getContext('2d');
  if (state.charts.market) {
    state.charts.market.destroy();
  }

  if (!prices || prices.length === 0) return;

  const latestPrice = prices[prices.length - 1][1];
  const firstPrice = prices[0][1];
  const isUp = latestPrice >= firstPrice;
  const color = isUp ? '#10b981' : '#f43f5e';
  const bgColor = isUp ? 'rgba(16, 185, 129, 0.12)' : 'rgba(244, 63, 94, 0.12)';

  document.getElementById('chart-price-banner').textContent = formatCurrency(latestPrice);
  document.getElementById('chart-price-banner').style.color = color;

  const labels = prices.map(p => {
    const d = new Date(p[0]);
    return state.activeChartDays === '1' ? d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : d.toLocaleDateString([], { month: 'short', day: 'numeric' });
  });
  const dataPoints = prices.map(p => p[1]);

  state.charts.market = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Price',
        data: dataPoints,
        borderColor: color,
        backgroundColor: bgColor,
        borderWidth: 2.5,
        fill: true,
        pointRadius: 0,
        tension: 0.2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#182236',
          bodyFont: { family: 'JetBrains Mono' },
          callbacks: {
            label: (c) => `Price: ${formatCurrency(c.raw)}`
          }
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255,255,255,0.03)' },
          ticks: { color: '#64748b', maxTicksLimit: 8, font: { family: 'JetBrains Mono', size: 11 } }
        },
        y: {
          grid: { color: 'rgba(255,255,255,0.03)' },
          ticks: {
            color: '#64748b',
            font: { family: 'JetBrains Mono', size: 11 },
            callback: (v) => formatCurrency(v)
          }
        }
      }
    }
  });
}

// Portfolio & Paper Trading Simulator
async function loadPortfolioData() {
  if (!state.token) {
    document.getElementById('portfolio-guest-notice').style.display = 'block';
    document.getElementById('portfolio-user-view').style.display = 'none';
    return;
  }

  document.getElementById('portfolio-guest-notice').style.display = 'none';
  document.getElementById('portfolio-user-view').style.display = 'block';

  try {
    const res = await fetch('/api/portfolio/', {
      headers: { 'Authorization': `Bearer ${state.token}` }
    });
    if (!res.ok) {
      if (res.status === 401) logoutUser();
      return;
    }
    const data = await res.json();
    renderPortfolioView(data);
  } catch (err) {
    console.error('Portfolio error:', err);
  }
}

function renderPortfolioView(data) {
  const sum = data.summary;
  document.getElementById('port-cash').textContent = formatCurrency(sum.cash_balance_usd, 'usd');
  document.getElementById('port-crypto-val').textContent = formatCurrency(sum.total_crypto_value_usd, 'usd');
  document.getElementById('port-net-worth').textContent = formatCurrency(sum.total_net_worth_usd, 'usd');

  const pnlEl = document.getElementById('port-pnl');
  const isPos = sum.total_profit_loss_usd >= 0;
  pnlEl.textContent = `${isPos ? '+' : ''}${formatCurrency(sum.total_profit_loss_usd, 'usd')} (${isPos ? '+' : ''}${sum.total_profit_loss_pct}%)`;
  pnlEl.style.color = isPos ? 'var(--emerald)' : 'var(--rose)';

  // Holdings Table
  const tbody = document.getElementById('portfolio-holdings-body');
  tbody.innerHTML = '';
  if (data.holdings.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-dim); padding: 24px;">No active crypto holdings. Buy coins from the Markets tab to build your portfolio!</td></tr>`;
  } else {
    data.holdings.forEach(h => {
      const isHPos = h.pnl_usd >= 0;
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>
          <div class="coin-cell">
            <div class="coin-name-block">
              <span class="coin-symbol">${h.symbol}</span>
              <span class="coin-full-name">${h.name}</span>
            </div>
          </div>
        </td>
        <td class="mono">${h.quantity}</td>
        <td class="mono">${formatCurrency(h.avg_buy_price_usd, 'usd')}</td>
        <td class="mono" style="font-weight: 700;">${formatCurrency(h.current_price_usd, 'usd')}</td>
        <td class="mono" style="font-weight: 700;">${formatCurrency(h.current_value_usd, 'usd')}</td>
        <td>
          <span class="${isHPos ? 'badge-positive' : 'badge-negative'}">
            ${isHPos ? '▲ +' : '▼ '}$${Math.abs(h.pnl_usd).toFixed(2)} (${h.pnl_percentage}%)
          </span>
        </td>
        <td style="text-align: right;">
          <div style="display: inline-flex; gap: 6px;">
            <button class="btn btn-emerald btn-sm" onclick="openTradeModal('${h.coin_id}', '${h.symbol}', '${h.name.replace(/'/g, "\\'")}', ${h.current_price_usd}, 'BUY')">Buy</button>
            <button class="btn btn-rose btn-sm" onclick="openTradeModal('${h.coin_id}', '${h.symbol}', '${h.name.replace(/'/g, "\\'")}', ${h.current_price_usd}, 'SELL')">Sell</button>
          </div>
        </td>
      `;
      tbody.appendChild(tr);
    });
  }

  // Transactions Table
  const txBody = document.getElementById('portfolio-transactions-body');
  txBody.innerHTML = '';
  if (data.recent_transactions.length === 0) {
    txBody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-dim); padding: 20px;">No trade executions yet.</td></tr>`;
  } else {
    data.recent_transactions.forEach(t => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><span class="${t.type === 'BUY' ? 'badge-positive' : 'badge-negative'}">${t.type}</span></td>
        <td style="font-weight: 700;">${t.symbol}</td>
        <td class="mono">${t.quantity}</td>
        <td class="mono">$${Number(t.price_usd).toLocaleString()}</td>
        <td class="mono" style="font-weight: 700;">$${Number(t.total_usd).toLocaleString()}</td>
        <td style="color: var(--text-dim); font-size: 12px;">${t.timestamp}</td>
      `;
      txBody.appendChild(tr);
    });
  }
}

async function resetPortfolioBalance() {
  if (!confirm('Are you sure you want to reset your portfolio and restore $50,000.00 USD virtual balance?')) return;
  try {
    const res = await fetch('/api/auth/reset-balance', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${state.token}` }
    });
    if (res.ok) {
      showToast('Portfolio and balance reset to $50,000 USD!', 'success');
      loadPortfolioData();
      checkAuthUser();
    }
  } catch (err) {
    showToast('Failed to reset portfolio', 'error');
  }
}

// Watchlist
async function toggleWatchlist(coinId, symbol, name) {
  const index = state.watchlist.indexOf(coinId);
  if (index > -1) {
    state.watchlist.splice(index, 1);
    localStorage.setItem('crypto_watchlist', JSON.stringify(state.watchlist));
    showToast(`${name} removed from watchlist`);
  } else {
    state.watchlist.push(coinId);
    localStorage.setItem('crypto_watchlist', JSON.stringify(state.watchlist));
    showToast(`${name} added to watchlist ⭐`);
  }
  renderMarketTable();
  if (state.currentTab === 'watchlist') renderWatchlist();
}

function renderWatchlist() {
  const tbody = document.getElementById('watchlist-table-body');
  const emptyMsg = document.getElementById('watchlist-empty-msg');
  const tableWrap = document.getElementById('watchlist-table-wrap');

  if (state.watchlist.length === 0) {
    emptyMsg.style.display = 'block';
    tableWrap.style.display = 'none';
    return;
  }

  emptyMsg.style.display = 'none';
  tableWrap.style.display = 'block';
  tbody.innerHTML = '';

  const watched = state.coins.filter(c => state.watchlist.includes(c.id));
  watched.forEach(c => {
    const change24h = c.price_change_percentage_24h || 0;
    const isPositive = change24h >= 0;

    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>
        <div class="coin-cell">
          <button class="btn btn-ghost btn-sm" style="padding: 2px 6px; border: none; font-size: 14px;" onclick="toggleWatchlist('${c.id}', '${c.symbol}', '${c.name.replace(/'/g, "\\'")}')">⭐</button>
          <img src="${c.image}" class="coin-img" alt="${c.name}">
          <div class="coin-name-block">
            <span class="coin-symbol">${c.symbol.toUpperCase()}</span>
            <span class="coin-full-name">${c.name}</span>
          </div>
        </div>
      </td>
      <td class="mono" style="font-weight: 700;">${formatCurrency(c.current_price)}</td>
      <td>
        <span class="${isPositive ? 'badge-positive' : 'badge-negative'}">
          ${isPositive ? '▲ +' : '▼ '}${change24h.toFixed(2)}%
        </span>
      </td>
      <td class="mono" style="font-size: 12.5px; color: var(--text-dim);">${formatCurrency(c.high_24h)} / ${formatCurrency(c.low_24h)}</td>
      <td class="mono" style="font-size: 12.5px;">${formatCurrency(c.market_cap)}</td>
      <td style="text-align: right;">
        <div style="display: inline-flex; gap: 6px;">
          <button class="btn btn-emerald btn-sm" onclick="openTradeModal('${c.id}', '${c.symbol}', '${c.name.replace(/'/g, "\\'")}', ${c.current_price}, 'BUY')">Buy</button>
          <button class="btn btn-primary btn-sm" onclick="quickPredict('${c.symbol.toUpperCase()}-USD')">Predict 🧠</button>
        </div>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// Authentication Controller
let authMode = 'login';

function openAuthModal(mode = 'login') {
  authMode = mode;
  setAuthMode(mode);
  document.getElementById('auth-modal').classList.add('show');
}

function closeAuthModal() {
  document.getElementById('auth-modal').classList.remove('show');
}

function setAuthMode(mode) {
  authMode = mode;
  document.getElementById('auth-modal-title').textContent = mode === 'login' ? 'Sign In to CryptoPulse' : 'Create Free Account & Claim $50k';
  document.getElementById('auth-name-group').style.display = mode === 'register' ? 'block' : 'none';
  document.getElementById('auth-submit-btn').textContent = mode === 'login' ? 'Sign In' : 'Create Account';
  document.getElementById('auth-tab-login').classList.toggle('btn-primary', mode === 'login');
  document.getElementById('auth-tab-register').classList.toggle('btn-primary', mode === 'register');
}

async function handleAuthSubmit(e) {
  e.preventDefault();
  const email = document.getElementById('auth-email').value.trim();
  const password = document.getElementById('auth-password').value;
  const name = document.getElementById('auth-name').value.trim();

  const endpoint = authMode === 'login' ? '/api/auth/login' : '/api/auth/register';
  const payload = authMode === 'login' ? { email, password } : { name, email, password };

  try {
    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Authentication failed');

    state.token = data.token;
    state.user = data.user;
    localStorage.setItem('crypto_token', data.token);

    showToast(data.message || 'Authenticated successfully!', 'success');
    closeAuthModal();
    updateUserHeader();
    if (state.currentTab === 'portfolio') loadPortfolioData();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function checkAuthUser() {
  if (!state.token) {
    updateUserHeader();
    return;
  }
  try {
    const res = await fetch('/api/auth/me', {
      headers: { 'Authorization': `Bearer ${state.token}` }
    });
    if (res.ok) {
      state.user = await res.json();
      updateUserHeader();
    } else {
      logoutUser();
    }
  } catch (err) {
    console.error('Auth verification error:', err);
  }
}

function updateUserHeader() {
  const authActions = document.getElementById('auth-actions-wrap');
  const userProfile = document.getElementById('user-profile-wrap');

  if (state.user) {
    authActions.style.display = 'none';
    userProfile.style.display = 'flex';
    document.getElementById('user-avatar-initial').textContent = state.user.name.charAt(0).toUpperCase();
    document.getElementById('user-name-display').textContent = state.user.name;
    document.getElementById('user-balance-display').textContent = formatCurrency(state.user.virtual_balance_usd, 'usd');
  } else {
    authActions.style.display = 'flex';
    userProfile.style.display = 'none';
  }
}

function logoutUser() {
  state.token = null;
  state.user = null;
  localStorage.removeItem('crypto_token');
  updateUserHeader();
  showToast('Logged out successfully');
  if (state.currentTab === 'portfolio') loadPortfolioData();
}

// Trading Modal
function openTradeModal(coinId, symbol, name, price, type = 'BUY') {
  if (!state.token) {
    showToast('Please sign in or register to execute paper trades', 'error');
    openAuthModal('login');
    return;
  }
  state.currentTradeCoin = { coinId, symbol, name, price };
  setTradeType(type);

  document.getElementById('trade-modal-title').textContent = `${type} ${name} (${symbol.toUpperCase()})`;
  document.getElementById('trade-price-display').value = `$${Number(price).toLocaleString()}`;
  document.getElementById('trade-quantity-input').value = '1';
  calculateTradeTotal();

  const balance = state.user?.virtual_balance_usd || 50000.0;
  document.getElementById('trade-balance-hint').textContent = `Available Cash Balance: $${balance.toLocaleString(undefined, { minimumFractionDigits: 2 })}`;

  document.getElementById('trade-modal').classList.add('show');
}

function closeTradeModal() {
  document.getElementById('trade-modal').classList.remove('show');
}

function setTradeType(type) {
  state.tradeType = type;
  const isBuy = type === 'BUY';
  document.getElementById('trade-tab-buy').classList.toggle('btn-emerald', isBuy);
  document.getElementById('trade-tab-buy').classList.toggle('btn-ghost', !isBuy);
  document.getElementById('trade-tab-sell').classList.toggle('btn-rose', !isBuy);
  document.getElementById('trade-tab-sell').classList.toggle('btn-ghost', isBuy);

  const btn = document.getElementById('trade-execute-btn');
  btn.textContent = `Confirm ${type} Order`;
  btn.className = isBuy ? 'btn btn-emerald' : 'btn btn-rose';
  btn.style.width = '100%';
}

function calculateTradeTotal() {
  if (!state.currentTradeCoin) return;
  const qty = parseFloat(document.getElementById('trade-quantity-input').value) || 0;
  const total = qty * state.currentTradeCoin.price;
  document.getElementById('trade-total-display').value = `$${total.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

async function executeTradeOrder() {
  if (!state.currentTradeCoin) return;
  const qty = parseFloat(document.getElementById('trade-quantity-input').value);
  if (!qty || qty <= 0) {
    showToast('Please enter a valid quantity', 'error');
    return;
  }

  const endpoint = state.tradeType === 'BUY' ? '/api/portfolio/buy' : '/api/portfolio/sell';
  const payload = {
    coin_id: state.currentTradeCoin.coinId,
    symbol: state.currentTradeCoin.symbol,
    name: state.currentTradeCoin.name,
    quantity: qty,
    price_usd: state.currentTradeCoin.price
  };

  try {
    const res = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${state.token}`
      },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Trade execution failed');

    showToast(data.message, 'success');
    closeTradeModal();
    checkAuthUser();
    if (state.currentTab === 'portfolio') loadPortfolioData();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// Initializer
document.addEventListener('DOMContentLoaded', () => {
  checkAuthUser();
  fetchGlobalStats();
  fetchMarketData();
  
  // Auto-refresh market data every 30 seconds
  setInterval(fetchMarketData, 30000);
});

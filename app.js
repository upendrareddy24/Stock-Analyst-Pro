document.addEventListener('DOMContentLoaded', () => {
    const analyzeBtn = document.getElementById('analyzeBtn');
    const tickerInput = document.getElementById('tickerInput');
    const dashboard = document.getElementById('dashboard');
    const welcome = document.getElementById('welcome');
    const loader = document.getElementById('loader');
    const demoButtons = document.querySelectorAll('.demo-btn');

    const modalOverlay = document.getElementById('modalOverlay');
    const modalBody = document.getElementById('modalBody');
    const closeModal = document.getElementById('closeModal');
    const historyList = document.getElementById('historyList');
    const bullishList = document.getElementById('bullishList');
    const exportReportBtn = document.getElementById('exportReportBtn');
    const autocompleteResults = document.getElementById('autocompleteResults');
    const intelligenceList = document.getElementById('intelligenceList');

    let analysisHistory = [];
    let bullishRadar = [];
    let personaWatchlists = {}; // We'll fetch this on demand for the modal

    // We no longer update local watchlists, the server handles persistence during /api/analyze

    const fetchSharedContent = async () => {
        try {
            const [histRes, radarRes] = await Promise.all([
                fetch('/api/history'),
                fetch('/api/radar')
            ]);
            analysisHistory = await histRes.json();
            bullishRadar = await radarRes.json();
            renderHistory();
            renderBullishRadar();
        } catch (err) {
            console.error("Failed to load shared content:", err);
        }
    };

    const renderBullishRadar = () => {
        if (bullishRadar.length === 0) {
            bullishList.innerHTML = '<p class="empty-msg">No recent gems.</p>';
            return;
        }

        bullishList.innerHTML = '';
        bullishRadar.forEach(item => {
            const div = document.createElement('div');
            div.className = 'history-item glass radar-item-glow';

            div.innerHTML = `
                <div class="history-item-header">
                    <h4>${item.ticker}</h4>
                    <div style="display:flex; flex-direction:column; align-items:flex-end; gap:4px;">
                        <span class="mini-consensus rating-pill rating-buy">${item.consensus.split(' ')[0]}</span>
                        <span style="font-size:0.65rem; color:var(--accent-blue); font-weight:700;">${item.master_score || 0} pts</span>
                    </div>
                </div>
                <div class="date">${item.date}</div>
            `;

            div.addEventListener('click', () => {
                tickerInput.value = item.ticker;
                handleAnalyze(item.ticker);
            });

            bullishList.appendChild(div);
        });
    };

    const renderHistory = () => {
        if (analysisHistory.length === 0) {
            historyList.innerHTML = '<p class="empty-msg">No recent history.</p>';
            return;
        }

        historyList.innerHTML = '';
        analysisHistory.forEach(item => {
            const div = document.createElement('div');
            div.className = 'history-item glass';

            let badgeClass = 'rating-hold';
            if (item.consensus.includes("Bullish")) badgeClass = 'rating-buy';
            if (item.consensus.includes("Bearish")) badgeClass = 'rating-avoid';

            div.innerHTML = `
                <div class="history-item-header">
                    <h4>${item.ticker}</h4>
                    <span class="mini-consensus rating-pill ${badgeClass}">${item.consensus.split(' ')[0]}</span>
                </div>
                <div class="date">${item.date}</div>
            `;

            div.addEventListener('click', () => {
                tickerInput.value = item.ticker;
                handleAnalyze(item.ticker);
            });

            historyList.appendChild(div);
        });
    };

    const handleAnalyze = async (ticker) => {
        if (!ticker) return;

        // Show loader
        welcome.classList.add('hidden');
        dashboard.classList.add('hidden');
        loader.classList.remove('hidden');

        try {
            const response = await fetch(`/api/analyze?ticker=${ticker}`);
            const data = await response.json();

            if (data.error) {
                alert(data.error);
                loader.classList.add('hidden');
                welcome.classList.remove('hidden');
                return;
            }

            renderDashboard(data);
            fetchSharedContent(); // Refresh shared lists
        } catch (err) {
            console.error(err);
            alert("Failed to reach the consulting spirits. Is the server running?");
            loader.classList.add('hidden');
            welcome.classList.remove('hidden');
        }
    };

    const renderDashboard = (data) => {
        loader.classList.add('hidden');
        dashboard.classList.remove('hidden');

        // Update Priority Section
        if (data.priority) {
            document.getElementById('priorityAction').textContent = data.priority.action;
            document.getElementById('priorityReasoning').textContent = data.priority.reasoning;
            document.getElementById('priorityConfidence').textContent = data.priority.confidence;
        }

        // Update Summary
        document.getElementById('tickerName').textContent = data.ticker;
        document.getElementById('tickerPrice').textContent = `$${data.current_price.toFixed(2)}`;

        const consensusEl = document.getElementById('overallConsensus');
        consensusEl.textContent = data.consensus;

        // Dynamic colors for consensus
        if (data.consensus && data.consensus.includes("Bullish")) {
            consensusEl.style.borderColor = 'var(--accent-green)';
            consensusEl.style.color = 'var(--accent-green)';
            consensusEl.style.background = 'rgba(16, 185, 129, 0.1)';
        } else if (data.consensus && data.consensus.includes("Bearish")) {
            consensusEl.style.borderColor = 'var(--accent-red)';
            consensusEl.style.color = 'var(--accent-red)';
            consensusEl.style.background = 'rgba(239, 68, 68, 0.1)';
        } else {
            consensusEl.style.borderColor = '#fbbf24';
            consensusEl.style.color = '#fbbf24';
            consensusEl.style.background = 'rgba(245, 158, 11, 0.1)';
        }

        // --- MASTER SCORE RENDER ---
        const scoreContainer = document.getElementById('masterScoreContainer');
        if (data.master_score) {
            document.getElementById('masterScoreValue').textContent = data.master_score.value + "/100";
            document.getElementById('masterScoreLabel').textContent = data.master_score.label;
            scoreContainer.classList.remove('hidden');

            // Color Logic
            const val = data.master_score.value;
            scoreContainer.className = 'master-score-badge'; // reset
            if (val >= 70) scoreContainer.classList.add('score-high');
            else if (val >= 40) scoreContainer.classList.add('score-mid');
            else scoreContainer.classList.add('score-low');
        } else {
            scoreContainer.classList.add('hidden');
        }

        // --- TRADE PLAN RENDER ---
        const tradeCard = document.getElementById('tradePlanCard');
        if (data.trade_plan) {
            document.getElementById('tpEntry').textContent = data.trade_plan.entry_zone;
            document.getElementById('tpTarget').textContent = data.trade_plan.target;
            document.getElementById('tpStop').textContent = data.trade_plan.stop_loss;
            tradeCard.classList.remove('hidden');
        } else {
            tradeCard.classList.add('hidden');
        }

        // --- VITAL SIGNS RENDER ---
        if (data.technical_indicators) {
            const tech = data.technical_indicators;

            // Squeeze
            const sqEl = document.getElementById('vitalSqueeze');
            const sqDet = document.getElementById('vitalSqueezeDetail');
            sqEl.textContent = tech.squeeze.status;
            sqDet.textContent = tech.squeeze.detail;
            sqEl.style.color = tech.squeeze.color === 'orange' ? '#fbbf24' : tech.squeeze.color === 'green' ? '#34d399' : tech.squeeze.color === 'red' ? '#f87171' : '#9ca3af';
            renderSparkline('sparklineSqueeze', tech.squeeze.history, tech.squeeze.color === 'orange' ? '#fbbf24' : '#34d399');

            // RSI
            document.getElementById('vitalRSI').textContent = tech.rsi.value;
            const rsiBar = document.getElementById('vitalRSIBar');
            rsiBar.style.width = `${tech.rsi.value}%`;
            rsiBar.style.backgroundColor = tech.rsi.value > 70 ? '#f87171' : tech.rsi.value < 30 ? '#34d399' : '#fbbf24';
            renderSparkline('sparklineRSI', tech.rsi.history, tech.rsi.value > 70 ? '#f87171' : tech.rsi.value < 30 ? '#34d399' : '#3b82f6');

            // Volume
            document.getElementById('vitalVol').textContent = tech.rel_volume.value + 'x';
            document.getElementById('vitalVolDetail').style.color = tech.rel_volume.value > 1.2 ? '#34d399' : '#9ca3af';
            renderSparkline('sparklineVol', tech.rel_volume.history, '#3b82f6');

            // MACD
            document.getElementById('vitalMACD').textContent = tech.macd.status;
            document.getElementById('vitalMACDDetail').textContent = tech.macd.trend;
            renderSparkline('sparklineMACD', tech.macd.history, '#8b5cf6');

            // Options Intel
            const optCard = document.getElementById('optionsIntelCard');
            if (data.options_intel && data.options_intel.has_options) {
                optCard.style.display = 'block';
                document.getElementById('optionsSentiment').textContent = data.options_intel.sentiment;
                document.getElementById('optionsStrike').textContent = `$${data.options_intel.max_oi_strike}`;
                document.getElementById('pcRatio').textContent = data.options_intel.pc_ratio;
                document.getElementById('avgIV').textContent = data.options_intel.avg_iv;

                const sentPill = document.getElementById('optionsSentiment');
                sentPill.className = 'mini-consensus rating-pill';
                if (data.options_intel.sentiment.includes('Bullish')) sentPill.classList.add('rating-buy');
                else if (data.options_intel.sentiment.includes('Bearish')) sentPill.classList.add('rating-sell');
                else sentPill.classList.add('rating-hold');
            } else {
                if (optCard) optCard.style.display = 'none';
            }
        }

        // --- EXPORT HANDLER ---
        if (exportReportBtn) {
            exportReportBtn.onclick = () => exportResearchReport(data);
        }

        // Render Strategies
        const strategiesList = document.getElementById('strategiesList');
        strategiesList.innerHTML = '';
        if (data.actionable_strategies && data.actionable_strategies.length > 0) {
            data.actionable_strategies.forEach(strategy => {
                const card = document.createElement('div');
                card.className = 'strategy-card glass';
                card.innerHTML = `
                    <h4>${strategy.type}</h4>
                    <p>${strategy.description}</p>
                    <div class="strategy-books">
                        ${strategy.books.map(book => `<span class="book-tag">${book}</span>`).join('')}
                    </div>
                `;
                strategiesList.appendChild(card);
            });
        } else {
            strategiesList.innerHTML = '<p class="text-secondary">No specific technical setups detected for current price action.</p>';
        }

        // Render Council
        const councilGrid = document.getElementById('councilGrid');
        councilGrid.innerHTML = '';
        Object.entries(data.personas).forEach(([persona, result]) => {
            const card = document.createElement('div');
            card.className = 'persona-card glass';

            const ratingClass = `rating-${result.rating.toLowerCase().split(' ')[0]}`;

            card.innerHTML = `
                <div class="persona-header">
                    <h4>${persona}</h4>
                    <span class="rating-pill ${ratingClass}">${result.rating}</span>
                </div>
                <ul class="persona-reasons">
                    ${result.reasons.length > 0 ?
                    result.reasons.map(r => `<li>${r}</li>`).join('') :
                    `<li>Maintaining neutral posture based on current data.</li>`}
                </ul>
                <div class="strategy-books" style="margin-top: auto; opacity: 0.6">
                    <small>Influenced by: ${result.books && result.books.length > 0 ? result.books.slice(0, 3).join(', ') : 'Market Observation'}</small>
                </div>
            `;

            // Card Click Event for Modal
            card.addEventListener('click', async () => {
                // Show initial modal with reasoning
                modalBody.innerHTML = `
                    <div class="modal-details">
                        <h2>${persona}'s Reasoning</h2>
                        <p>${result.details || "No further details available."}</p>
                        <div id="modalWatchlist" class="watchlist-section">
                            <span class="modal-books-title">🕒 Loading shared picks...</span>
                        </div>
                        <span class="modal-books-title">Referenced Wisdom:</span>
                        <div class="strategy-books">
                            ${result.books.map(book => `<span class="book-tag">${book}</span>`).join('')}
                        </div>
                    </div>
                `;
                modalOverlay.classList.remove('hidden');

                // Fetch shared picks for this persona
                try {
                    const pickRes = await fetch(`/api/persona_picks?persona=${persona}`);
                    const picks = await pickRes.json();
                    const watchlistEl = document.getElementById('modalWatchlist');

                    if (picks && picks.length > 0) {
                        watchlistEl.innerHTML = `
                            <span class="modal-books-title">🏆 Shared Hall of Fame</span>
                            <div class="watchlist-grid">
                                ${picks.map(item => `
                                    <div class="watchlist-item glass-low" title="Added: ${item.date}" onclick="document.getElementById('tickerInput').value='${item.ticker}'; document.getElementById('analyzeBtn').click(); document.getElementById('closeModal').click();">
                                        <strong>${item.ticker}</strong>
                                        <span class="mini-rating ${item.rating.includes('Strong') ? 'strong-buy' : 'buy'}">${item.rating}</span>
                                    </div>
                                `).join('')}
                            </div>
                        `;
                    } else {
                        watchlistEl.innerHTML = '<p class="text-secondary" style="font-size: 0.8rem; margin-top: 10px;">No shared picks for this persona yet.</p>';
                    }
                } catch (err) {
                    console.error("Failed to load picks:", err);
                }
            });

            councilGrid.appendChild(card);
        });

        // Render News
        const newsFeed = document.getElementById('newsFeed');
        newsFeed.innerHTML = '';
        if (data.recent_news && data.recent_news.length > 0) {
            data.recent_news.forEach(item => {
                const newsItem = document.createElement('div');
                newsItem.className = 'news-item glass';
                newsItem.innerHTML = `
                    <div class="news-info">
                        <h4>${item.title}</h4>
                        <p>${item.summary ? item.summary.substring(0, 150) + '...' : 'Recent catalyst update.'}</p>
                    </div>
        <div class="news-meta">
            <span class="news-date">${item.date}</span>
            <a href="${item.url}" target="_blank" class="news-link">Read More <i class="fas fa-external-link-alt"></i></a>
        </div>
    `;
                newsFeed.appendChild(newsItem);
            });
        } else {
            newsFeed.innerHTML = '<p class="text-secondary">No recent news catalysts found for this ticker.</p>';
        }
    };

    const intelligenceFeedList = document.getElementById('intelligenceList');

    const fetchIntelligence = async () => {
        try {
            const resp = await fetch('/api/market_intelligence');
            const data = await resp.json();
            renderIntelligence(data);
        } catch (err) {
            console.error("Failed to fetch market intelligence:", err);
            intelligenceFeedList.innerHTML = '<p class="text-secondary" style="font-size:0.7rem;">Feed temporarily unavailable.</p>';
        }
    };

    const renderIntelligence = (leads) => {
        if (!leads || leads.length === 0) {
            intelligenceFeedList.innerHTML = '<p class="empty-msg">Scanning for market leaders...</p>';
            return;
        }

        intelligenceFeedList.innerHTML = '';
        leads.forEach(lead => {
            const div = document.createElement('div');
            div.className = 'history-item glass intelligence-item';

            div.innerHTML = `
                <div class="history-item-header">
                    <h4>${lead.ticker}</h4>
                    <span class="mini-consensus rating-pill rating-buy">${lead.master_score} pts</span>
                </div>
                <div class="intelligence-meta">
                    <span class="target">Target: ${lead.potential_gain}</span>
                    <span class="time">${lead.date.split(' ')[1]} ${lead.date.split(' ')[2]}</span>
                </div>
            `;

            div.addEventListener('click', () => {
                tickerInput.value = lead.ticker;
                handleAnalyze(lead.ticker);
            });

            intelligenceFeedList.appendChild(div);
        });
    };

    // Modals and Search logic
    closeModal.addEventListener('click', () => modalOverlay.classList.add('hidden'));

    modalOverlay.addEventListener('click', (e) => {
        if (e.target === modalOverlay) modalOverlay.classList.add('hidden');
    });

    analyzeBtn.addEventListener('click', () => handleAnalyze(tickerInput.value));
    tickerInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleAnalyze(tickerInput.value);
    });

    demoButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            tickerInput.value = btn.textContent;
            handleAnalyze(btn.textContent);
        });
    });

    // --- SPARKLINE HELPER ---
    const renderSparkline = (canvasId, dataPoints, color) => {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        const w = canvas.width;
        const h = canvas.height;

        ctx.clearRect(0, 0, w, h);
        if (!dataPoints || dataPoints.length < 2) return;

        ctx.beginPath();
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.lineJoin = 'round';

        const min = Math.min(...dataPoints);
        const max = Math.max(...dataPoints);
        const range = max - min || 1;

        dataPoints.forEach((val, i) => {
            const x = (i / (dataPoints.length - 1)) * w;
            const y = h - ((val - min) / range) * h;
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        });

        ctx.stroke();
    };

    // --- REPORT EXPORT ---
    const exportResearchReport = (data) => {
        const timestamp = new Date().toLocaleString();
        let report = `# ANALYST MASTERMIND REPORT: ${data.ticker}\n`;
        report += `Generated: ${timestamp}\n`;
        report += `Price: $${data.current_price}\n\n`;
        report += `## CONSENSUS VERDICT: ${data.consensus}\n`;
        report += `Priority Action: ${data.priority.action}\n`;
        report += `${data.priority.reasoning}\n\n`;

        report += `## TRADE PLAN\n`;
        report += `- Entry Zone: ${data.trade_plan.entry_zone}\n`;
        report += `- Target: ${data.trade_plan.target}\n`;
        report += `- Stop Loss: ${data.trade_plan.stop_loss}\n\n`;

        report += `## THE ANALYST COUNCIL\n`;
        Object.entries(data.personas).forEach(([persona, res]) => {
            report += `### ${persona}: ${res.rating}\n`;
            res.reasons.forEach(r => report += `- ${r}\n`);
            report += `\n`;
        });

        const blob = new Blob([report], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${data.ticker}_Mastermind_Report.md`;
        a.click();
    };

    // --- AUTOCOMPLETE LOGIC ---
    let debounceTimer;
    const tickerList = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMD', 'AMD', 'META', 'GOOGL', 'AMZN', 'NFLX', 'BRK.B', 'V', 'PYPL', 'DIS', 'BA', 'MSTR', 'COIN', 'PLTR', 'SNOW'];

    tickerInput.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        const query = tickerInput.value.trim().toUpperCase();
        if (query.length < 1) {
            autocompleteResults.classList.add('hidden');
            return;
        }

        debounceTimer = setTimeout(() => {
            const matches = tickerList.filter(t => t.startsWith(query)).slice(0, 5);
            if (matches.length > 0) {
                autocompleteResults.innerHTML = matches.map(m => `
                    <div class="autocomplete-item" data-ticker="${m}">
                        <span class="symbol">${m}</span>
                        <span class="name">Stock Ticker</span>
                    </div>
                `).join('');
                autocompleteResults.classList.remove('hidden');

                autocompleteResults.querySelectorAll('.autocomplete-item').forEach(item => {
                    item.addEventListener('click', () => {
                        tickerInput.value = item.getAttribute('data-ticker');
                        autocompleteResults.classList.add('hidden');
                        handleAnalyze(tickerInput.value);
                    });
                });
            } else {
                autocompleteResults.classList.add('hidden');
            }
        }, 200);
    });

    document.addEventListener('click', (e) => {
        if (!tickerInput.contains(e.target) && !autocompleteResults.contains(e.target)) {
            autocompleteResults.classList.add('hidden');
        }
    });

    // Initial Render
    fetchSharedContent();
    fetchIntelligence();
    setInterval(fetchIntelligence, 30000); // Polling intelligence every 30s
});

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

    let analysisHistory = JSON.parse(localStorage.getItem('stock_history') || '[]');
    let bullishRadar = JSON.parse(localStorage.getItem('bullish_radar') || '[]');
    let personaWatchlists = JSON.parse(localStorage.getItem('persona_watchlists') || '{}');

    const updatePersonaWatchlists = (ticker, personas) => {
        let updated = false;
        Object.entries(personas).forEach(([persona, result]) => {
            if (!personaWatchlists[persona]) personaWatchlists[persona] = [];

            // If Buy/Strong Buy, add to list
            if (result.rating.includes("Buy")) {
                // Remove existing to update timestamp/position
                personaWatchlists[persona] = personaWatchlists[persona].filter(item => item.ticker !== ticker);
                personaWatchlists[persona].unshift({
                    ticker,
                    rating: result.rating,
                    date: new Date().toLocaleDateString(),
                    timestamp: Date.now()
                });
                updated = true;
            } else if (result.rating.includes("Avoid") || result.rating.includes("Hold")) {
                // Remove if it's no longer a buy
                const preLength = personaWatchlists[persona].length;
                personaWatchlists[persona] = personaWatchlists[persona].filter(item => item.ticker !== ticker);
                if (personaWatchlists[persona].length !== preLength) updated = true;
            }

            // Keep top 20 items per persona
            if (personaWatchlists[persona].length > 20) {
                personaWatchlists[persona] = personaWatchlists[persona].slice(0, 20);
            }
        });

        if (updated) {
            localStorage.setItem('persona_watchlists', JSON.stringify(personaWatchlists));
        }
    };

    const saveToHistory = (ticker, consensus) => {
        const newItem = {
            ticker,
            consensus,
            date: new Date().toLocaleDateString() + ' ' + new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            timestamp: Date.now()
        };

        // Remove existing if same ticker to move to top
        analysisHistory = analysisHistory.filter(item => item.ticker !== ticker);
        analysisHistory.unshift(newItem);
        analysisHistory = analysisHistory.slice(0, 10); // Keep last 10

        localStorage.setItem('stock_history', JSON.stringify(analysisHistory));
        renderHistory();

        // Also update Bullish Radar
        if (consensus.includes("Bullish")) {
            const radarItem = {
                ticker,
                consensus,
                date: new Date().toLocaleDateString(),
                timestamp: Date.now()
            };
            bullishRadar = bullishRadar.filter(item => item.ticker !== ticker);
            bullishRadar.unshift(radarItem);
            bullishRadar = bullishRadar.slice(0, 10);
            localStorage.setItem('bullish_radar', JSON.stringify(bullishRadar));
            renderBullishRadar();
        } else {
            // If rating changed to non-bullish, remove it
            const prevLen = bullishRadar.length;
            bullishRadar = bullishRadar.filter(item => item.ticker !== ticker);
            if (bullishRadar.length !== prevLen) {
                localStorage.setItem('bullish_radar', JSON.stringify(bullishRadar));
                renderBullishRadar();
            }
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
                    <span class="mini-consensus rating-pill rating-buy">${item.consensus.split(' ')[0]}</span>
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
            saveToHistory(data.ticker, data.consensus);
            updatePersonaWatchlists(data.ticker, data.personas);
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

            // RSI
            document.getElementById('vitalRSI').textContent = tech.rsi;
            const rsiBar = document.getElementById('vitalRSIBar');
            rsiBar.style.width = `${tech.rsi}%`;
            rsiBar.style.backgroundColor = tech.rsi > 70 ? '#f87171' : tech.rsi < 30 ? '#34d399' : '#fbbf24';

            // Volume
            document.getElementById('vitalVol').textContent = tech.rel_volume + 'x';
            document.getElementById('vitalVolDetail').style.color = tech.rel_volume > 1.2 ? '#34d399' : '#9ca3af';

            // MACD
            document.getElementById('vitalMACD').textContent = tech.macd.status;
            document.getElementById('vitalMACDDetail').textContent = tech.macd.trend;
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
            card.addEventListener('click', () => {
                modalBody.innerHTML = `
                    <div class="modal-details">
                    <h2>${persona}'s Reasoning</h2>
                    <p>${result.details || "No further details available."}</p>

                    ${personaWatchlists[persona] && personaWatchlists[persona].length > 0 ? `
                        <div class="watchlist-section">
                            <span class="modal-books-title">🏆 ${persona}'s Top Picks</span>
                            <div class="watchlist-grid">
                                ${personaWatchlists[persona].map(item => `
                                    <div class="watchlist-item glass-low" title="Added: ${item.date}" onclick="document.getElementById('tickerInput').value='${item.ticker}'; document.getElementById('analyzeBtn').click(); document.getElementById('closeModal').click();">
                                        <strong>${item.ticker}</strong>
                                        <span class="mini-rating ${item.rating.includes('Strong') ? 'strong-buy' : 'buy'}">${item.rating}</span>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                        ` : ''}

                    <span class="modal-books-title">Referenced Wisdom:</span>
                    <div class="strategy-books">
                        ${result.books.map(book => `<span class="book-tag">${book}</span>`).join('')}
                    </div>
                </div>
                    </div>
                `;
                modalOverlay.classList.remove('hidden');
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

    // Initial Render
    renderHistory();
    renderBullishRadar();
});

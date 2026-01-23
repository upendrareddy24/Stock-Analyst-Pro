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
                <div class="date">${formatDate(item.date)}</div>
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
                <div class="date">${formatDate(item.date)}</div>
            `;

            div.addEventListener('click', () => {
                tickerInput.value = item.ticker;
                handleAnalyze(item.ticker);
            });

            historyList.appendChild(div);
        });
    };

    const handleAnalyze = async (ticker) => {
        window.handleAnalyze = handleAnalyze;
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
            let actionText = data.priority.action;
            if (actionText.includes("Mixed signals") || actionText.includes("Not yet aligned")) {
                actionText = "Signals are mixed across styles. Treat as watchlist candidate: consider alerts, not a full-sized entry.";
            }
            document.getElementById('priorityAction').textContent = actionText;
            document.getElementById('priorityReasoning').textContent = data.priority.reasoning;
            document.getElementById('priorityConfidence').textContent = data.priority.confidence;

            // Update Trade Bias Banner
            const biasVal = document.getElementById('tradeBiasValue');
            const biasContainer = document.getElementById('tradeBiasContainer');
            let biasText = "Neutral / Mixed – watchlist, not an A+ setup yet.";
            let biasColor = "var(--accent-amber)";

            if (data.master_score && data.master_score.value > 70) {
                biasText = "Bullish – Strong technical and fundamental alignment.";
                biasColor = "var(--accent-green)";
            } else if (data.master_score && data.master_score.value < 40) {
                biasText = "Bearish / Caution – Multiple risk factors detected.";
                biasColor = "var(--accent-red)";
            }

            biasVal.textContent = biasText;
            biasContainer.style.borderColor = biasColor;
            biasVal.style.color = biasColor;
        }

        // --- MARKET CLIMATE RENDER ---
        const radar = document.getElementById('marketRadar');
        if (data.market_climate) {
            radar.style.display = 'flex';
            const status = document.getElementById('climateText');
            const icon = document.getElementById('climateIcon');

            status.textContent = data.market_climate.status;
            icon.style.color = data.market_climate.color === 'green' ? '#34d399' : data.market_climate.color === 'red' ? '#f87171' : '#fbbf24';
            status.style.color = icon.style.color;

            radar.title = data.market_climate.description + '\n' + data.market_climate.details;
        }

        // --- SMART CHART RENDER ---
        if (data.chart_data && window.LightweightCharts) {
            // Inject VWAP series into vpaData package for chart rendering
            const chartPayload = data.vpa_analysis || [];
            if (data.technical_indicators && data.technical_indicators.vwap) {
                chartPayload.vwap_series = data.technical_indicators.vwap.full_history;
            }
            renderSmartChart(data.chart_data, chartPayload, data.patterns, data.trade_plan);
        }

        // --- TREND ALIGNMENT RENDER ---
        const mtf = data.technical_indicators.mtf_alignment;
        const rs = data.technical_indicators.relative_strength;

        const updateTag = (id, val) => {
            const el = document.getElementById(id);
            const span = el.querySelector('.trend-val');
            span.textContent = val;
            span.className = 'trend-val ' + val.toLowerCase();
        };

        updateTag('tagMonthly', mtf.monthly);
        updateTag('tagWeekly', mtf.weekly);
        updateTag('tagDaily', mtf.daily);

        const leaderTag = document.getElementById('rsLeaderTag');
        if (rs.status === 'Leader') {
            leaderTag.classList.remove('hidden');
            leaderTag.title = `Outperforming SPY by ${rs.value}%`;
        } else {
            leaderTag.classList.add('hidden');
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

            // Pyramiding Logic
            const pSection = document.getElementById('pyramidSection');
            if (pSection) {
                if (data.trade_plan.pyramiding) {
                    pSection.classList.remove('hidden');
                    const p1 = data.trade_plan.pyramiding[0];
                    const p2 = data.trade_plan.pyramiding[1];
                    document.getElementById('pyramidEntry1').textContent = `${p1.price} (${p1.size})`;
                    document.getElementById('pyramidEntry2').textContent = `${p2.price} (${p2.size})`;

                    // Show Risk/Share
                    const riskEl = document.getElementById('tpRisk');
                    if (riskEl) riskEl.textContent = `$${data.trade_plan.risk_per_share.toFixed(2)}`;
                } else {
                    pSection.classList.add('hidden');
                }
            }

            tradeCard.classList.remove('hidden');

            // Initial Position Sizer Calculation
            updatePositionSizer(data.trade_plan);

            // Attach listeners for dynamic update
            document.getElementById('accountSize').oninput = () => updatePositionSizer(data.trade_plan);
            document.getElementById('riskPercent').oninput = () => updatePositionSizer(data.trade_plan);
        } else {
            tradeCard.classList.add('hidden');
        }

        // --- VITAL SIGNS RENDER ---
        if (data.technical_indicators) {
            const tech = data.technical_indicators;

            // Snapshot Header
            const snapshotEl = document.getElementById('snapshotText');
            let snapshot = "Normal Volatility, Neutral RSI";
            if (tech.adx.value > 25) snapshot = "Strong trend, " + snapshot;
            if (tech.rel_volume.value > 1.2) snapshot = "Elevated volume, " + snapshot;
            if (tech.macd.status.includes("Bullish")) snapshot = "Bullish momentum, " + snapshot;
            if (tech.squeeze.status.includes("Squeeze On")) snapshot = "Volatility Squeeze, " + snapshot;
            snapshotEl.textContent = snapshot + ".";

            // Squeeze
            const sqEl = document.getElementById('vitalSqueeze');
            const sqCard = sqEl.closest('.vital-card');
            sqEl.textContent = tech.squeeze.status.replace("OFF", "Off").replace("ON", "On");
            document.getElementById('vitalSqueezeDetail').textContent = `Volatility: ${tech.squeeze.status.includes('Off') ? 'Normal (no squeeze active)' : 'Squeeze active'}`;

            let sqColor = '#94a3b8';
            if (tech.squeeze.color === 'green') sqColor = '#34d399';
            else if (tech.squeeze.color === 'red') sqColor = '#f87171';
            else if (tech.squeeze.color === 'orange') sqColor = '#fbbf24';

            sqCard.style.border = `1px solid ${sqColor}`;
            sqCard.style.boxShadow = `0 0 10px ${sqColor}20`; // subtle glow
            renderSparkline('sparklineSqueeze', tech.squeeze.history, sqColor);

            // RSI
            const rsiVal = tech.rsi.value;
            const rsiCard = document.getElementById('vitalRSI').closest('.vital-card');
            let rsiColor = '#fbbf24'; // Neutral
            if (rsiVal < 30) rsiColor = '#34d399'; // Bullish
            else if (rsiVal > 70) rsiColor = '#f87171'; // Bearish

            document.getElementById('vitalRSI').textContent = rsiVal;
            document.getElementById('vitalRSIBar').style.width = `${rsiVal}%`;
            document.getElementById('vitalRSIBar').style.backgroundColor = rsiColor;

            rsiCard.style.border = `1px solid ${rsiColor}`;
            rsiCard.style.boxShadow = `0 0 10px ${rsiColor}20`;
            renderSparkline('sparklineRSI', tech.rsi.history, rsiColor);

            // Volume
            const rvolVal = tech.rel_volume.value;
            const volCard = document.getElementById('vitalVol').closest('.vital-card');
            let rvolColor = '#fbbf24';
            if (rvolVal > 1.2) rvolColor = '#34d399'; // High
            else if (rvolVal < 0.8) rvolColor = '#f87171'; // Low

            document.getElementById('vitalVol').textContent = rvolVal + 'x';
            document.getElementById('vitalVolDetail').style.color = rvolColor;

            volCard.style.border = `1px solid ${rvolColor}`;
            volCard.style.boxShadow = `0 0 10px ${rvolColor}20`;
            renderSparkline('sparklineVol', tech.rel_volume.history, rvolColor);

            // MACD
            const macdStatus = tech.macd.status;
            const macdCard = document.getElementById('vitalMACD').closest('.vital-card');
            let macdColor = '#fbbf24';
            if (macdStatus.includes('Bullish')) macdColor = '#34d399';
            if (macdStatus.includes('Bearish')) macdColor = '#f87171';

            document.getElementById('vitalMACD').textContent = macdStatus;
            document.getElementById('vitalMACD').style.color = macdColor;
            document.getElementById('vitalMACDDetail').textContent = tech.macd.trend;

            macdCard.style.border = `1px solid ${macdColor}`;
            macdCard.style.boxShadow = `0 0 10px ${macdColor}20`;
            renderSparkline('sparklineMACD', tech.macd.history, macdColor);

            // ATR
            const atrVal = tech.atr.value;
            const atrCard = document.getElementById('cardATR'); // Targeted by ID
            // ATR is neutral/risk, so we usually keep it neutral unless extreme. 
            // Let's just use neutral blue/purple styling for consistency unless we add historical ATR comparison.
            const atrColor = '#60a5fa';

            document.getElementById('vitalATR').textContent = `$${atrVal}`;
            atrCard.style.border = `1px solid ${atrColor}`;
            atrCard.style.boxShadow = `0 0 10px ${atrColor}20`;
            renderSparkline('sparklineATR', tech.atr.history, atrColor);

            // ADX
            const adxVal = tech.adx.value;
            const adxCard = document.getElementById('cardADX');
            let adxColor = '#fbbf24';
            if (adxVal > 25) adxColor = '#34d399'; // Strong Trend
            if (adxVal < 20) adxColor = '#f87171'; // Weak Trend

            document.getElementById('vitalADX').textContent = adxVal;
            document.getElementById('vitalADXBar').style.width = `${Math.min(adxVal, 100)}%`;
            document.getElementById('vitalADXBar').style.backgroundColor = adxColor;
            document.getElementById('vitalADXStatus').textContent = tech.adx.status;

            adxCard.style.border = `1px solid ${adxColor}`;
            adxCard.style.boxShadow = `0 0 10px ${adxColor}20`;

            // VWAP Deviation
            // Check if VWAP data exists to avoid crash on cached data
            if (tech.vwap && tech.vwap.deviation) {
                const vwapDevStr = tech.vwap.deviation;
                const vwapDevNum = parseFloat(vwapDevStr.replace('%', ''));
                const vwapCard = document.getElementById('cardVWAP');
                let vwapColor = '#fbbf24';
                if (vwapDevNum > 0) vwapColor = '#34d399'; // Bullish
                if (vwapDevNum < 0) vwapColor = '#f87171'; // Bearish

                document.getElementById('vitalVWAP').textContent = vwapDevStr;
                document.getElementById('vitalVWAP').style.color = vwapColor;
                document.getElementById('vitalVWAPDetail').textContent = `vs Avg Price: $${tech.vwap.value}`;

                vwapCard.style.border = `1px solid ${vwapColor}`;
                vwapCard.style.boxShadow = `0 0 10px ${vwapColor}20`;
            }


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

                // --- OPTION PICK RENDER ---
                const pickContainer = document.getElementById('optionPick');
                if (pickContainer && data.options_intel.recommendation && data.options_intel.recommendation.type !== 'WAIT') {
                    pickContainer.classList.remove('hidden');
                    document.getElementById('optType').textContent = data.options_intel.recommendation.type;
                    document.getElementById('optStrike').textContent = `$${data.options_intel.recommendation.strike}`;
                    document.getElementById('optReason').textContent = data.options_intel.recommendation.reason;

                    const typePill = document.getElementById('optType');
                    typePill.className = 'mini-consensus rating-pill';
                    typePill.classList.add(data.options_intel.recommendation.type === 'CALL' ? 'rating-buy' : 'rating-sell');
                } else if (pickContainer) {
                    pickContainer.classList.add('hidden');
                }
            } else {
                if (optCard) optCard.style.display = 'none';
            }

            // --- CHART PATTERNS ---
            const pSection = document.getElementById('patternSection');
            const pList = document.getElementById('patternList');
            if (data.patterns && data.patterns.length > 0) {
                pSection.style.display = 'block';
                pList.innerHTML = data.patterns.map(p => `
                    <div class="pattern-item" style="background: rgba(0,0,0,0.2); padding: 0.6rem; border-radius: 8px; border: 1px solid rgba(139, 92, 246, 0.2);">
                        <h5 style="font-size: 0.7rem; color: #a78bfa; margin: 0;">${p.name} <span class="mini-consensus" style="font-size:0.5rem; background:rgba(255,255,255,0.1);">${p.status}</span></h5>
                        <p style="font-size: 0.6rem; color: #94a3b8; margin: 0.2rem 0 0 0;">${p.description}</p>
                    </div>
                `).join('');
            } else if (pSection) {
                pSection.style.display = 'none';
            }

            // --- VPA RENDER ---
            const vSection = document.getElementById('vpaSection');
            const vList = document.getElementById('vpaList');
            if (data.vpa_analysis && data.vpa_analysis.length > 0) {
                vSection.style.display = 'block';
                vList.innerHTML = data.vpa_analysis.map(v => `
                    <div class="pattern-item" style="background: rgba(0,0,0,0.2); padding: 0.6rem; border-radius: 8px; border: 1px solid rgba(236, 72, 153, 0.2);">
                        <h5 style="font-size: 0.7rem; color: #fbcfe8; margin: 0;">${v.name} <span class="mini-consensus" style="font-size:0.5rem; background:rgba(255,255,255,0.1);">${v.bias}</span></h5>
                        <p style="font-size: 0.6rem; color: #94a3b8; margin: 0.2rem 0 0 0;">${v.description}</p>
                    </div>
                `).join('');
            } else if (vSection) {
                vSection.style.display = 'none';
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
                <p style="font-size: 0.8rem; font-style: italic; color: var(--accent-blue); margin-top: 0.2rem;">
                    ${translatePersonaAction(persona, result.rating)}
                </p>
                <ul class="persona-reasons" style="margin-top: 0.5rem;">
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
                const sentiment = item.title.toLowerCase().match(/up|rise|surge|gain|profit|buy|beat|growth|positive/i) ? 'bullish' :
                    item.title.toLowerCase().match(/down|fall|drop|loss|sell|miss|negative|risk/i) ? 'bearish' : 'mixed';
                const tag = item.title.toLowerCase().includes('earn') ? 'Earnings' :
                    item.title.toLowerCase().includes('ai') ? 'AI' :
                        item.title.toLowerCase().includes('fed') || item.title.toLowerCase().includes('macro') ? 'Macro' : 'News';

                const newsItem = document.createElement('div');
                newsItem.className = 'news-item glass';
                newsItem.innerHTML = `
                    <div class="news-info">
                        <div style="display:flex; gap: 0.5rem; margin-bottom: 0.5rem;">
                            <span class="news-tag tag-${sentiment}">${sentiment}</span>
                            <span class="news-tag" style="background: rgba(255,255,255,0.05); color: var(--text-secondary);">${tag}</span>
                        </div>
                        <h4>${item.title}</h4>
                        <p>${item.summary ? item.summary.substring(0, 150) + '...' : 'Recent catalyst update.'}</p>
                    </div>
                    <div class="news-meta">
                        <span class="news-date">${formatDate(item.date)}</span>
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

    // --- POSITION SIZER PERSISTENCE ---
    const accInput = document.getElementById('accountSize');
    const riskInput = document.getElementById('riskPercent');

    // Load saved preferences
    if (localStorage.getItem('analyst_portfolio')) {
        accInput.value = localStorage.getItem('analyst_portfolio');
    }
    if (localStorage.getItem('analyst_risk')) {
        riskInput.value = localStorage.getItem('analyst_risk');
    }

    // Save on change
    accInput.addEventListener('input', () => {
        localStorage.setItem('analyst_portfolio', accInput.value);
    });
    riskInput.addEventListener('input', () => {
        localStorage.setItem('analyst_risk', riskInput.value);
    });

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

function updatePositionSizer(tradePlan) {
    const accSize = parseFloat(document.getElementById('accountSize').value) || 10000;
    const rPk = parseFloat(document.getElementById('riskPercent').value) || 2;
    const entry = parseFloat(tradePlan.entry_zone.replace('$', '').split('-')[0].trim()) || 0;
    const stop = parseFloat(tradePlan.stop_loss.replace('$', '').trim()) || 0;
    const resultEl = document.getElementById('sizerResult');
    if (entry > 0 && stop > 0 && entry > stop) {
        const totalRisk = accSize * (rPk / 100);
        const riskPerShare = entry - stop;
        const shares = Math.floor(totalRisk / riskPerShare);
        resultEl.textContent = shares > 0 ? shares + ' Shares' : '-- Shares';
    } else {
        resultEl.textContent = '-- Shares';
    }
}

/* --- SECTOR SCOUT LOGIC --- */
document.getElementById('sectorScoutBtn').addEventListener('click', async () => {
    const modal = document.getElementById('sectorModal');
    modal.classList.remove('hidden');
    const container = document.getElementById('sectorLeaderboard');
    container.innerHTML = '<div class="loader-container"><div class="spinner"></div><p>Performing competitive sector analysis... This may take a moment.</p></div>';
    try {
        const response = await fetch('/api/sector_scout');
        const data = await response.json();
        renderSectorLeaderboard(data);
    } catch (err) {
        console.error(err);
        container.innerHTML = '<p class="error-msg">Failed to scout sectors. Consult the logs.</p>';
    }
});

document.getElementById('closeSectorModal').addEventListener('click', () => {
    document.getElementById('sectorModal').classList.add('hidden');
});

function renderSectorLeaderboard(data) {
    const container = document.getElementById('sectorLeaderboard');
    container.innerHTML = '';
    Object.entries(data).forEach(([sector, stocks]) => {
        const sectorEl = document.createElement('div');
        sectorEl.className = 'sector-card glass';
        let stockHTML = stocks.map((s, idx) => `
            <div class="sector-ticker ${idx === 0 ? 'winner' : ''}" onclick="window.handleAnalyze('${s.ticker}'); document.getElementById('sectorModal').classList.add('hidden');">
                <div class="ticker-info">
                    <span class="ticker-sym">${idx === 0 ? '🏆 ' : ''}${s.ticker}</span>
                    <span class="ticker-price">$${s.price.toFixed(2)}</span>
                </div>
                <div class="ticker-stats">
                    <div class="ticker-score">${s.score}</div>
                    <div class="ticker-label">${s.label}</div>
                    <div style="font-size:0.55rem; color:${s.top_rating.includes('Strong') ? '#34d399' : '#94a3b8'}; margin-top:2px;">
                        <i class="fas fa-users"></i> ${s.top_rating}
                    </div>
                </div>
            </div>
        `).join('');
        sectorEl.innerHTML = `<h4><i class="fas fa-layer-group"></i> ${sector}</h4>${stockHTML}`;
        container.appendChild(sectorEl);
    });
}

/* --- SMART CHART LOGIC --- */
let chartInstance = null;

function renderSmartChart(ohlcData, vpaData, patterns, tradePlan) {
    const container = document.getElementById("tvChart");
    if (!container) return;

    // Reset
    container.innerHTML = "";
    if (chartInstance) {
        chartInstance.remove();
        chartInstance = null;
    }

    // Create Chart
    chartInstance = LightweightCharts.createChart(container, {
        width: container.clientWidth,
        height: 350,
        layout: {
            background: { type: "solid", color: "transparent" },
            textColor: "#94a3b8",
        },
        grid: {
            vertLines: { color: "rgba(255, 255, 255, 0.05)" },
            horzLines: { color: "rgba(255, 255, 255, 0.05)" },
        },
        timeScale: {
            borderColor: "rgba(255, 255, 255, 0.1)",
        },
        rightPriceScale: {
            borderColor: "rgba(255, 255, 255, 0.1)",
        },
    });

    // Candlestick Series
    const candleSeries = chartInstance.addCandlestickSeries({
        upColor: "#34d399",
        downColor: "#f87171",
        borderVisible: false,
        wickUpColor: "#34d399",
        wickDownColor: "#f87171",
    });
    candleSeries.setData(ohlcData);

    // Draw Trade Plan Lines (Support/Resistance)
    if (tradePlan) {
        const parsePrice = (str) => {
            const match = str.match(/\$?([\d,]+\.?\d*)/);
            return match ? parseFloat(match[1].replace(",", "")) : null;
        };

        const stopPrice = parsePrice(tradePlan.stop_loss);
        const targetPrice = parsePrice(tradePlan.target);
        const entryPrice = parsePrice(tradePlan.entry_zone.split('-')[0]);

        if (stopPrice) {
            candleSeries.createPriceLine({
                price: stopPrice,
                color: '#f87171',
                lineWidth: 1, // Thinner
                lineStyle: 1, // Dotted
                axisLabelVisible: true,
                title: 'STOP',
            });
        }

        if (targetPrice) {
            candleSeries.createPriceLine({
                price: targetPrice,
                color: '#60a5fa',
                lineWidth: 1, // Thinner
                lineStyle: 1, // Dotted
                axisLabelVisible: true,
                title: 'TARGET',
            });
        }

        if (entryPrice) {
            candleSeries.createPriceLine({
                price: entryPrice,
                color: '#fbbf24',
                lineWidth: 1, // Thinner
                lineStyle: 2, // Dashed
                axisLabelVisible: true,
                title: 'ENTRY',
            });
        }
    }

    // Draw VWAP Line
    if (vpaData && vpaData.vwap_series && vpaData.vwap_series.length > 0) {
        const vwapLine = chartInstance.addLineSeries({
            color: '#a78bfa', // Purple for Institutional VWAP
            lineWidth: 2,
            lineStyle: 0, // Solid
            title: 'VWAP',
        });
        vwapLine.setData(vpaData.vwap_series);
    }

    // Volume Series (Overlay)
    const volumeSeries = chartInstance.addHistogramSeries({
        priceFormat: {
            type: "volume",
        },
        priceScaleId: "", // Set as an overlay
        scaleMargins: {
            top: 0.8,
            bottom: 0,
        },
    });

    // Map volume colors
    const volumeData = ohlcData.map(d => ({
        time: d.time,
        value: d.volume,
        color: d.close >= d.open ? "rgba(52, 211, 153, 0.3)" : "rgba(248, 113, 113, 0.3)",
    }));
    volumeSeries.setData(volumeData);

    // Markers for VPA
    const markers = [];
    if (vpaData && vpaData.length > 0) {
        const lastTime = ohlcData[ohlcData.length - 1].time;
        vpaData.forEach(vpa => {
            markers.push({
                time: lastTime,
                position: vpa.bias === "Bullish" ? "belowBar" : "aboveBar",
                color: vpa.color === "green" ? "#34d399" : vpa.color === "red" ? "#f87171" : "#fbbf24",
                shape: vpa.bias === "Bullish" ? "arrowUp" : "arrowDown",
                text: vpa.name,
            });
        });
    }
    candleSeries.setMarkers(markers);

    // Resize Handler
    new ResizeObserver(entries => {
        if (entries.length === 0 || entries[0].target !== container) { return; }
        const newRect = entries[0].contentRect;
        chartInstance.applyOptions({ width: newRect.width, height: newRect.height });
    }).observe(container);
}

function translatePersonaAction(persona, rating) {
    const r = rating.toLowerCase();
    const actions = {
        'Growth Maverick': { 'buy': 'Strong momentum trend setup.', 'hold': 'Awaiting breakout confirmation.', 'avoid': 'Trend structure is broken.' },
        'Macro Strategist': { 'buy': 'Aligned with fiscal tailwinds.', 'hold': 'Macro environment is uncertain.', 'avoid': 'Significant macro headwinds.' },
        'News Watch': { 'buy': 'Catalyst confirmed by volume.', 'hold': 'Awaiting specific news event.', 'avoid': 'Negative news sentiment detected.' },
        'Psychology Expert': { 'buy': 'Extreme fear turning to greed.', 'hold': 'Market sentiment is balanced.', 'avoid': 'Hyper-euphoria; topping risk.' },
        'Quant Master': { 'buy': 'Statistical edge is high.', 'hold': 'Mean reversion in progress.', 'avoid': 'Low probability setup.' },
        'Trend Follower': { 'buy': 'Classic bull trend configuration.', 'hold': 'Price is range-bound.', 'avoid': 'Bearish trend established.' },
        'Value Sage': { 'buy': 'Deep value with safety margin.', 'hold': 'Fairly valued at current levels.', 'avoid': 'Severely overvalued.' }
    };

    const ratingKey = r.includes('buy') ? 'buy' : r.includes('avoid') || r.includes('sell') ? 'avoid' : 'hold';
    return (actions[persona] && actions[persona][ratingKey]) || 'Maintaining focused neutral posture.';
}

function formatDate(dateStr) {
    if (!dateStr) return '--';
    try {
        const date = new Date(dateStr);
        if (isNaN(date)) return dateStr; // Return raw string if parsing fails
        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            hour12: false
        });
    } catch (e) {
        return dateStr;
    }
}


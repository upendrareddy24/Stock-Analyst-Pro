import pandas as pd
import json
import os
from typing import Dict, List, Any

class AnalystEngine:
    def __init__(self, books_db_path: str = "books_db.json"):
        with open(books_db_path, 'r') as f:
            self.books = json.load(f)
        
        self.personas = {
            "Value Sage": self._analyze_value,
            "Growth Maverick": self._analyze_growth,
            "Trend Follower": self._analyze_trend,
            "Quant Master": self._analyze_quant,
            "Psychology Expert": self._analyze_psychology,
            "Macro Strategist": self._analyze_macro,
            "News Watch": self._analyze_news
        }

    def analyze_ticker(self, ticker: str, df: pd.DataFrame, news: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Runs the full council analysis on a ticker, including news if provided.
        """
        if df.empty or len(df) < 50:
            return {"error": "Insufficient data"}

        results = {}
        for persona, func in self.personas.items():
            if persona == "News Watch":
                results[persona] = func(news) if news else {"rating": "Hold", "score": 0, "reasons": ["No recent news found."], "details": "No news catalysts detected to influence short-term direction.", "books": []}
            else:
                results[persona] = func(df)

        actionable_strategies = self._detect_specific_strategies(df, news)
        
        return {
            "ticker": ticker,
            "current_price": round(df['Close'].iloc[-1], 2),
            "consensus": self._calculate_consensus(results),
            "priority": self._generate_priority(results, actionable_strategies),
            "master_score": self._calculate_master_score(results, actionable_strategies),
            "trade_plan": self._generate_trade_plan(df, results, actionable_strategies),
            "personas": results,
            "actionable_strategies": actionable_strategies,
            "recent_news": news[:5] if news else []
        }

    def _generate_priority(self, results: Dict[str, Any], strategies: List[Dict[str, Any]]) -> Dict[str, Any]:
        buy_count = sum(1 for p in results.values() if "Buy" in p['rating'])
        
        if buy_count >= 5:
            return {
                "action": "URGENT BUY 🚀",
                "confidence": "High",
                "reasoning": "Rare 5-persona alignment. Technicals, Momentum, and Sentiment are converging simultaneously."
            }
        elif buy_count >= 3:
            return {
                "action": "STRATEGIC ACCUMULATE 📈",
                "confidence": "Medium-High",
                "reasoning": "Majority consensus reached. Momentum is building, but wait for 'Strategy Spotlight' triggers for optimal entry."
            }
        elif any(s['type'] == "Positive News Catalyst" for s in strategies):
            return {
                "action": "CATALYST WATCH ⚡",
                "confidence": "Medium",
                "reasoning": "News-driven potential. Technicals are lagging, but the news event could spark a sudden breakout."
            }
        else:
            return {
                "action": "PATIENT WATCH ⏱️",
                "confidence": "Neutral",
                "reasoning": "Mixed signals across different styles. Not yet aligned for a high-probability trade."
            }

    def _detect_specific_strategies(self, df: pd.DataFrame, news: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Derives specific strategy recommendations based on technical patterns and news catalysts.
        """
        strategies = []
        current_price = df['Close'].iloc[-1]
        vol = df['Volume'].iloc[-1]
        avg_vol = df['Volume'].tail(20).mean()

        # 0. News-Driven Catalyst
        if news:
            positive_keywords = ["upgrade", "beat", "buy", "outperforms", "growth", "approval", "partnership"]
            catalyst_found = False
            for item in news[:3]:
                title_lower = item['title'].lower()
                if any(kw in title_lower for kw in positive_keywords):
                    catalyst_found = True
                    break
            
            if catalyst_found:
                strategies.append({
                    "type": "Positive News Catalyst",
                    "description": "High-impact news (upgrade/earnings beat) detected within the last 48 hours.",
                    "books": ["The Alchemy of Finance", "Liar's Poker"]
                })
        
        # 1. High Volume Breakout
        year_high = df['High'].tail(252).max()
        if current_price >= year_high * 0.98 and vol > avg_vol * 1.5:
            strategies.append({
                "type": "High Volume Breakout",
                "description": "Stock is breaking out of index/yearly highs with significant volume support.",
                "books": ["How to Make Money in Stocks", "Trade Like a Stock Market Wizard"]
            })

        # 2. Pullback Play (Long Term)
        sma50 = df['Close'].rolling(50).mean().iloc[-1]
        low_5d = df['Low'].tail(5).min()
        if current_price > sma50 and low_5d < sma50 * 1.02:
            strategies.append({
                "type": "Support Pullback",
                "description": "Bullish stock cooling off to major support (SMA50), offering a low-risk entry.",
                "books": ["Stan Weinstein's Secrets", "Market Wizards"]
            })

        # 3. High Volatility Momentum
        atr = (df['High'] - df['Low']).tail(14).mean()
        volatility = (atr / current_price) * 100
        if volatility > 5:
            strategies.append({
                "type": "High Volatility Speculation",
                "description": "Significant price swings detected. suitable for aggressive traders.",
                "books": ["Reminiscences of a Stock Operator", "Trade Your Way to Financial Freedom"]
            })

        # 4. Long Term Value (Contrarian)
        rsi = self._calculate_rsi(df)
        if rsi < 35 and current_price < df['Close'].rolling(200).mean().iloc[-1]:
            strategies.append({
                "type": "Long Term Value / Reversal",
                "description": "Oversold conditions in a beaten-down stock. Classic value play.",
                "books": ["The Intelligent Investor", "Margin of Safety"]
            })

        return strategies

    def _calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> float:
        delta = df['Close'].diff()
        up = delta.clip(lower=0)
        down = -1 * delta.clip(upper=0)
        ma_up = up.rolling(period).mean()
        ma_down = down.rolling(period).mean()
        rs = ma_up / ma_down
        return 100 - (100 / (1 + rs)).iloc[-1]

    def _calculate_consensus(self, results: Dict[str, Any]) -> str:
        sentiment_scores = {
            "Strong Buy": 2,
            "Buy": 1,
            "Hold": 0,
            "Avoid": -1,
            "Strong Sell": -2
        }
        
        total_score = 0
        for r in results.values():
            total_score += sentiment_scores.get(r['rating'], 0)
            
        if total_score >= 6: return "Stong Bullish Consensus"
        if total_score >= 3: return "Bullish Consensus"
        if total_score <= -6: return "Strong Bearish Consensus"
        if total_score <= -3: return "Bearish Consensus"
        return "Neutral / Mixed"

    def _analyze_value(self, df: pd.DataFrame) -> Dict[str, Any]:
        # Principles: Margin of Safety, Intrinsic Value, Defensive
        current_price = df['Close'].iloc[-1]
        year_low = df['Low'].rolling(window=252, min_periods=1).min().iloc[-1]
        year_high = df['High'].rolling(window=252, min_periods=1).max().iloc[-1]
        
        # Valuation distance (Simple Proxy: Price vs 52W Low/High)
        price_pos = (current_price - year_low) / (year_high - year_low) if year_high > year_low else 0.5
        
        score = 0
        reasons = []
        
        if price_pos < 0.3:
            score += 2
            reasons.append("Trading near 52-week lows (Potential Deep Value)")
        elif price_pos > 0.8:
            score -= 1
            reasons.append("Trading near 52-week highs (Potential Overvaluation)")
            
        # Volatility check (Value sages like stability)
        std_dev = df['Close'].pct_change().std() * (252**0.5)
        if std_dev < 0.25:
            score += 1
            reasons.append("Low historical volatility (Stable investment)")
        
        rating = "Buy" if score >= 2 else "Avoid" if score < 0 else "Hold"
        
        details = (
            "Value Sage analysis focuses on the 'Margin of Safety'. "
            "We look for stocks trading at a discount to their intrinsic value or near historical lows. "
            "A high score suggests the downside risk is limited relative to the asset value."
        ) if rating == "Buy" else (
            "Currently, the price doesn't offer a significant enough discount for a value-based entry. "
            "We prefer waiting for a deeper correction or better fundamentals."
        )

        return {
            "rating": rating,
            "score": score,
            "reasons": reasons,
            "details": details,
            "books": [b['title'] for b in self.books if b['persona'] == "Value Sage"]
        }

    def _analyze_growth(self, df: pd.DataFrame) -> Dict[str, Any]:
        # Principles: Momentum, CANSLIM, Management Quality
        current_price = df['Close'].iloc[-1]
        sma50 = df['Close'].rolling(window=50).mean().iloc[-1]
        sma200 = df['Close'].rolling(window=200).mean().iloc[-1]
        
        score = 0
        reasons = []
        
        if current_price > sma50 > sma200:
            score += 2
            reasons.append("Stage 2 Uptrend confirmed (Price > SMA50 > SMA200)")
            
        # Relative Strength Proxy
        perf_3m = (df['Close'].iloc[-1] / df['Close'].iloc[-63] - 1) * 100
        if perf_3m > 20:
            score += 1
            reasons.append(f"Strong 3-month momentum (+{perf_3m:.1f}%)")
            
        rating = "Strong Buy" if score >= 3 else "Buy" if score >= 1 else "Hold"
        
        details = (
            "Growth Mavericks look for 'Superperformers'. We prioritize institutional momentum "
            "and Stage 2 uptrends. A Buy rating here indicates the 'path of least resistance' is currently UP."
        ) if "Buy" in rating else "Momentum is currently cooling or hasn't started. Growth experts prefer to see price > SMA50 before commitment."

        return {
            "rating": rating,
            "score": score,
            "reasons": reasons,
            "details": details,
            "books": [b['title'] for b in self.books if b['persona'] == "Growth Maverick"]
        }

    def _analyze_trend(self, df: pd.DataFrame) -> Dict[str, Any]:
        # Principles: Cutting Losses, Riding Winners, Chart Patterns
        current_price = df['Close'].iloc[-1]
        ema20 = df['Close'].ewm(span=20, adjust=False).mean().iloc[-1]
        
        score = 0
        reasons = []
        
        if current_price > ema20:
            score += 1
            reasons.append("Price above 20-day EMA (Short-term trend is up)")
            
        # Volume expansion on up days
        recent_vol = df['Volume'].tail(5).mean()
        avg_vol = df['Volume'].tail(20).mean()
        if recent_vol > avg_vol * 1.5 and df['Close'].iloc[-1] > df['Close'].iloc[-2]:
            score += 2
            reasons.append("Institutional accumulation detected (High volume breakout)")
            
        rating = "Buy" if score >= 2 else "Avoid" if score <= 0 else "Hold"
        
        details = (
            "Trend Followers 'trade the tape'. If the short-term EMA is rising and volume is expanding, "
            "we jump on board. We don't care about 'value'—only direction and strength."
        ) if rating == "Buy" else "The short-term trend is either broken or too weak to support a high-probability trade right now."

        return {
            "rating": rating,
            "score": score,
            "reasons": reasons,
            "details": details,
            "books": [b['title'] for b in self.books if b['persona'] == "Trend Follower"]
        }

    def _analyze_quant(self, df: pd.DataFrame) -> Dict[str, Any]:
        # Principles: Efficiency, Probabilities, Algorithmic
        score = 0
        reasons = []
        
        # Mean Reversion calculation
        z_score = (df['Close'].iloc[-1] - df['Close'].rolling(20).mean().iloc[-1]) / df['Close'].rolling(20).std().iloc[-1]
        
        if z_score < -2:
            score += 2
            reasons.append("Statistically oversold (Z-score < -2)")
        elif z_score > 2:
            score -= 2
            reasons.append("Statistically overbought (Z-score > 2)")
            
        rating = "Buy" if score >= 2 else "Hold" if score >= 0 else "Avoid"
        
        details = (
            "Quant analysis is purely statistical. A Buy rating suggests the ticker has deviated too far from its mean "
            "and has a high probability of reverting back (Mean Reversion)."
        ) if rating == "Buy" else "The price is currently within normal statistical boundaries (Z-score 0 to 1). No statistical edge detected."

        return {
            "rating": rating,
            "score": score,
            "reasons": reasons,
            "details": details,
            "books": [b['title'] for b in self.books if b['persona'] == "Quant Master"]
        }

    def _analyze_psychology(self, df: pd.DataFrame) -> Dict[str, Any]:
        # Principles: Fear/Greed, Bias, Mastery
        rsi = self._calculate_rsi(df)
        
        score = 0
        reasons = []
        
        if rsi > 70:
            score -= 2
            reasons.append(f"Market Greed: RSI is overbought ({rsi:.1f})")
        elif rsi < 30:
            score += 2
            reasons.append(f"Market Fear: RSI is oversold ({rsi:.1f})")
        else:
            reasons.append("Market in Neutral psychological territory")
            
        rating = "Buy" if score >= 2 else "Hold" if score >= 0 else "Avoid"
        
        details = (
            "The Psychology Expert monitors 'Fear and Greed'. We look for divergence between price "
            "and technical indicators like RSI. A Buy rating here suggests the market is overly pessimistic "
            "relative to the trend, offering a contrarian or consolidation entry."
        ) if rating == "Buy" else "The market is currently in a 'neutral' psychological zone—neither euphoria nor panic detected."

        return {
            "rating": rating,
            "score": score,
            "reasons": reasons,
            "details": details,
            "books": [b['title'] for b in self.books if b['persona'] == "Psychology Expert"]
        }

    def _analyze_news(self, news: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyzes news sentiment and determines impact on price movement.
        """
        if not news:
            return {"rating": "Hold", "score": 0, "reasons": ["No news available."], "books": []}

        positive_keywords = ["upgrade", "beat", "buy", "outperforms", "growth", "approval", "partnership", "success", "expanded"]
        negative_keywords = ["downgrade", "miss", "sell", "underperforms", "loss", "rejection", "lawsuit", "deficit", "investigation"]

        score = 0
        reasons = []
        
        for item in news[:5]:
            title_lower = item['title'].lower()
            if any(kw in title_lower for kw in positive_keywords):
                score += 1
                reasons.append(f"Positive sentiment: '{item['title'][:50]}...'")
            if any(kw in title_lower for kw in negative_keywords):
                score -= 1
                reasons.append(f"Negative sentiment: '{item['title'][:50]}...'")

        rating = "Strong Buy" if score >= 3 else "Buy" if score >= 1 else "Avoid" if score <= -2 else "Hold"
        
        details = (
            "News Watch filters real-time catalysts. A Buy rating suggests that recent news "
            "(earnings, upgrades, or partnerships) is acting as a powerful 'tailwind' for the stock."
        ) if "Buy" in rating else "No high-impact news catalysts detected in the recent headlines."

        return {
            "rating": rating,
            "score": score,
            "reasons": reasons,
            "details": details,
            "books": ["The Alchemy of Finance", "Liar's Poker", "Fooled by Randomness"]
        }

    def _analyze_macro(self, df: pd.DataFrame) -> Dict[str, Any]:
        # Principles: Cycles, Reflexivity, Second-level Thinking
        # Proxy: Long-term trend alignment
        sma200 = df['Close'].rolling(window=200).mean().iloc[-1]
        current_price = df['Close'].iloc[-1]
        
        score = 0
        reasons = []
        
        if current_price > sma200:
            score += 1
            reasons.append("Major cycle is in expansion phase (Price > SMA200)")
        else:
            score -= 1
            reasons.append("Major cycle is in contraction phase (Price < SMA200)")
            
        rating = "Buy" if score >= 1 else "Hold" if score == 0 else "Avoid"
        
        details = (
            "Macro Strategists look at the 'Big Picture'. We prioritize stocks that are above their "
            "200-day moving average (Long-term growth phase). A Buy rating indicates the "
            "underlying economic tide for this ticker is rising."
        ) if rating == "Buy" else "The macro trend is currently neutral or bearish. We prefer to stay on the sidelines until the 'tide' turns."

        return {
            "rating": rating,
            "score": score,
            "reasons": reasons,
            "details": details,
            "books": [b['title'] for b in self.books if b['persona'] == "Macro Strategist"]
        }

    def _calculate_master_score(self, results: Dict[str, Any], strategies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculates a 0-100 Master Score based on diverse inputs.
        """
        base_score = 50 # Neutral Start
        
        # 1. Persona Contributions
        for res in results.values():
            if "Strong Buy" in res['rating']: base_score += 8
            elif "Buy" in res['rating']: base_score += 4
            elif "Strong Sell" in res['rating'] or "Avoid" in res['rating']: base_score -= 5
            
        # 2. Strategy Bonuses
        base_score += (len(strategies) * 5)
        
        # 3. Consensus Multiplier
        consensus = self._calculate_consensus(results)
        if "Strong Bullish" in consensus: base_score += 10
        if "Bearish" in consensus: base_score -= 10
        
        # Clamp Score
        final_score = max(0, min(99, base_score))
        
        # Rating Label
        label = "A+ Setup 🚀" if final_score >= 85 else "B Setup ✅" if final_score >= 70 else "Neutral ⚠️" if final_score >= 40 else "Avoid ⛔"
        
        return {
            "value": final_score,
            "label": label
        }

    def _generate_trade_plan(self, df: pd.DataFrame, results: Dict[str, Any], strategies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generates simulated Entry, Target, and Stop Loss levels.
        """
        current_price = df['Close'].iloc[-1]
        score_data = self._calculate_master_score(results, strategies)
        
        if score_data['value'] < 60:
            return None # No trade recommended
            
        # Calculate ATR for volatility-based levels
        atr = (df['High'] - df['Low']).tail(14).mean()
        
        # Strategy specific tweaks
        is_momentum = any(s['type'] in ["High Volume Breakout", "High Volatility Speculation"] for s in strategies)
        is_value = any(s['type'] in ["Support Pullback", "Long Term Value / Reversal"] for s in strategies)
        
        stop_buffer = 1.5 * atr if is_momentum else 2.0 * atr # Wider stop for value (catch falling knife), tighter for momentum
        target_buffer = 3.0 * atr if is_momentum else 4.0 * atr # High reward targeting
        
        entry_low = current_price - (atr * 0.2)
        entry_high = current_price + (atr * 0.2)
        
        stop_loss = current_price - stop_buffer
        target_price = current_price + target_buffer
        
        risk = current_price - stop_loss
        reward = target_price - current_price
        rr_ratio = round(reward / risk, 1) if risk > 0 else 0
        
        return {
            "entry_zone": f"${entry_low:.2f} - ${entry_high:.2f}",
            "stop_loss": f"${stop_loss:.2f}",
            "target": f"${target_price:.2f}",
            "risk_reward": f"1:{rr_ratio}"
        }

if __name__ == "__main__":
    import sys
    sys.path.append('.')
    from data_orchestrator import DataOrchestrator
    
    orchestrator = DataOrchestrator()
    engine = AnalystEngine("books_db.json")
    
    ticker = "NVDA"
    df = orchestrator.get_stock_data(ticker)
    analysis = engine.analyze_ticker(ticker, df)
    
    print(f"\n--- {ticker} Analysis Report ---")
    print(f"Price: ${analysis['current_price']:.2f}")
    print(f"Consensus: {analysis['consensus']}")
    
    print("\n[Strategy Matches]")
    if analysis['actionable_strategies']:
        for strategy in analysis['actionable_strategies']:
            print(f" 🔥 {strategy['type']}: {strategy['description']}")
            print(f"    Referenced Books: {', '.join(strategy['books'])}")
    else:
        print(" No specific technical strategies detected at current price.")

    for persona, result in analysis['personas'].items():
        print(f"\n[{persona}] Rating: {result['rating']}")
        for reason in result['reasons']:
            print(f" - {reason}")

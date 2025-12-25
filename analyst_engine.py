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

    def analyze_ticker(self, ticker: str, df: pd.DataFrame, news: List[Dict[str, Any]] = None, options: Dict[str, Any] = None, benchmark_df: pd.DataFrame = None) -> Dict[str, Any]:
        """
        Runs the full council analysis on a ticker, including news, options, and benchmark.
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
        options_intel = self._analyze_options(options) if options else {"has_options": False}
        
        return {
            "ticker": ticker,
            "current_price": round(df['Close'].iloc[-1], 2),
            "consensus": self._calculate_consensus(results),
            "priority": self._generate_priority(results, actionable_strategies),
            "master_score": self._calculate_master_score(results, actionable_strategies, options_intel),
            "trade_plan": self._generate_trade_plan(df, results, actionable_strategies),
            "technical_indicators": {
                "squeeze": self._calculate_squeeze(df),
                "rsi": self._calculate_rsi(df),
                "macd": self._calculate_macd(df),
                "rel_volume": {
                    "value": round(df['Volume'].iloc[-1] / df['Volume'].tail(20).mean(), 2),
                    "history": [round(v, 2) for v in (df['Volume'] / df['Volume'].rolling(20).mean()).tail(20).tolist()]
                },
                "relative_strength": self._calculate_relative_strength(df, benchmark_df),
                "mtf_alignment": self._calculate_mtf_alignment(df)
            },
            "personas": results,
            "actionable_strategies": actionable_strategies,
            "recent_news": news[:5] if news else [],
            "recent_news": news[:5] if news else [],
            "options_intel": options_intel,
            "patterns": self._detect_chart_patterns(df),
            "vpa_analysis": self._detect_vpa_patterns(df),
            "chart_data": self._prepare_chart_data(df)
        }

    def _prepare_chart_data(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Helper to safely format chart data."""
        try:
            # Create a copy to avoid SettingWithCopy warnings
            chart_df = df.tail(150).copy()
            chart_df = chart_df.reset_index()
            
            # Ensure the first column (date) is named 'Date'
            chart_df.columns.values[0] = 'Date'
            
            return chart_df.apply(lambda x: {
                "time": x['Date'].strftime('%Y-%m-%d'),
                "open": x['Open'],
                "high": x['High'],
                "low": x['Low'],
                "close": x['Close'],
                "volume": x['Volume']
            }, axis=1).tolist()
        except Exception as e:
            print(f"Chart Data Error: {e}")
            return []

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
        rsi_val = self._calculate_rsi(df)['value'] # Access the value from the dict
        if rsi_val < 35 and current_price < df['Close'].rolling(200).mean().iloc[-1]:
            strategies.append({
                "type": "Long Term Value / Reversal",
                "description": "Oversold conditions in a beaten-down stock. Classic value play.",
                "books": ["The Intelligent Investor", "Margin of Safety"]
            })

        return strategies

    def _calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> Dict[str, Any]:
        delta = df['Close'].diff()
        up = delta.clip(lower=0)
        down = -1 * delta.clip(upper=0)
        ma_up = up.rolling(period).mean()
        ma_down = down.rolling(period).mean()
        rs = ma_up / ma_down
        rsi_series = 100 - (100 / (1 + rs))
        return {
            "value": round(rsi_series.iloc[-1], 1),
            "history": [round(v, 1) for v in rsi_series.tail(20).tolist()]
        }

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
        rsi_val = self._calculate_rsi(df)['value'] # Access the value from the dict
        
        score = 0
        reasons = []
        
        if rsi_val > 70:
            score -= 2
            reasons.append(f"Market Greed: RSI is overbought ({rsi_val:.1f})")
        elif rsi_val < 30:
            score += 2
            reasons.append(f"Market Fear: RSI is oversold ({rsi_val:.1f})")
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

    def _calculate_master_score(self, results: Dict[str, Any], strategies: List[Dict[str, Any]], options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Calculates a 0-100 Master Score based on diverse inputs, including options.
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
        
        # 4. Options Conviction Boost
        if options and options.get('has_options'):
            base_score += options.get('conviction_boost', 0)
        
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
        # We don't necessarily need options for the trade plan levels, but we'll pass None for consistency
        score_data = self._calculate_master_score(results, strategies, None)
        
        if score_data['value'] < 60:
            return None # No trade recommended
            
        # Calculate ATR for volatility-based levels
        atr = (df['High'] - df['Low']).tail(14).mean()
    def _generate_trade_plan(self, df: pd.DataFrame, consensus: str, signal_price: float) -> Dict[str, Any]:
        """Creates a Livermore-style pyramiding plan with ATR-based stops."""
        current_price = df['Close'].iloc[-1]
        atr = self._calculate_atr(df)
        
        # Volatility Sizing: Stop is 2x ATR for wiggle room
        stop_dist = atr * 2
        
        if "Bullish" in consensus:
            entry_1 = current_price # Pilot Position (30%)
            entry_2 = current_price + (atr * 0.5) # Confirmation (50%)
            stop_loss = current_price - stop_dist
            target = current_price + (stop_dist * 3) # 1:3 Risk/Reward
            
            return {
                "action": "LONG",
                "entry_zone": f"${entry_1:.2f} - ${entry_1*1.01:.2f}",
                "pyramiding": [
                    {"stage": "Pilot", "size": "30%", "price": f"${entry_1:.2f}"},
                    {"stage": "Add-on", "size": "50%", "price": f"${entry_2:.2f}"},
                ],
                "stop_loss": f"${stop_loss:.2f}",
                "target": f"${target:.2f}",
                "risk_per_share": stop_dist
            }
        
        elif "Bearish" in consensus:
            # Shorting Logic
            entry_1 = current_price
            entry_2 = current_price - (atr * 0.5)
            stop_loss = current_price + stop_dist
            target = current_price - (stop_dist * 3)
            
            return {
                "action": "SHORT",
                "entry_zone": f"${entry_1:.2f}",
                "pyramiding": [
                    {"stage": "Pilot", "size": "30%", "price": f"${entry_1:.2f}"},
                    {"stage": "Add-on", "size": "50%", "price": f"${entry_2:.2f}"},
                ],
                "stop_loss": f"${stop_loss:.2f}",
                "target": f"${target:.2f}",
                "risk_per_share": stop_dist
            }
            
        return None

    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """Calculates Average True Range for volatility sizing."""
        high_low = df['High'] - df['Low']
        high_close = (df['High'] - df['Close'].shift()).abs()
        low_close = (df['Low'] - df['Close'].shift()).abs()
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        return true_range.tail(period).mean()

    def _calculate_squeeze(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Detects if TTM Squeeze is On, Off, or Firing.
        """
        # 20 SMA
        sma20 = df['Close'].rolling(window=20).mean()
        
        # Bollinger Bands (2.0 std dev)
        std_dev = df['Close'].rolling(window=20).std()
        upper_bb = sma20 + (2.0 * std_dev)
        lower_bb = sma20 - (2.0 * std_dev)
        
        # Keltner Channels (1.5 ATR)
        atr = (df['High'] - df['Low']).rolling(window=20).mean() # Simple ATR approximation
        upper_kc = sma20 + (1.5 * atr)
        lower_kc = sma20 - (1.5 * atr)
        
        # Current status
        curr_upper_bb = upper_bb.iloc[-1]
        curr_lower_bb = lower_bb.iloc[-1]
        curr_upper_kc = upper_kc.iloc[-1]
        curr_lower_kc = lower_kc.iloc[-1]
        
        # Squeeze IS ON if BB are INSIDE KC
        is_squeezing = (curr_upper_bb < curr_upper_kc) and (curr_lower_bb > curr_lower_kc)
        
        # Momentum (Linear Reg or just Delta Price for simplicity proxy)
        # Using simple Delta relative to ATR for color
        momentum = df['Close'].iloc[-1] - sma20.iloc[-1]
        
        if is_squeezing:
            return {"status": "Squeeze ON", "color": "orange", "detail": "Volatility Compression", "history": [round(v, 2) for v in (df['Close'] - sma20).tail(20).tolist()]}
        else:
            # Check previous candle to see if it JUST fired
            prev_upper_bb = upper_bb.iloc[-2]
            prev_upper_kc = upper_kc.iloc[-2]
            was_squeezing = (prev_upper_bb < prev_upper_kc)
            
            if was_squeezing:
                return {"status": "Fired!", "color": "green" if momentum > 0 else "red", "detail": "Explosive Move Started", "history": [round(v, 2) for v in (df['Close'] - sma20).tail(20).tolist()]}
            
            return {"status": "Squeeze Off", "color": "gray", "detail": "Normal Volatility", "history": [round(v, 2) for v in (df['Close'] - sma20).tail(20).tolist()]}

    def _calculate_macd(self, df: pd.DataFrame) -> Dict[str, Any]:
        # EMA 12, 26
        ema12 = df['Close'].ewm(span=12, adjust=False).mean()
        ema26 = df['Close'].ewm(span=26, adjust=False).mean()
        macd_line = ema12 - ema26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        histogram = macd_line - signal_line
        
        curr_hist = histogram.iloc[-1]
        prev_hist = histogram.iloc[-2]
        
        status = "Bullish" if curr_hist > 0 else "Bearish"
        trend = "Strengthening" if abs(curr_hist) > abs(prev_hist) else "Weakening"
        
        return {
            "value": round(curr_hist, 2),
            "status": status,
            "trend": trend,
            "history": [round(v, 2) for v in histogram.tail(20).tolist()]
        }

    def _analyze_options(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """Processes raw option data into actionable sentiment insights."""
        if not options or not options.get('has_options'):
            return {"has_options": False}

        pc_ratio = options.get('put_call_ratio', 0)
        iv = options.get('avg_iv', 0)
        
        sentiment = "Neutral"
        conviction_boost = 0
        
        if pc_ratio < 0.6 and pc_ratio > 0:
            sentiment = "Highly Bullish"
            conviction_boost = 5 # +5 to master score
        elif pc_ratio > 1.2:
            sentiment = "Bearish (Hedging)"
            conviction_boost = -3
        elif iv > 80:
            sentiment = "Speculative (High Volatility)"
            
        return {
            "has_options": True,
            "sentiment": sentiment,
            "pc_ratio": pc_ratio,
            "avg_iv": iv,
            "conviction_boost": conviction_boost,
            "max_oi_strike": options.get('max_oi_strike'),
            "expiration": options.get('expiration'),
            "recommendation": self._generate_option_rec(options)
        }

    def _generate_option_rec(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """Generates a specific strike and type suggestion."""
        pc = options.get('put_call_ratio', 0)
        strike = options.get('max_oi_strike', 0)
        expr = options.get('expiration', '--')
        if pc < 0.65 and pc > 0:
            return {"type": "CALL", "strike": strike, "expiry": expr, "reason": "Bullish institutional wall detected."}
        elif pc > 1.25:
            return {"type": "PUT", "strike": strike, "expiry": expr, "reason": "Institutional hedging/bearish flow."}
        return {"type": "WAIT", "strike": "--", "expiry": "--", "reason": "Option flow is mixed."}

    def _calculate_relative_strength(self, df: pd.DataFrame, benchmark_df: pd.DataFrame) -> Dict[str, Any]:
        """Calculates 3-month performance vs SPY."""
        if benchmark_df is None or benchmark_df.empty:
            return {"status": "Neutral", "value": 0}
        
        # Align dates
        combined = pd.concat([df['Close'], benchmark_df['Close']], axis=1).dropna()
        combined.columns = ['Ticker', 'Benchmark']
        
        if len(combined) < 63: # 3 months of trading days
            return {"status": "Neutral", "value": 0}
            
        ticker_perf = (combined['Ticker'].iloc[-1] / combined['Ticker'].iloc[-63]) - 1
        bench_perf = (combined['Benchmark'].iloc[-1] / combined['Benchmark'].iloc[-63]) - 1
        
        rs_value = round((ticker_perf - bench_perf) * 100, 1)
        status = "Leader" if rs_value > 5 else "Laggard" if rs_value < -5 else "Neutral"
        
        return {"status": status, "value": rs_value}

    def _calculate_mtf_alignment(self, df: pd.DataFrame) -> Dict[str, str]:
        """Detects if Daily, Weekly, and Monthly charts are in sync."""
        if len(df) < 250: return {"daily": "--", "weekly": "--", "monthly": "--"}
        
        # Daily
        sma50_d = df['Close'].rolling(50).mean()
        daily = "Bullish" if df['Close'].iloc[-1] > sma50_d.iloc[-1] else "Bearish"
        
        # Weekly (Resample)
        weekly_df = df['Close'].resample('W').last()
        sma10_w = weekly_df.rolling(10).mean() # ~50 days
        weekly = "Bullish" if weekly_df.iloc[-1] > sma10_w.iloc[-1] else "Bearish"
        
        # Monthly
        monthly_df = df['Close'].resample('ME').last()
        sma10_m = monthly_df.rolling(10).mean() # ~10 months
        monthly = "Bullish" if monthly_df.iloc[-1] > sma10_m.iloc[-1] else "Bearish"
        
        return {"daily": daily, "weekly": weekly, "monthly": monthly}

    def _detect_chart_patterns(self, df: pd.DataFrame) -> List[Dict[str, str]]:
        """Detects classic chart patterns like Double Bottom, Cup & Handle, etc."""
        patterns = []
        if len(df) < 100: return []
        
        sub_df = df.tail(60)
        min1 = sub_df['Low'].iloc[0:20].min()
        min2 = sub_df['Low'].iloc[-20:].min()
        current = df['Close'].iloc[-1]
        
        # Double Bottom
        if abs(min1 - min2) / min1 < 0.03 and current > min2 * 1.05:
            patterns.append({
                "name": "Double Bottom",
                "status": "Bullish",
                "description": "Verified support at major level. Momentum is shifting up."
            })

        # Double Top
        max1 = sub_df['High'].iloc[0:20].max()
        max2 = sub_df['High'].iloc[-20:].max()
        if abs(max1 - max2) / max1 < 0.03 and current < max2 * 0.95:
             patterns.append({
                "name": "Double Top",
                "status": "Bearish",
                "description": "Rejected twice at major resistance. High supply zone."
            })

        # Cup and Handle
        lowest_60 = sub_df['Low'].min()
        start_60 = df['Close'].iloc[-60]
        if lowest_60 < start_60 * 0.85 and current > lowest_60 * 1.15 and current < start_60:
            patterns.append({
                "name": "Cup and Handle",
                "status": "Breakout Potential",
                "description": "Deep accumulation bowl detected. Consolidation handle forming."
            })

        return patterns

    def _analyze_market_climate(self, spy_df: pd.DataFrame, vix_data: pd.DataFrame = None) -> Dict[str, Any]:
        """
        Analyzes the broader market context using SPY trend and VIX volatility.
        Returns a 'Traffic Light' status: Green (Aggressive), Yellow (Caution), Red (Defense).
        """
        if spy_df is None or spy_df.empty:
            return {"status": "Unknown", "color": "grey", "reason": "Market Data Unavailable"}

        current_price = spy_df['Close'].iloc[-1]
        sma50 = spy_df['Close'].rolling(window=50).mean().iloc[-1]
        sma200 = spy_df['Close'].rolling(window=200).mean().iloc[-1]
        
        # Volatility check
        vix_val = 20 # Default neutral if missing
        if vix_data is not None and not vix_data.empty:
            vix_val = vix_data['Close'].iloc[-1]
            
        # Logic: Traffic Light System
        if current_price > sma50 and vix_val < 20:
            return {
                "status": "Aggressive Growth",
                "color": "green",
                "description": "Market is in a confirmed uptrend with low volatility. Buy breakouts confidentally.",
                "details": f"SPY > SMA50 (${sma50:.2f}) | VIX: {vix_val:.2f}"
            }
        elif current_price < sma200 or vix_val > 25:
            return {
                "status": "Correction / Defense",
                "color": "red",
                "description": "Major trend damage or high fear. Cash is a position. Avoid new longs.",
                "details": f"SPY < SMA200 (${sma200:.2f}) or VIX Spiking ({vix_val:.2f})"
            }
        else:
             return {
                "status": "Caution / choppy",
                "color": "yellow",
                "description": "Mixed signals. Market is indecisive. Reduce position sizing.",
                "details": f"SPY between SMAs or VIX elevated ({vix_val:.2f})"
            }

    def _detect_vpa_patterns(self, df: pd.DataFrame) -> List[Dict[str, str]]:
        """Detects Volume Price Analysis (VPA) anomalies."""
        signals = []
        if len(df) < 20: return []
        
        current = df.iloc[-1]
        prev = df.iloc[-2]
        avg_vol = df['Volume'].tail(20).mean()
        
        # Calculate Spread (End - Low vs High - Low) relative to body size
        spread = current['High'] - current['Low']
        body = abs(current['Close'] - current['Open'])
        
        # 1. Churning (High Effort, No Result)
        # High Volume (> 1.5x avg), Small Spread (Doji-like or small body), at Highs
        if current['Volume'] > avg_vol * 1.5 and spread < (df['High'].tail(10).mean() - df['Low'].tail(10).mean()) * 0.6:
            signals.append({
                "name": "Churning",
                "bias": "Bearish",
                "color": "red",
                "description": "High volume with little price progress. Smart money potential selling."
            })
            
        # 2. Stopping Volume (High Effort to Stop Downmove)
        # Down day, High Volume, Long lower wick (Hammer) or Small Spread after drop
        if current['Close'] < prev['Close'] and current['Volume'] > avg_vol * 1.5:
            # Check for Hammer candle (Lower wick > 2x body)
            lower_wick = min(current['Open'], current['Close']) - current['Low']
            if lower_wick > body * 2:
                signals.append({
                    "name": "Stopping Volume",
                    "bias": "Bullish",
                    "color": "green",
                    "description": "High volume absorption on weakness. Smart money buying the dip."
                })
        
        # 3. No Demand (Up Candle, Low Vol)
        if current['Close'] > prev['Close'] and current['Volume'] < avg_vol * 0.7:
             signals.append({
                "name": "No Demand",
                "bias": "Bearish",
                "color": "orange",
                "description": "Price rising on weak volume. Lack of professional interest."
            })

        return signals

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

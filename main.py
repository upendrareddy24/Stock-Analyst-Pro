import os
import re
from flask import Flask, request, jsonify, send_from_directory
from collaborative_models import db, SharedHistory, BullishRadar, PersonaPick, MarketIntelligence
from analyst_engine import AnalystEngine
from data_orchestrator import DataOrchestrator
import threading
import time

app = Flask(__name__, static_folder='.', static_url_path='')

# Database Configuration
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'instance', 'hub.db')
if not os.path.exists(os.path.join(basedir, 'instance')):
    os.makedirs(os.path.join(basedir, 'instance'))

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f'sqlite:///{db_path}').replace('postgres://', 'postgresql://')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

orchestrator = DataOrchestrator()
engine = AnalystEngine("books_db.json")

# Expanded Universe for Dynamic Discovery
DYNAMIC_MOONSHOT_UNIVERSE = [
    "NNE", "LUNR", "TMC", "QUBT", "PGEN", "ASTS", "VRT", "SMCI", "ARM", 
    "RGTI", "IONQ", "BKSY", "PLTR", "SOUN", "SERV", "MARA", "RIOT", "COIN",
    "MSTR", "RDDT", "PATH", "CELH", "SMR", "OKLO", "LEU", "UUUU", "CCJ",
    "GME", "CHPT", "NIO", "XPEV", "LI", "PLUG", "FCEL", "SPCE", "BLNK"
]

# EXPERT TRADER: Sector Watchlist
SECTOR_MAP = {
    "Next-Gen Moonshots": ["NNE", "LUNR", "TMC", "QUBT", "PGEN"],
    "AI Growth/Compute": ["PLTR", "ASTS", "VRT", "SMCI", "ARM"],
    "Nuclear/Uranium": ["OKLO", "SMR", "LEU", "UUUU", "CCJ"],
    "Cybersecurity": ["PANW", "CRWD", "FTNT", "NET", "ZS"],
    "Defense/Warfare": ["LMT", "RTX", "NOC", "GD", "HWM"],
    "Financials (XLF)": ["JPM", "BAC", "MS", "GS", "WFC"],
    "Healthcare (XLV)": ["LLY", "UNH", "VRTX", "AMGN", "ISRG"],
    "Utilities (XLU)": ["NEE", "DUK", "CEG", "VST", "SRE"],
    "Commodities/Metal": ["GLD", "SLV", "GDX", "FCX", "NEM"],
    "Digital/Crypto": ["IBIT", "MSTR", "COIN", "MARA", "RIOT"],
    "Retail/Global": ["AMZN", "WMT", "COST", "TGT", "MELI"],
    "EV/Battery Tech": ["TSLA", "RIVN", "LCID", "ALB", "QS"],
    "AgriTech/Food": ["DE", "CAT", "CF", "NTR", "ADM"],
    "Semi/Chips": ["NVDA", "AVGO", "MU", "AMD", "TSM"],
    "Software/SaaS": ["MSFT", "CRM", "SAP", "SNOW", "DDOG"]
}

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/analyze', methods=['GET'])
def analyze():
    ticker = request.args.get('ticker', 'AAPL').upper().strip()
    try:
        df = orchestrator.get_stock_data(ticker)
        if df is None or df.empty:
            return jsonify({"error": f"Could not fetch data for {ticker}"}), 400
            
        news = orchestrator.get_ticker_news(ticker)
        options = orchestrator.get_options_intel(ticker)
        benchmark_df = orchestrator.get_stock_data("SPY")
        vix_df = orchestrator.get_stock_data("^VIX")
        
        analysis = engine.analyze_ticker(ticker, df, news, options, benchmark_df)
        analysis['market_climate'] = engine._analyze_market_climate(benchmark_df, vix_df)
        
        # --- SHARED PERSISTENCE ---
        # 1. Update Global History
        new_hist = SharedHistory(ticker=ticker, consensus=analysis['consensus'])
        db.session.add(new_hist)
        
        # 2. Update Bullish Radar
        if "Bullish" in analysis['consensus']:
            existing_radar = BullishRadar.query.filter_by(ticker=ticker).first()
            score_val = analysis.get('master_score', {}).get('value', 0)
            if existing_radar:
                existing_radar.timestamp = db.func.now()
                existing_radar.master_score = score_val
            else:
                db.session.add(BullishRadar(ticker=ticker, consensus=analysis['consensus'], master_score=score_val))
        else:
            BullishRadar.query.filter_by(ticker=ticker).delete()

        # 3. Update Persona Picks
        for persona, result in analysis['personas'].items():
            if "Buy" in result['rating']:
                # Update or add
                existing_pick = PersonaPick.query.filter_by(persona=persona, ticker=ticker).first()
                if existing_pick:
                    existing_pick.timestamp = db.func.now()
                    existing_pick.rating = result['rating']
                else:
                    db.session.add(PersonaPick(persona=persona, ticker=ticker, rating=result['rating']))
            else:
                # Remove if not buy anymore
                PersonaPick.query.filter_by(persona=persona, ticker=ticker).delete()

        db.session.commit()
        
        return jsonify(analysis)
    except Exception as e:
        print(f"Error in analysis: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    history = SharedHistory.query.order_by(SharedHistory.timestamp.desc()).limit(10).all()
    return jsonify([h.to_dict() for h in history])

@app.route('/api/radar', methods=['GET'])
def get_radar():
    # Sort by master_score descending (High potential first), then timestamp
    radar = BullishRadar.query.order_by(BullishRadar.master_score.desc(), BullishRadar.timestamp.desc()).limit(15).all()
    return jsonify([r.to_dict() for r in radar])

@app.route('/api/persona_picks', methods=['GET'])
def get_persona_picks():
    persona = request.args.get('persona')
    if persona:
        picks = PersonaPick.query.filter_by(persona=persona).order_by(PersonaPick.timestamp.desc()).limit(20).all()
    else:
        picks = PersonaPick.query.order_by(PersonaPick.timestamp.desc()).limit(20).all()
    return jsonify([p.to_dict() for p in picks])

@app.route('/api/market_intelligence', methods=['GET'])
def get_market_intelligence():
    leads = MarketIntelligence.query.order_by(MarketIntelligence.master_score.desc()).limit(10).all()
    return jsonify([l.to_dict() for l in leads])

@app.route('/api/sector_scout', methods=['GET'])
def sector_scout():
    """Ranks leaders within each sector using full 'Consulting the Greats' Logic."""
    results = {}
    benchmark_df = orchestrator.get_stock_data("SPY")
    for sector, tickers in SECTOR_MAP.items():
        current_watchlist = DYNAMIC_MOONSHOT_UNIVERSE if sector == "Next-Gen Moonshots" else tickers
        sector_results = []
        for ticker in current_watchlist:
            try:
                df = orchestrator.get_stock_data(ticker)
                if df is not None and not df.empty:
                    # Upgrade: Attempting light news/options fetch for better scoring if time permits
                    # We limit news to 1 item to be fast
                    news = orchestrator.get_ticker_news(ticker) 
                    options = orchestrator.get_options_intel(ticker)
                    
                    analysis = engine.analyze_ticker(ticker, df, news, options, benchmark_df)
                    
                    # Extract top persona rating
                    top_rating = "Neutral"
                    for _, res in analysis.get('personas', {}).items():
                        if "Strong Buy" in res['rating']:
                            top_rating = "Strong Buy"
                            break
                        elif "Buy" in res['rating'] and top_rating != "Strong Buy":
                            top_rating = "Buy"
                            
                    sector_results.append({
                        "ticker": ticker,
                        "score": analysis.get('master_score', {}).get('value', 0),
                        "label": analysis.get('master_score', {}).get('label', 'Neutral'),
                        "price": analysis.get('current_price', 0),
                        "consensus": analysis.get('consensus', 'Neutral'),
                        "top_rating": top_rating
                    })
            except Exception as e:
                print(f"Scout error on {ticker}: {e}")
                continue
        # Sort by score descending and take top 5
        sector_results.sort(key=lambda x: x['score'], reverse=True)
        results[sector] = sector_results[:5]
    return jsonify(results)


# --- AUTONOMOUS SCANNER ENGINE ---
def run_autonomous_scanner():
    """Background thread to proactively find opportunities."""
    # List of high-impact tickers to scan
    watchlist = ['NVDA', 'TSLA', 'AAPL', 'MSFT', 'AMD', 'MSTR', 'COIN', 'GOOGL', 'AMZN', 'META', 'PLTR', 'IWM']
    
    print("Autonomous Intelligence: Engine initialized, waiting 10s for server boot...")
    time.sleep(10) # Safety delay for Gunicorn workers
    
    with app.app_context():
        print("Autonomous Market Intelligence Scanner: LIVE")
        while True:
            for ticker in watchlist:
                try:
                    # Check if recently updated 
                    existing = MarketIntelligence.query.filter_by(ticker=ticker).first()
                    if existing and (time.time() - existing.timestamp.timestamp() < 3600):
                        continue
                        
                    print(f"AI Scanner: Analyzing {ticker}...")
                    df = orchestrator.get_stock_data(ticker)
                    if df is None or df.empty:
                        continue
                        
                    news = orchestrator.get_ticker_news(ticker)
                    options = orchestrator.get_options_intel(ticker)
                    benchmark_df = orchestrator.get_stock_data("SPY")
                    analysis = engine.analyze_ticker(ticker, df, news, options, benchmark_df)
                    
                    if "Bullish" in analysis['consensus'] or "Strong" in analysis['consensus']:
                        score = analysis.get('master_score', {}).get('value', 0)
                        potential = analysis.get('trade_plan', {}).get('target', 'N/A')
                        
                        if existing:
                            existing.consensus = analysis['consensus']
                            existing.master_score = score
                            existing.potential_gain = potential
                            existing.timestamp = db.func.now()
                        else:
                            new_lead = MarketIntelligence(
                                ticker=ticker,
                                consensus=analysis['consensus'],
                                master_score=score,
                                potential_gain=potential
                            )
                            db.session.add(new_lead)
                        db.session.commit()
                        print(f"AI Detected Advantage: {ticker} (Score: {score})")
                    else:
                        if existing:
                            db.session.delete(existing)
                            db.session.commit()
                            
                except Exception as e:
                    if "no such column" in str(e).lower() or "undefined_column" in str(e).lower():
                        print(f"CRITICAL: Database out of sync! Please run: heroku pg:reset DATABASE_URL --confirm {os.environ.get('HEROKU_APP_NAME')}")
                    print(f"Scanner error on {ticker}: {e}")
                
                time.sleep(30)
            time.sleep(600)

# Start Background Scanner if not in testing/shell
if os.environ.get('RUN_SCANNER', 'true').lower() == 'true':
    scanner_thread = threading.Thread(target=run_autonomous_scanner, daemon=True)
    scanner_thread.start()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)

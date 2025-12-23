import os
import re
from flask import Flask, request, jsonify, send_from_directory
from collaborative_models import db, SharedHistory, BullishRadar, PersonaPick, Stock
from analyst_engine import AnalystEngine
from data_orchestrator import DataOrchestrator
from utils import fetch_current_price, process_excel

app = Flask(__name__, static_folder='.', static_url_path='')

# Database Configuration
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'instance', 'hub.db')
if not os.path.exists(os.path.join(basedir, 'instance')):
    os.makedirs(os.path.join(basedir, 'instance'))

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f'sqlite:///{db_path}').replace('postgres://', 'postgresql://')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

db.init_app(app)

with app.app_context():
    db.create_all()

orchestrator = DataOrchestrator()
engine = AnalystEngine("books_db.json")

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
        analysis = engine.analyze_ticker(ticker, df, news)
        
        # --- SHARED PERSISTENCE ---
        # 1. Update Global History
        new_hist = SharedHistory(ticker=ticker, consensus=analysis['consensus'])
        db.session.add(new_hist)
        
        # 2. Update Bullish Radar
        if "Bullish" in analysis['consensus']:
            existing_radar = BullishRadar.query.filter_by(ticker=ticker).first()
            if existing_radar:
                existing_radar.timestamp = db.func.now()
            else:
                db.session.add(BullishRadar(ticker=ticker, consensus=analysis['consensus']))
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
    radar = BullishRadar.query.order_by(BullishRadar.timestamp.desc()).limit(10).all()
    return jsonify([r.to_dict() for r in radar])

@app.route('/api/persona_picks', methods=['GET'])
def get_persona_picks():
    persona = request.args.get('persona')
    if persona:
        picks = PersonaPick.query.filter_by(persona=persona).order_by(PersonaPick.timestamp.desc()).limit(20).all()
    else:
        picks = PersonaPick.query.order_by(PersonaPick.timestamp.desc()).limit(20).all()
    return jsonify([p.to_dict() for p in picks])

# --- STRATEGY TRACKER LOGIC (Unified) ---

@app.route('/api/stocks', methods=['GET'])
def get_stocks():
    stocks = Stock.query.all()
    return jsonify([s.to_dict() for s in stocks])

@app.route('/api/add_stock', methods=['POST'])
def add_stock():
    data = request.json
    ticker = data.get('ticker').upper()
    strategy = data.get('strategy')
    
    price_data = fetch_current_price(ticker)
    if not price_data:
        return jsonify({'error': 'Could not fetch price for ticker'}), 400
        
    new_stock = Stock(
        ticker=ticker,
        strategy=strategy,
        entry_price=price_data['price'],
        current_price=price_data['price'],
        daily_change=price_data['daily_change']
    )
    db.session.add(new_stock)
    db.session.commit()
    return jsonify(new_stock.to_dict())

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    strategy = request.form.get('strategy')
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)
    
    tickers = process_excel(file_path)
    print(f"DEBUG: Extracted {len(tickers)} tickers for Strategy {strategy}")
    
    added_stocks_objects = []
    for ticker in tickers:
        ticker = ticker.upper()
        price_data = fetch_current_price(ticker)
        if price_data:
            new_stock = Stock(
                ticker=ticker,
                strategy=strategy,
                entry_price=price_data['price'],
                current_price=price_data['price'],
                daily_change=price_data['daily_change']
            )
            db.session.add(new_stock)
            added_stocks_objects.append(new_stock)
            
    db.session.commit()
    return jsonify([s.to_dict() for s in added_stocks_objects])

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)

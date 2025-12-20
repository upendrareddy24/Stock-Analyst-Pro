from flask import Flask, request, jsonify, send_from_directory
import pandas as pd
import os
from analyst_engine import AnalystEngine
from data_orchestrator import DataOrchestrator

app = Flask(__name__, static_folder='.', static_url_path='')
orchestrator = DataOrchestrator()
engine = AnalystEngine("books_db.json")

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/analyze', methods=['GET'])
def analyze():
    ticker = request.args.get('ticker', 'AAPL').upper()
    try:
        df = orchestrator.get_stock_data(ticker)
        if df is None or df.empty:
            return jsonify({"error": f"Could not fetch data for {ticker}"}), 400
            
        news = orchestrator.get_ticker_news(ticker)
        analysis = engine.analyze_ticker(ticker, df, news)
        return jsonify(analysis)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)

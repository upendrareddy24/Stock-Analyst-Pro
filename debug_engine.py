import pandas as pd
from analyst_engine import AnalystEngine
import json

engine = AnalystEngine("books_db.json")
df = pd.DataFrame({
    'Close': [100.0] * 300,
    'High': [101.0] * 300,
    'Low': [99.0] * 300,
    'Volume': [1000000] * 300
})
analysis = engine.analyze_ticker("TEST", df)
print(json.dumps(list(analysis.keys())))

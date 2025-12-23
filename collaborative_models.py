from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class SharedHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(20), nullable=False)
    consensus = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'ticker': self.ticker,
            'consensus': self.consensus,
            'date': self.timestamp.strftime('%m/%d/%Y %I:%M %p'),
            'timestamp': self.timestamp.timestamp() * 1000
        }

class BullishRadar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(20), unique=True, nullable=False)
    consensus = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'ticker': self.ticker,
            'consensus': self.consensus,
            'date': self.timestamp.strftime('%m/%d/%Y'),
            'timestamp': self.timestamp.timestamp() * 1000
        }

class PersonaPick(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    persona = db.Column(db.String(50), nullable=False)
    ticker = db.Column(db.String(20), nullable=False)
    rating = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'ticker': self.ticker,
            'rating': self.rating,
            'date': self.timestamp.strftime('%m/%d/%Y'),
            'timestamp': self.timestamp.timestamp() * 1000
        }

class Stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(20), nullable=False)
    strategy = db.Column(db.String(100))
    entry_price = db.Column(db.Float)
    current_price = db.Column(db.Float)
    daily_change = db.Column(db.Float)
    added_date = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'ticker': self.ticker,
            'strategy': self.strategy,
            'entry_price': self.entry_price,
            'current_price': self.current_price,
            'daily_change': self.daily_change,
            'added_date': self.added_date.strftime('%m/%d/%Y') if self.added_date else None
        }

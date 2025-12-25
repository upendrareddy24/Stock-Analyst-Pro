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
    master_score = db.Column(db.Integer, default=0)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'ticker': self.ticker,
            'consensus': self.consensus,
            'master_score': self.master_score,
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


class MarketIntelligence(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(20), unique=True, nullable=False)
    consensus = db.Column(db.String(50), nullable=False)
    master_score = db.Column(db.Integer, default=0)
    potential_gain = db.Column(db.String(20), default="Unknown")
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'ticker': self.ticker,
            'consensus': self.consensus,
            'master_score': self.master_score,
            'potential_gain': self.potential_gain,
            'date': self.timestamp.strftime('%m/%d/%Y %I:%M %p'),
            'timestamp': self.timestamp.timestamp() * 1000
        }

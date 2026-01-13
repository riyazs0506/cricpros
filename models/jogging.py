from datetime import datetime
from models import db

class Jogging(db.Model):
    __tablename__ = "jogging"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, nullable=False)
    role = db.Column(db.String(10))   # player / coach

    distance_km = db.Column(db.Float)
    duration_min = db.Column(db.Integer)
    avg_speed = db.Column(db.Float)   # km/h
    calories = db.Column(db.Float)

    path = db.Column(db.Text)         # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

from datetime import datetime
from models import db

class MatchPayment(db.Model):
    __tablename__ = "match_payments"

    id = db.Column(db.Integer, primary_key=True)

    availability_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, nullable=False)

    amount = db.Column(db.Numeric(10, 2), nullable=False)

    payment_method = db.Column(db.String(20), default="upi")
    payment_status = db.Column(db.String(20), default="pending")

    transaction_id = db.Column(db.String(100), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # ✅ ALIAS so old code using `status` works
    @property
    def status(self):
        return self.payment_status
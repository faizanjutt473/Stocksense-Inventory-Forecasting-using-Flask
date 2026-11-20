from datetime import datetime
from app.extensions import db


class StockMovement(db.Model):
    __tablename__ = "stock_movements"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    movement_type = db.Column(db.String(3), nullable=False)  # "in" ya "out"
    quantity = db.Column(db.Integer, nullable=False)
    note = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    product = db.relationship("Product")

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.created_at.strftime("%Y-%m-%d"),
            "product": self.product.name,
            "type": self.movement_type,
            "quantity": self.quantity,
            "note": self.note,
        }
from datetime import datetime
from app.extensions import db


class PurchaseOrder(db.Model):
    __tablename__ = "purchase_orders"

    id = db.Column(db.Integer, primary_key=True)
    po_number = db.Column(db.String(20), unique=True, nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    status = db.Column(db.String(20), nullable=False, default="Pending")  # Pending / Received
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    received_at = db.Column(db.DateTime, nullable=True)

    supplier = db.relationship("Supplier")
    product = db.relationship("Product")

    def to_dict(self):
        return {
            "id": self.id,
            "po_number": self.po_number,
            "supplier": self.supplier.name,
            "product": self.product.name,
            "quantity": self.quantity,
            "total_amount": float(self.total_amount),
            "status": self.status,
        }
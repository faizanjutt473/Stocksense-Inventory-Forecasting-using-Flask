from datetime import datetime

from flask import request
from flask_restx import Namespace, Resource, fields

from app.extensions import db
from app.models import PurchaseOrder, Product, Supplier, StockMovement

ns = Namespace("purchase-orders", description="Purchase orders")

po_input = ns.model("PurchaseOrderInput", {
    "supplier_id": fields.Integer(required=True, example=1),
    "product_id": fields.Integer(required=True, example=2),
    "quantity": fields.Integer(required=True, min=1, example=50),
})


def _next_po_number():
    last_id = db.session.query(db.func.max(PurchaseOrder.id)).scalar() or 0
    return f"PO-{last_id + 1:04d}"


@ns.route("")
class PurchaseOrderList(Resource):
    @ns.doc(params={"status": "Pending ya Received"})
    def get(self):
        """Saare purchase orders (naye pehle)"""
        query = PurchaseOrder.query
        status = request.args.get("status", "").strip()
        if status:
            query = query.filter(PurchaseOrder.status == status)
        return [o.to_dict() for o in query.order_by(PurchaseOrder.id.desc()).all()]

    @ns.expect(po_input, validate=True)
    def post(self):
        """Naya purchase order banayein"""
        data = ns.payload
        if data["quantity"] < 1:
            return {"message": "Quantity kam az kam 1 honi chahiye"}, 400
        supplier = db.session.get(Supplier, data["supplier_id"])
        product = db.session.get(Product, data["product_id"])
        if not supplier or not product:
            return {"message": "Supplier ya product maujood nahi"}, 404

        order = PurchaseOrder(
            po_number=_next_po_number(),
            supplier_id=supplier.id,
            product_id=product.id,
            quantity=data["quantity"],
            total_amount=data["quantity"] * product.cost_price,
            status="Pending",
        )
        db.session.add(order)
        db.session.commit()
        return order.to_dict(), 201


@ns.route("/<int:order_id>")
class PurchaseOrderItem(Resource):
    def get(self, order_id):
        """Ek purchase order ki detail"""
        return db.get_or_404(PurchaseOrder, order_id).to_dict()


@ns.route("/<int:order_id>/receive")
class PurchaseOrderReceive(Resource):
    def post(self, order_id):
        """Order receive karein: stock barh jata hai aur movement record hota hai"""
        order = db.get_or_404(PurchaseOrder, order_id)
        if order.status == "Received":
            return {"message": "Ye order pehle hi receive ho chuka hai"}, 409

        order.status = "Received"
        order.received_at = datetime.utcnow()
        order.product.stock += order.quantity
        db.session.add(StockMovement(
            product_id=order.product_id,
            movement_type="in",
            quantity=order.quantity,
            note=f"{order.po_number} received",
        ))
        db.session.commit()
        return order.to_dict()
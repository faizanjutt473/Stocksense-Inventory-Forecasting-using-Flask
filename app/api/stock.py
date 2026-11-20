from flask import request
from flask_restx import Namespace, Resource, fields

from app.extensions import db
from app.models import Product, StockMovement

ns = Namespace("stock", description="Stock in / out movements")

movement_input = ns.model("MovementInput", {
    "product_id": fields.Integer(required=True, example=1),
    "movement_type": fields.String(required=True, enum=["in", "out"], example="in"),
    "quantity": fields.Integer(required=True, example=10),
    "note": fields.String(example="Weekly delivery"),
})


@ns.route("/movements")
class MovementList(Resource):
    @ns.doc(params={"limit": "Kitni entries (default 50)", "product_id": "Ek product ki history"})
    def get(self):
        """Stock movement history (naye pehle)"""
        query = StockMovement.query
        product_id = request.args.get("product_id", type=int)
        if product_id:
            query = query.filter(StockMovement.product_id == product_id)
        limit = min(request.args.get("limit", 50, type=int), 500)
        rows = query.order_by(StockMovement.created_at.desc(), StockMovement.id.desc()).limit(limit).all()
        return [m.to_dict() for m in rows]

    @ns.expect(movement_input, validate=True)
    def post(self):
        """Stock In ya Stock Out record karein"""
        data = ns.payload
        mtype = data["movement_type"]
        qty = data["quantity"]

        if mtype not in ("in", "out"):
            return {"message": "movement_type sirf 'in' ya 'out' ho sakta hai"}, 400
        if qty < 1:
            return {"message": "Quantity kam az kam 1 honi chahiye"}, 400

        # Row lock: do log ek hi waqt mein stock kharab na karein
        product = (db.session.query(Product)
                   .filter_by(id=data["product_id"])
                   .with_for_update()
                   .first())
        if not product:
            return {"message": "Product maujood nahi"}, 404

        if mtype == "out" and qty > product.stock:
            return {"message": f"Itna stock maujood nahi (available: {product.stock})"}, 400

        product.stock += qty if mtype == "in" else -qty
        movement = StockMovement(
            product_id=product.id,
            movement_type=mtype,
            quantity=qty,
            note=(data.get("note") or "").strip() or None,
        )
        db.session.add(movement)
        db.session.commit()

        result = movement.to_dict()
        result["new_stock"] = product.stock
        return result, 201
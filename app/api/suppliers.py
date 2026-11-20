from flask import request
from flask_restx import Namespace, Resource, fields

from app.extensions import db
from app.models import Supplier, PurchaseOrder

ns = Namespace("suppliers", description="Suppliers management")

supplier_input = ns.model("SupplierInput", {
    "name": fields.String(required=True, example="Karachi Distributors"),
    "contact_person": fields.String(example="Usman Ali"),
    "phone": fields.String(example="0345-1112223"),
    "lead_time_days": fields.Integer(example=4),
})


def _invalid(data):
    if "name" in data and not data["name"].strip():
        return "Name khali nahi ho sakta"
    if data.get("lead_time_days") is not None and data["lead_time_days"] < 0:
        return "Lead time negative nahi ho sakta"
    return None


@ns.route("")
class SupplierList(Resource):
    def get(self):
        """Saare suppliers"""
        return [s.to_dict() for s in Supplier.query.order_by(Supplier.id).all()]

    @ns.expect(supplier_input, validate=True)
    def post(self):
        """Naya supplier add karein"""
        data = ns.payload
        error = _invalid(data)
        if error:
            return {"message": error}, 400
        supplier = Supplier(
            name=data["name"].strip(),
            contact_person=data.get("contact_person"),
            phone=data.get("phone"),
            lead_time_days=data.get("lead_time_days") if data.get("lead_time_days") is not None else 5,
        )
        db.session.add(supplier)
        db.session.commit()
        return supplier.to_dict(), 201


@ns.route("/<int:supplier_id>")
class SupplierItem(Resource):
    def get(self, supplier_id):
        """Ek supplier ki detail"""
        return db.get_or_404(Supplier, supplier_id).to_dict()

    @ns.expect(supplier_input)
    def put(self, supplier_id):
        """Supplier edit karein"""
        supplier = db.get_or_404(Supplier, supplier_id)
        data = request.get_json() or {}
        error = _invalid(data)
        if error:
            return {"message": error}, 400
        for f in ("name", "contact_person", "phone", "lead_time_days"):
            if f in data and data[f] is not None:
                setattr(supplier, f, data[f])
        db.session.commit()
        return supplier.to_dict()

    def delete(self, supplier_id):
        """Supplier delete karein"""
        supplier = db.get_or_404(Supplier, supplier_id)
        if supplier.products or PurchaseOrder.query.filter_by(supplier_id=supplier_id).first():
            return {"message": "Is supplier ke products ya orders maujood hain, isliye delete nahi ho sakta"}, 409
        db.session.delete(supplier)
        db.session.commit()
        return {"message": "Supplier delete ho gaya"}
from flask import request
from flask_restx import Namespace, Resource, fields
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Product

ns = Namespace("products", description="Products management")

product_input = ns.model("ProductInput", {
    "sku": fields.String(required=True, example="SKU-1009"),
    "name": fields.String(required=True, example="Sugar 1kg"),
    "category": fields.String(example="Grocery"),
    "cost_price": fields.Float(example=120),
    "sale_price": fields.Float(example=150),
    "stock": fields.Integer(example=50),
    "reorder_level": fields.Integer(example=10),
    "supplier_id": fields.Integer(example=1),
})


def _apply(product, data):
    """Request ka data product par lagata hai (sirf wo fields jo bheji gayi hon)."""
    if "sku" in data:
        product.sku = data["sku"].strip()
    if "name" in data:
        product.name = data["name"].strip()
    if "category" in data:
        product.category = (data["category"] or "General").strip()
    for f in ("cost_price", "sale_price", "stock", "reorder_level"):
        if f in data and data[f] is not None:
            setattr(product, f, data[f])
    if "supplier_id" in data:
        product.supplier_id = data["supplier_id"]


def _invalid(data):
    """Galat values check karta hai, error message wapis karta hai."""
    for f in ("cost_price", "sale_price", "stock", "reorder_level"):
        if data.get(f) is not None and data[f] < 0:
            return f"{f} negative nahi ho sakta"
    if "sku" in data and not data["sku"].strip():
        return "SKU khali nahi ho sakta"
    if "name" in data and not data["name"].strip():
        return "Name khali nahi ho sakta"
    return None


@ns.route("")
class ProductList(Resource):
    @ns.doc(params={"q": "SKU ya naam se search", "category": "Category filter"})
    def get(self):
        """Saare products (search aur category filter ke sath)"""
        query = Product.query
        q = request.args.get("q", "").strip()
        category = request.args.get("category", "").strip()
        if q:
            like = f"%{q}%"
            query = query.filter(db.or_(Product.name.ilike(like), Product.sku.ilike(like)))
        if category:
            query = query.filter(Product.category == category)
        return [p.to_dict() for p in query.order_by(Product.id).all()]

    @ns.expect(product_input, validate=True)
    def post(self):
        """Naya product add karein"""
        data = ns.payload
        error = _invalid(data)
        if error:
            return {"message": error}, 400
        if Product.query.filter_by(sku=data["sku"].strip()).first():
            return {"message": "Ye SKU pehle se maujood hai"}, 409
        product = Product()
        _apply(product, data)
        db.session.add(product)
        db.session.commit()
        return product.to_dict(), 201


@ns.route("/categories")
class ProductCategories(Resource):
    def get(self):
        """Saari categories ki list"""
        rows = db.session.query(Product.category).distinct().order_by(Product.category).all()
        return [r[0] for r in rows]


@ns.route("/<int:product_id>")
class ProductItem(Resource):
    def get(self, product_id):
        """Ek product ki detail"""
        return db.get_or_404(Product, product_id).to_dict()

    @ns.expect(product_input)
    def put(self, product_id):
        """Product edit karein"""
        product = db.get_or_404(Product, product_id)
        data = request.get_json() or {}
        error = _invalid(data)
        if error:
            return {"message": error}, 400
        new_sku = data.get("sku", "").strip()
        if new_sku and new_sku != product.sku and Product.query.filter_by(sku=new_sku).first():
            return {"message": "Ye SKU pehle se maujood hai"}, 409
        _apply(product, data)
        db.session.commit()
        return product.to_dict()

    def delete(self, product_id):
        """Product delete karein"""
        product = db.get_or_404(Product, product_id)
        try:
            db.session.delete(product)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return {"message": "Is product ki sales ya orders ki history maujood hai, isliye delete nahi ho sakta"}, 409
        return {"message": "Product delete ho gaya"}
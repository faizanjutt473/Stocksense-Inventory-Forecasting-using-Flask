from io import BytesIO

import barcode
import qrcode
from barcode.writer import ImageWriter
from flask import send_file
from flask_restx import Namespace, Resource

from app.extensions import db
from app.models import Product

ns = Namespace("barcode", description="Barcode / QR lookup aur images")


def _find_by_sku(sku):
    sku = sku.strip()
    return Product.query.filter(db.func.lower(Product.sku) == sku.lower()).first()


@ns.route("/lookup/<string:sku>")
class BarcodeLookup(Resource):
    def get(self, sku):
        """SKU scan karke product ki detail"""
        product = _find_by_sku(sku)
        if not product:
            return {"message": "Product nahi mila. SKU dobara check karein."}, 404
        return product.to_dict()


@ns.route("/<string:sku>.png")
class BarcodeImage(Resource):
    def get(self, sku):
        """Product ka Code128 barcode (PNG image)"""
        product = _find_by_sku(sku)
        if not product:
            return {"message": "Product nahi mila"}, 404
        buf = BytesIO()
        code = barcode.get("code128", product.sku, writer=ImageWriter())
        code.write(buf, options={"module_height": 12, "font_size": 8, "text_distance": 3, "quiet_zone": 4})
        buf.seek(0)
        return send_file(buf, mimetype="image/png")


@ns.route("/<string:sku>/qr.png")
class QrImage(Resource):
    def get(self, sku):
        """Product ka QR code (PNG image)"""
        product = _find_by_sku(sku)
        if not product:
            return {"message": "Product nahi mila"}, 404
        buf = BytesIO()
        qrcode.make(product.sku).save(buf, format="PNG")
        buf.seek(0)
        return send_file(buf, mimetype="image/png")
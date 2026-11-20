from flask import Blueprint, request, jsonify
from flask_login import current_user
from flask_restx import Api

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.before_request
def require_login():
    if request.path == "/api/auth/login":
        return None
    if not current_user.is_authenticated:
        return jsonify(message="Pehle login karein"), 401


api = Api(
    api_bp,
    title="StockSense API",
    version="1.0",
    description="Inventory & Demand Forecasting System - REST API",
    doc="/docs",
)

from .auth import ns as auth_ns  # noqa: E402
from .products import ns as products_ns  # noqa: E402
from .suppliers import ns as suppliers_ns  # noqa: E402
from .purchase_orders import ns as purchase_orders_ns  # noqa: E402
from .stock import ns as stock_ns  # noqa: E402
from .barcode import ns as barcode_ns  # noqa: E402
from .dashboard import ns as dashboard_ns  # noqa: E402
from .reports import ns as reports_ns  # noqa: E402
from .forecast import ns as forecast_ns  # noqa: E402

api.add_namespace(auth_ns, path="/auth")
api.add_namespace(products_ns, path="/products")
api.add_namespace(suppliers_ns, path="/suppliers")
api.add_namespace(purchase_orders_ns, path="/purchase-orders")
api.add_namespace(stock_ns, path="/stock")
api.add_namespace(barcode_ns, path="/barcode")
api.add_namespace(dashboard_ns, path="/dashboard")
api.add_namespace(reports_ns, path="/reports")
api.add_namespace(forecast_ns, path="/forecast")
from flask import request
from flask_restx import Namespace, Resource

from app.services import analytics

ns = Namespace("reports", description="Reports")


def _days(default, maximum=365):
    value = request.args.get("days", default, type=int)
    return max(1, min(value, maximum))


@ns.route("/profit-by-category")
@ns.doc(params={"days": "Kitne din ki sales (default 90)"})
class ProfitByCategory(Resource):
    def get(self):
        """Category ke hisaab se munafa"""
        return analytics.profit_by_category(_days(90))


@ns.route("/fast-moving")
@ns.doc(params={"days": "Kitne din (default 30)", "limit": "Kitne items (default 6)"})
class FastMoving(Resource):
    def get(self):
        """Sab se tezi se bikne wale items"""
        limit = max(1, min(request.args.get("limit", 6, type=int), 50))
        return analytics.fast_moving(_days(30), limit)


@ns.route("/dead-stock")
@ns.doc(params={"days": "Itne din se koi sale nahi (default 60)"})
class DeadStock(Resource):
    def get(self):
        """Dead stock: jis ki kai din se sale nahi hui"""
        return analytics.dead_stock(_days(60))
from flask_restx import Namespace, Resource

from app.services import analytics

ns = Namespace("dashboard", description="Dashboard ka data")


@ns.route("")
class Dashboard(Resource):
    def get(self):
        """Dashboard ke saare cards, alerts aur chart ka data ek hi call mein"""
        return {
            "summary": analytics.summary(),
            "low_stock": analytics.low_stock_items(),
            "stock_by_category": analytics.stock_by_category(),
            "weekly_sales": analytics.weekly_sales(12),
            "recent_activity": analytics.recent_activity(5),
        }
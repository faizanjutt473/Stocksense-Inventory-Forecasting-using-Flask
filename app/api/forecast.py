from celery.result import AsyncResult
from flask import request
from flask_restx import Namespace, Resource

from app.extensions import db
from app.models import Product
from app.services import forecasting
from app.tasks.forecast_tasks import run_forecast

ns = Namespace("forecast", description="Demand forecasting")


def _model_from_request():
    """(model, error_response) wapis karta hai."""
    model = request.args.get("model", "prophet").strip().lower()
    if model == "lstm":
        return None, ({"message": "LSTM abhi available nahi, Prophet ya XGBoost use karein"}, 400)
    if model not in forecasting.MODELS:
        return None, ({"message": "Model sirf 'prophet' ya 'xgboost' ho sakta hai"}, 400)
    return model, None


@ns.route("/models")
class ForecastModels(Resource):
    def get(self):
        """Kaun kaun se models available hain"""
        return {"available": list(forecasting.MODELS), "coming_soon": ["lstm"]}


@ns.route("/<int:product_id>")
@ns.doc(params={"model": "prophet ya xgboost (default: prophet)"})
class ProductForecast(Resource):
    def get(self, product_id):
        """Forecast foran (Flask ruk kar chalata hai, test ke liye)"""
        model, error = _model_from_request()
        if error:
            return error
        product = db.get_or_404(Product, product_id)
        try:
            return forecasting.run(product, model)
        except forecasting.ForecastError as e:
            return {"message": str(e)}, 422


@ns.route("/<int:product_id>/run")
@ns.doc(params={"model": "prophet ya xgboost (default: prophet)"})
class ProductForecastAsync(Resource):
    def post(self, product_id):
        """Forecast background mein shuru karein (task_id wapis milta hai)"""
        model, error = _model_from_request()
        if error:
            return error
        db.get_or_404(Product, product_id)
        try:
            task = run_forecast.delay(product_id, model)
        except Exception:
            return {"message": "Background service (Redis/Celery) chal nahi rahi"}, 503
        return {"task_id": task.id, "status": "pending"}, 202


@ns.route("/tasks/<string:task_id>")
class ForecastTask(Resource):
    def get(self, task_id):
        """Background forecast ka status aur result"""
        try:
            result = AsyncResult(task_id)
            state = result.state
            if state == "SUCCESS":
                data = result.result
                if isinstance(data, dict) and "error" in data:
                    return {"status": "failed", "message": data["error"]}
                return {"status": "done", "result": data}
            if state == "FAILURE":
                return {"status": "failed", "message": "Forecast banate waqt masla aaya"}
            if state == "STARTED":
                return {"status": "running"}
            return {"status": "pending"}
        except Exception:
            return {"message": "Background service (Redis/Celery) chal nahi rahi"}, 503
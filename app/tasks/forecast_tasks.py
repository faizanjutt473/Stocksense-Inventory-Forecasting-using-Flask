from celery import shared_task

from app.extensions import db
from app.models import Product
from app.services import forecasting


@shared_task(ignore_result=False)
def run_forecast(product_id, model_name):
    """Background mein forecast chalata hai."""
    product = db.session.get(Product, product_id)
    if not product:
        return {"error": "Product maujood nahi"}
    try:
        return forecasting.run(product, model_name)
    except forecasting.ForecastError as e:
        return {"error": str(e)}
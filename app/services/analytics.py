from datetime import date, timedelta

from sqlalchemy import func

from app.extensions import db
from app.models import Product, Sale, StockMovement

# Suggested order = reorder_level x 3 minus maujooda stock (frontend wala hi formula)
REORDER_MULTIPLIER = 3


def summary():
    total = Product.query.count()
    low = Product.query.filter(Product.stock <= Product.reorder_level).count()
    out = Product.query.filter(Product.stock == 0).count()
    value = db.session.query(
        func.coalesce(func.sum(Product.stock * Product.cost_price), 0)
    ).scalar()
    return {
        "total_products": total,
        "low_stock_count": low,
        "out_of_stock_count": out,
        "stock_value": float(value),
    }


def low_stock_items():
    rows = (Product.query
            .filter(Product.stock <= Product.reorder_level)
            .order_by(Product.stock.asc(), Product.id.asc())
            .all())
    result = []
    for p in rows:
        item = p.to_dict()
        item["suggested_order"] = max(p.reorder_level * REORDER_MULTIPLIER - p.stock, 0)
        result.append(item)
    return result


def stock_by_category():
    rows = (db.session.query(Product.category, func.sum(Product.stock))
            .group_by(Product.category)
            .order_by(Product.category)
            .all())
    return [{"category": c, "stock": int(s or 0)} for c, s in rows]


def weekly_sales(weeks=12):
    today = date.today()
    start = today - timedelta(days=weeks * 7)
    rows = (db.session.query(Sale.sale_date, func.sum(Sale.quantity))
            .filter(Sale.sale_date > start)
            .group_by(Sale.sale_date)
            .all())
    totals = [0] * weeks
    for day, qty in rows:
        idx = weeks - 1 - ((today - day).days // 7)
        if 0 <= idx < weeks:
            totals[idx] += int(qty)
    return {"labels": [f"W{i + 1}" for i in range(weeks)], "units": totals}


def recent_activity(limit=5):
    rows = (StockMovement.query
            .order_by(StockMovement.created_at.desc(), StockMovement.id.desc())
            .limit(limit)
            .all())
    return [m.to_dict() for m in rows]


def profit_by_category(days=90):
    since = date.today() - timedelta(days=days)
    profit = func.sum((Sale.unit_price - Product.cost_price) * Sale.quantity)
    rows = (db.session.query(Product.category, profit)
            .select_from(Sale)
            .join(Product, Product.id == Sale.product_id)
            .filter(Sale.sale_date > since)
            .group_by(Product.category)
            .order_by(profit.desc())
            .all())
    return [{"category": c, "profit": float(p or 0)} for c, p in rows]


def fast_moving(days=30, limit=6):
    since = date.today() - timedelta(days=days)
    units = func.sum(Sale.quantity)
    rows = (db.session.query(Product.sku, Product.name, units)
            .select_from(Sale)
            .join(Product, Product.id == Sale.product_id)
            .filter(Sale.sale_date > since)
            .group_by(Product.id, Product.sku, Product.name)
            .order_by(units.desc())
            .limit(limit)
            .all())
    return [{"sku": s, "name": n, "units_sold": int(u)} for s, n, u in rows]


def dead_stock(days=60):
    today = date.today()
    last = (db.session.query(Sale.product_id, func.max(Sale.sale_date).label("last_sale"))
            .group_by(Sale.product_id)
            .subquery())
    rows = (db.session.query(Product, last.c.last_sale)
            .outerjoin(last, last.c.product_id == Product.id)
            .filter(Product.stock > 0)
            .all())
    result = []
    for p, last_sale in rows:
        reference = last_sale or p.created_at.date()
        idle = (today - reference).days
        if idle >= days:
            result.append({
                "sku": p.sku,
                "name": p.name,
                "stock": p.stock,
                "tied_up_value": float(p.stock * p.cost_price),
                "days_idle": idle,
            })
    result.sort(key=lambda r: r["tied_up_value"], reverse=True)
    return result
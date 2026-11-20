import random
import sys
from datetime import date, datetime, timedelta

from app import create_app
from app.extensions import db
from app.models import Supplier, Product, PurchaseOrder, StockMovement, Sale

random.seed(42)


def reset_all():
    for model in (Sale, StockMovement, PurchaseOrder, Product, Supplier):
        model.query.delete()
    db.session.commit()
    print("Purana data delete ho gaya.")


def seed():
    if Supplier.query.first():
        print("Data pehle se maujood hai. Dobara daalne ke liye: python seed.py --reset")
        return

    # ---------- Suppliers ----------
    s1 = Supplier(name="Al-Noor Traders", contact_person="Ahmed Khan", phone="0300-1234567", lead_time_days=3)
    s2 = Supplier(name="Punjab Wholesale", contact_person="Bilal Ahmad", phone="0321-7654321", lead_time_days=5)
    s3 = Supplier(name="TechZone Imports", contact_person="Sara Malik", phone="0333-1112233", lead_time_days=7)
    db.session.add_all([s1, s2, s3])
    db.session.flush()

    # ---------- Products ----------
    # (sku, name, category, cost, price, stock, reorder_level, supplier, 12 hafte mein bikri, dead_stock)
    rows = [
        ("SKU-1001", "Basmati Rice 5kg",     "Grocery",       1500, 1850, 120, 40, s1, 310, False),
        ("SKU-1002", "Cooking Oil 3L",       "Grocery",       1900, 2250,  18, 30, s1, 280, False),
        ("SKU-1003", "Detergent Powder 1kg", "Household",      420,  560,   6, 25, s2, 240, False),
        ("SKU-1004", "LED Bulb 12W",         "Electronics",    260,  390,   0, 20, s3, 150, False),
        ("SKU-1005", "USB Cable Type-C",     "Electronics",    180,  350,  75, 20, s3,  12, True),
        ("SKU-1006", "Shampoo 400ml",        "Personal Care",  540,  690,  44, 20, s2, 190, False),
        ("SKU-1007", "Notebook A4 (Pack)",   "Stationery",     320,  450,  90, 25, s2,  20, True),
        ("SKU-1008", "Green Tea 100 bags",   "Grocery",        480,  640,  12, 20, s1, 170, False),
    ]
    products = []
    for sku, name, cat, cost, price, stock, rl, sup, sold, dead in rows:
        p = Product(sku=sku, name=name, category=cat, cost_price=cost, sale_price=price,
                    stock=stock, reorder_level=rl, supplier_id=sup.id)
        db.session.add(p)
        products.append((p, sold, dead))
    db.session.flush()

    # ---------- Sales (pichle 90 din) ----------
    today = date.today()
    for p, sold, dead in products:
        avg_daily = sold / 84  # 12 hafte
        for offset in range(1, 91):
            day = today - timedelta(days=offset)
            if dead:
                # Dead stock: sirf 60 din se purani sales
                if offset <= 60 and offset >= 90:
                    continue
                if offset < 61:
                    continue
                avg = 0.6
            else:
                trend = 1 + (90 - offset) / 90 * 0.25   # halki barhti hui demand
                weekend = 1.3 if day.weekday() in (4, 5) else 1.0
                avg = avg_daily * trend * weekend
            qty = max(0, round(random.gauss(avg, avg * 0.4)))
            if qty > 0:
                db.session.add(Sale(product_id=p.id, quantity=qty,
                                    unit_price=p.sale_price, sale_date=day))

    # ---------- Purchase Orders ----------
    oil = next(p for p, _, _ in products if p.sku == "SKU-1002")
    led = next(p for p, _, _ in products if p.sku == "SKU-1004")
    db.session.add_all([
        PurchaseOrder(po_number="PO-0001", supplier_id=s1.id, product_id=oil.id,
                      quantity=60, total_amount=60 * 1900, status="Pending"),
        PurchaseOrder(po_number="PO-0002", supplier_id=s3.id, product_id=led.id,
                      quantity=100, total_amount=100 * 260, status="Received",
                      received_at=datetime.utcnow() - timedelta(days=2)),
    ])

    # ---------- Stock Movements ----------
    rice = next(p for p, _, _ in products if p.sku == "SKU-1001")
    shampoo = next(p for p, _, _ in products if p.sku == "SKU-1006")
    det = next(p for p, _, _ in products if p.sku == "SKU-1003")
    db.session.add_all([
        StockMovement(product_id=rice.id, movement_type="in", quantity=50, note="Weekly delivery",
                      created_at=datetime.utcnow() - timedelta(days=2)),
        StockMovement(product_id=shampoo.id, movement_type="out", quantity=8, note="Counter sale",
                      created_at=datetime.utcnow() - timedelta(days=2)),
        StockMovement(product_id=det.id, movement_type="out", quantity=14, note="Counter sale",
                      created_at=datetime.utcnow() - timedelta(days=3)),
    ])

    db.session.commit()
    print("Demo data add ho gaya.")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        if "--reset" in sys.argv:
            reset_all()
        seed()
        print("Suppliers:", Supplier.query.count())
        print("Products:", Product.query.count())
        print("Sales records:", Sale.query.count())
        print("Purchase orders:", PurchaseOrder.query.count())
        print("Stock movements:", StockMovement.query.count())
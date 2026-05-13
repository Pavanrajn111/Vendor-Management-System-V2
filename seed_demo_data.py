"""
One-time / idempotent demo seed for vendor.db.
Only INSERTs — never DELETE or DROP. Skips entirely if marker user exists.

Run from project root:
    python seed_demo_data.py
"""
from __future__ import annotations

import base64
import os
import sqlite3
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor.db")
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "uploads")
MARKER_USER = "TechNova Electronics"

# Minimal 1x1 PNG (transparent) — valid image for static/uploads
_TINY_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


def _ensure_placeholder() -> str:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    path = os.path.join(UPLOAD_DIR, "seed_placeholder.png")
    if not os.path.isfile(path):
        with open(path, "wb") as f:
            f.write(_TINY_PNG)
    return "uploads/seed_placeholder.png"


def _dt(offset_days: int = 0, hour: int = 14, minute: int = 30) -> str:
    d = datetime.now() - timedelta(days=offset_days)
    d = d.replace(hour=hour, minute=minute, second=0, microsecond=0)
    return d.strftime("%d/%m/%Y, %I:%M %p")


def _iso(offset_days: int = 0, hour: int = 11, minute: int = 0) -> str:
    d = datetime.now() - timedelta(days=offset_days)
    d = d.replace(hour=hour, minute=minute, second=0, microsecond=0)
    return d.strftime("%Y-%m-%d %H:%M:%S")


def main() -> None:
    img = _ensure_placeholder()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    if conn.execute("SELECT 1 FROM users WHERE username=?", (MARKER_USER,)).fetchone():
        print("Demo seed already present (marker user exists). No changes made.")
        conn.close()
        return

    DEMO_PASSWORD = "pass123"

    vendors_spec = [
        (MARKER_USER, "TechNova Electronics", "9876543210", "technova.electronics@example.in", "9876543210@okaxis"),
        ("Urban Fashion Hub", "Urban Fashion Hub", "9876543211", "urbanfashion@example.in", "urbanfashion@okhdfcbank"),
        ("FreshMart Groceries", "FreshMart Groceries", "9876543212", "freshmart@example.in", "freshmart@okicici"),
        ("HomeStyle Living", "HomeStyle Living", "9876543213", "homestyle@example.in", "homestyle@okaxis"),
        ("Prime Accessories", "Prime Accessories", "9876543214", "primeacc@example.in", "primeacc@okybl"),
        ("SportX Arena", "SportX Arena", "9876543215", "sportx@example.in", "sportx@okaxis"),
        ("Elite Furniture", "Elite Furniture", "9876543216", "elitefurniture@example.in", "elitefurniture@okhdfcbank"),
        ("Mobile Planet", "Mobile Planet", "9876543217", "mobileplanet@example.in", "mobileplanet@okicici"),
        ("Urban Glow Beauty", "Urban Glow Beauty", "9876543218", "urbanglow@example.in", "urbanglow@okaxis"),
        ("The Reading Room", "The Reading Room", "9876543219", "readingroom@example.in", "readingroom@okaxis"),
        ("ChefPro Kitchenware", "ChefPro Kitchenware", "9876543220", "chefpro@example.in", "chefpro@okybl"),
        ("Scholar Stationery Co", "Scholar Stationery Co", "9876543221", "scholarstationery@example.in", "scholar@okaxis"),
    ]

    customers_spec = [
        ("Rahul Sharma", "9123456701"),
        ("Priya Verma", "9123456702"),
        ("Rohit Mehta", "9123456703"),
        ("Neha Joshi", "9123456704"),
        ("Vikram Singh", "9123456705"),
        ("Ananya Rao", "9123456706"),
        ("Kiran Kumar", "9123456707"),
        ("Sneha Kapoor", "9123456708"),
        ("Arjun Reddy", "9123456709"),
        ("Pooja Nair", "9123456710"),
    ]

    # (vendor_username, product_title_with_hint, price_inr, availability)
    products_spec: list[tuple[str, str, str, str]] = [
        (MARKER_USER, "Noise-cancelling Bluetooth Headphones — 40h battery", "3299", "In Stock"),
        (MARKER_USER, "AMOLED Smartwatch — SpO2 & heart rate", "4499", "In Stock"),
        ("Urban Fashion Hub", "Cotton Hoodie — unisex, winter fleece", "1299", "In Stock"),
        ("Urban Fashion Hub", "Running Sneakers — breathable mesh", "2499", "Out Of Stock"),
        ("FreshMart Groceries", "Basmati Rice 5kg — long grain", "799", "In Stock"),
        ("FreshMart Groceries", "Cold-pressed Mustard Oil 1L", "289", "In Stock"),
        ("HomeStyle Living", "Mixer Grinder 750W — 3 jars", "4299", "In Stock"),
        ("HomeStyle Living", "Induction Cooktop 2000W", "2199", "In Stock"),
        ("Prime Accessories", "Leather Laptop Sleeve 15.6 inch", "899", "In Stock"),
        ("Prime Accessories", "USB-C Hub — 7-in-1 HDMI & card reader", "1599", "In Stock"),
        ("SportX Arena", "Cricket Leather Ball — season grade", "649", "In Stock"),
        ("SportX Arena", "Yoga Mat 6mm — anti-slip TPE", "999", "In Stock"),
        ("Elite Furniture", "Study Table — engineered wood, walnut", "8999", "In Stock"),
        ("Elite Furniture", "Ergonomic Office Chair — mesh back", "12499", "In Stock"),
        ("Mobile Planet", "Fast Charger 25W USB-C brick", "799", "In Stock"),
        ("Mobile Planet", "Tempered Glass — universal 6.5 inch", "299", "In Stock"),
        ("Urban Glow Beauty", "Vitamin C Face Serum 30ml", "599", "In Stock"),
        ("Urban Glow Beauty", "SPF50 Sunscreen Gel 50g", "449", "In Stock"),
        ("The Reading Room", "Indian Polity — McGraw Hill latest", "699", "In Stock"),
        ("The Reading Room", "Data Structures in Python — beginner friendly", "549", "In Stock"),
        ("ChefPro Kitchenware", "Non-stick Kadai 24cm with lid", "1199", "In Stock"),
        ("ChefPro Kitchenware", "Stainless Steel Casserole set 3pc", "1899", "In Stock"),
        ("Scholar Stationery Co", "Premium Gel Pen set — 12 colours", "349", "In Stock"),
        ("Scholar Stationery Co", "A4 Spiral Notebook — 200 pages", "199", "In Stock"),
    ]

    cur = conn.cursor()

    for uname, _biz, mobile, _email, vpa in vendors_spec:
        cur.execute(
            "INSERT INTO users(username,password,role,mobile,upi_vpa) VALUES(?,?,?,?,?)",
            (uname, DEMO_PASSWORD, "vendor", mobile, vpa),
        )

    for uname, mobile in customers_spec:
        cur.execute(
            "INSERT INTO users(username,password,role,mobile,upi_vpa) VALUES(?,?,?,?,?)",
            (uname, DEMO_PASSWORD, "customer", mobile, ""),
        )

    product_rows: list[dict] = []
    for vendor, name, price, avail in products_spec:
        cur.execute(
            "INSERT INTO products(vendor,name,price,image,availability) VALUES(?,?,?,?,?)",
            (vendor, name, price, img, avail),
        )
        row = cur.execute("SELECT * FROM products WHERE id=?", (cur.lastrowid,)).fetchone()
        product_rows.append(dict(row))

    all_vendor_usernames = [v[0] for v in vendors_spec]
    existing_vendors = [
        r[0]
        for r in cur.execute(
            "SELECT username FROM users WHERE role='vendor' AND username NOT IN (%s)"
            % (",".join("?" * len(all_vendor_usernames))),
            all_vendor_usernames,
        ).fetchall()
    ]
    every_vendor = existing_vendors + all_vendor_usernames

    customer_names = [c[0] for c in customers_spec] + ["Pavan", "c1"]

    def connect(cust: str, vend: str) -> None:
        if cur.execute(
            "SELECT 1 FROM connections WHERE customer=? AND vendor=?", (cust, vend)
        ).fetchone():
            return
        cur.execute("INSERT INTO connections(customer,vendor) VALUES(?,?)", (cust, vend))

    # Rich connection graph
    for i, cust in enumerate(customer_names):
        for j, vend in enumerate(every_vendor):
            if (i + j) % 2 == 0 or (i * 3 + j) % 5 == 0:
                connect(cust, vend)

    def pid_for(vendor: str, fragment: str) -> dict:
        for p in product_rows:
            if p["vendor"] == vendor and fragment.lower() in p["name"].lower():
                return p
        raise KeyError((vendor, fragment))

    # Orders: (customer, vendor_key, product_fragment, status, exp_del, del_date, payment_spec or None)
    # payment_spec: (status, method, platform, flow, last4, masked) or None
    order_plan: list[tuple] = []

    def add_o(c, v, frag, st, exp, dd, pay):
        order_plan.append((c, v, frag, st, exp, dd, pay))

    # --- New vendor / new customer heavy mix ---
    add_o("Rahul Sharma", MARKER_USER, "Headphones", "Delivered", "05/04/2026", "08/04/2026", ("Accepted", "upi", "Google Pay", "QR", "", "rahul****@okaxis"))
    add_o("Priya Verma", MARKER_USER, "Smartwatch", "Out For Delivery", "12/05/2026", "", ("Accepted", "card", "", "", "4829", ""))
    add_o("Rohit Mehta", "Urban Fashion Hub", "Hoodie", "Shipped", "15/05/2026", "", ("Pending Vendor Verification", "upi", "PhonePe", "upi-id", "", "rohit****@ybl"))
    add_o("Neha Joshi", "Urban Fashion Hub", "Sneakers", "Pending", "", "", None)
    add_o("Vikram Singh", "FreshMart Groceries", "Basmati", "Processing", "18/05/2026", "", ("Accepted", "card", "", "", "6012", ""))
    add_o("Ananya Rao", "FreshMart Groceries", "Mustard", "Delivered", "01/03/2026", "03/03/2026", ("Completed", "upi", "Paytm", "QR", "", "ananya****@paytm"))
    add_o("Kiran Kumar", "HomeStyle Living", "Mixer", "Accepted", "", "", None)
    add_o("Sneha Kapoor", "HomeStyle Living", "Induction", "Delivered", "20/01/2026", "22/01/2026", ("Accepted", "card", "", "", "9081", ""))
    add_o("Arjun Reddy", "SportX Arena", "Cricket", "Processing", "20/05/2026", "", ("Pending Vendor Verification", "upi", "Google Pay", "QR", "", "arjun****@okaxis"))
    add_o("Pooja Nair", "SportX Arena", "Yoga", "Shipped", "10/05/2026", "", ("Accepted", "upi", "PhonePe", "QR", "", "pooja****@okhdfcbank"))
    add_o("Pavan", "Mobile Planet", "Charger", "Delivered", "28/02/2026", "02/03/2026", ("Accepted", "upi", "Google Pay", "upi-id", "", "pavan****@okaxis"))
    add_o("c1", "Mobile Planet", "Tempered", "Accepted", "", "", ("Pending Vendor Verification", "card", "", "", "3344", ""))
    add_o("Rahul Sharma", "Elite Furniture", "Study Table", "Out For Delivery", "11/05/2026", "", ("Accepted", "card", "", "", "1122", ""))
    add_o("Priya Verma", "Elite Furniture", "Office Chair", "Pending", "", "", None)
    add_o("Rohit Mehta", "Urban Glow Beauty", "Serum", "Delivered", "15/12/2025", "18/12/2025", ("Accepted", "upi", "PhonePe", "QR", "", "rohit****@ybl"))
    add_o("Neha Joshi", "Urban Glow Beauty", "Sunscreen", "Shipped", "08/05/2026", "", ("Accepted", "card", "", "", "7766", ""))
    add_o("Vikram Singh", "The Reading Room", "Polity", "Delivered", "10/11/2025", "12/11/2025", ("Completed", "upi", "Google Pay", "QR", "", "vikram****@okaxis"))
    add_o("Ananya Rao", "The Reading Room", "Python", "Processing", "25/05/2026", "", ("Pending Vendor Verification", "card", "", "", "5544", ""))
    add_o("Kiran Kumar", "ChefPro Kitchenware", "Kadai", "Accepted", "", "", None)
    add_o("Sneha Kapoor", "ChefPro Kitchenware", "Casserole", "Delivered", "02/04/2026", "05/04/2026", ("Accepted", "upi", "Paytm", "upi-id", "", "sneha****@paytm"))
    add_o("Arjun Reddy", "Scholar Stationery Co", "Gel Pen", "Shipped", "09/05/2026", "", ("Accepted", "card", "", "", "9900", ""))
    add_o("Pooja Nair", "Scholar Stationery Co", "Notebook", "Pending", "", "", None)
    add_o("Rahul Sharma", "Prime Accessories", "Sleeve", "Out For Delivery", "13/05/2026", "", ("Accepted", "upi", "PhonePe", "QR", "", "rahul****@ybl"))
    add_o("Priya Verma", "Prime Accessories", "USB-C Hub", "Delivered", "22/03/2026", "25/03/2026", ("Accepted", "card", "", "", "2211", ""))
    # Existing catalogue orders
    add_o("Rohit Mehta", "UrbanKart Supplies", "Smart Watch", "Delivered", "01/02/2026", "04/02/2026", ("Accepted", "upi", "Google Pay", "QR", "", "rohit****@okaxis"))
    add_o("Neha Joshi", "GreenLeaf Organics", "Organic Rice", "Shipped", "14/05/2026", "", ("Pending Vendor Verification", "card", "", "", "6677", ""))
    add_o("Vikram Singh", "TechNova Solutions", "Mouse", "Processing", "16/05/2026", "", ("Accepted", "upi", "PhonePe", "QR", "", "vikram****@okhdfcbank"))
    add_o("Ananya Rao", "BookNest Store", "Novels", "Delivered", "05/01/2026", "07/01/2026", ("Completed", "card", "", "", "4433", ""))
    add_o("Kiran Kumar", "AutoZone Parts", "Engine oil", "Accepted", "", "", None)

    order_ids: list[int] = []
    pay_specs: list[tuple[int, tuple | None]] = []

    day_counter = 3
    for cust, vend, frag, st, exp, dd, pay in order_plan:
        pr = None
        if vend in all_vendor_usernames:
            pr = pid_for(vend, frag.split()[0] if frag else frag)
        else:
            cur2 = conn.execute(
                "SELECT * FROM products WHERE vendor=? AND name LIKE ? LIMIT 1",
                (vend, f"%{frag}%"),
            ).fetchone()
            if not cur2:
                continue
            pr = dict(cur2)

        pay_date = _dt(offset_days=day_counter, hour=10 + (len(order_ids) % 8), minute=(len(order_ids) * 7) % 60)
        day_counter += 1

        cur.execute(
            """INSERT INTO orders(customer,vendor,product_name,price,status,product_image,expected_delivery,delivered_date)
               VALUES(?,?,?,?,?,?,?,?)""",
            (cust, vend, pr["name"], pr["price"], st, pr["image"] or img, exp, dd),
        )
        oid = cur.lastrowid
        order_ids.append(oid)
        pay_specs.append((oid, pay, pr, cust, vend, pay_date))

    for oid, pay, pr, cust, vend, pay_date in pay_specs:
        if not pay:
            continue
        pst, pm, plat, flow, last4, masked = pay
        pm_code = "card" if pm == "card" else "upi"
        cur.execute(
            """INSERT INTO payments(order_id,customer,vendor,product_name,amount,status,payment_date,
               payment_method,upi_platform,upi_flow,card_last4,upi_masked)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                oid,
                cust,
                vend,
                pr["name"],
                pr["price"],
                pst,
                pay_date,
                pm_code,
                plat,
                flow,
                last4,
                masked,
            ),
        )

    review_templates = [
        ("5", "Fast delivery and good packaging. Very happy!"),
        ("5", "Product quality was excellent — matches description."),
        ("4", "Vendor support was very responsive. Minor delay only."),
        ("5", "Great value for money. Will order again."),
        ("4", "Authentic products. Recommended for college projects demo :)"),
        ("3", "Okay experience; product fine but delivery took a bit longer."),
        ("5", "Smooth checkout and clear communication throughout."),
        ("4", "Nice packaging and bill details. Appreciate the professionalism."),
        ("5", "Loved the quality! Exceeded expectations."),
        ("4", "Good seller — item arrived in perfect condition."),
    ]

    rid = 0
    for vend in every_vendor:
        n_rev = 3 if vend in existing_vendors else 2
        for k in range(n_rev):
            cust = customer_names[(rid + k * 2) % len(customer_names)]
            rt, comment = review_templates[(rid + k) % len(review_templates)]
            created = _iso(offset_days=10 + rid + k * 4, hour=9 + k, minute=15 * k)
            cur.execute(
                "INSERT INTO reviews(vendor,rating,comment,customer,created_at) VALUES(?,?,?,?,?)",
                (vend, rt, comment, cust, created),
            )
        rid += 1

    conn.commit()
    conn.close()

    print("Demo seed completed successfully.")
    print("Added: 12 vendors, 10 customers, 24 products, connections, orders, payments, reviews.")
    print("\n--- Vendor accounts (password: pass123) ---")
    for u, biz, *_ in vendors_spec:
        print(f"  {u} / {DEMO_PASSWORD}  ({biz})")
    print("\n--- Customer accounts (password: pass123) ---")
    for u, _ in customers_spec:
        print(f"  {u} / {DEMO_PASSWORD}")
    print("\nExisting accounts (unchanged): c1, Pavan, UrbanKart Supplies, etc.")


if __name__ == "__main__":
    main()

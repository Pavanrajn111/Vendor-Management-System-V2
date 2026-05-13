"""
One-time migration: rename seeded demo_* usernames to professional display names.
Updates users + all string references (products, orders, payments, reviews, connections).
Safe: UPDATE only, no DELETE. Idempotent: skips rows already using new names.

Run: python rename_demo_accounts.py
"""
from __future__ import annotations

import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor.db")

# Old username -> New username (must stay unique vs existing accounts)
VENDOR_RENAMES: dict[str, str] = {
    "demo_electronics_nexus": "TechNova Electronics",
    "demo_fashion_aura": "Urban Fashion Hub",
    "demo_grocery_freshkart": "FreshMart Groceries",
    "demo_home_appliances_plus": "HomeStyle Living",
    "demo_accessories_corner": "Prime Accessories",
    "demo_sports_edge": "SportX Arena",
    "demo_furniture_craft": "Elite Furniture",
    "demo_mobile_gadgets": "Mobile Planet",
    "demo_beauty_glow": "Urban Glow Beauty",
    "demo_books_pages": "The Reading Room",
    "demo_kitchenware_kwik": "ChefPro Kitchenware",
    "demo_stationery_blueprint": "Scholar Stationery Co",
}

CUSTOMER_RENAMES: dict[str, str] = {
    "demo_customer_rahul": "Rahul Sharma",
    "demo_customer_priya": "Priya Verma",
    "demo_customer_amit": "Rohit Mehta",
    "demo_customer_neha": "Neha Joshi",
    "demo_customer_vikram": "Vikram Singh",
    "demo_customer_ananya": "Ananya Rao",
    "demo_customer_kiran": "Kiran Kumar",
    "demo_customer_sneha": "Sneha Kapoor",
    "demo_customer_arjun": "Arjun Reddy",
    "demo_customer_divya": "Pooja Nair",
}


def _rename_user_refs(conn: sqlite3.Connection, old: str, new: str) -> None:
    conn.execute("UPDATE users SET username=? WHERE username=?", (new, old))
    conn.execute("UPDATE products SET vendor=? WHERE vendor=?", (new, old))
    conn.execute("UPDATE orders SET customer=? WHERE customer=?", (new, old))
    conn.execute("UPDATE orders SET vendor=? WHERE vendor=?", (new, old))
    conn.execute("UPDATE payments SET customer=? WHERE customer=?", (new, old))
    conn.execute("UPDATE payments SET vendor=? WHERE vendor=?", (new, old))
    conn.execute("UPDATE reviews SET customer=? WHERE customer=?", (new, old))
    conn.execute("UPDATE reviews SET vendor=? WHERE vendor=?", (new, old))
    conn.execute("UPDATE connections SET customer=? WHERE customer=?", (new, old))
    conn.execute("UPDATE connections SET vendor=? WHERE vendor=?", (new, old))


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    pending_v = [(o, n) for o, n in VENDOR_RENAMES.items() if conn.execute("SELECT 1 FROM users WHERE username=?", (o,)).fetchone()]
    pending_c = [(o, n) for o, n in CUSTOMER_RENAMES.items() if conn.execute("SELECT 1 FROM users WHERE username=?", (o,)).fetchone()]

    try:
        if pending_v or pending_c:
            for old, new in pending_v + pending_c:
                if conn.execute("SELECT 1 FROM users WHERE username=?", (new,)).fetchone() and conn.execute(
                    "SELECT 1 FROM users WHERE username=?", (old,)
                ).fetchone():
                    raise SystemExit(
                        f"Refusing rename {old!r} -> {new!r}: target username is already used by another account."
                    )
            for old, new in pending_v + pending_c:
                _rename_user_refs(conn, old, new)
            print(f"Renamed {len(pending_v)} vendor account(s) and {len(pending_c)} customer account(s).")
        else:
            print("No demo_* accounts to rename (already migrated).")

        # Intermediate seed name -> presentation name (idempotent)
        for old, new in (("Trendy Wear", "Urban Fashion Hub"),):
            if conn.execute("SELECT 1 FROM users WHERE username=?", (old,)).fetchone():
                if not conn.execute("SELECT 1 FROM users WHERE username=?", (new,)).fetchone():
                    _rename_user_refs(conn, old, new)
                    print(f"Refined vendor username {old!r} -> {new!r}.")

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()

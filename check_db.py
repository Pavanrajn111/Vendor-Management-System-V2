import sqlite3
import json

conn = sqlite3.connect('vendor.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row[0] for row in cursor.fetchall()]

print("=== TABLES ===")
for table in tables:
    print(f"\n{table}:")
    cursor.execute(f"PRAGMA table_info({table});")
    for row in cursor.fetchall():
        print(f"  {row[1]} ({row[2]})")

# Get product count
cursor.execute("SELECT COUNT(*) as count FROM products;")
print(f"\n\nTotal Products: {cursor.fetchone()['count']}")

# Get product details
cursor.execute("""
    SELECT id, name, price, image, availability, vendor
    FROM products 
    ORDER BY id
    LIMIT 15
""")
print("\n=== First 15 Products ===")
for row in cursor.fetchall():
    print(f"ID: {row['id']}, Name: {row['name']}, Price: {row['price']}, Image: {row['image']}, Availability: {row['availability']}, Vendor: {row['vendor']}")

# Get vendor count
cursor.execute("SELECT COUNT(*) as count FROM vendors;")
print(f"\n\nTotal Vendors: {cursor.fetchone()['count']}")

# Get vendors
cursor.execute("SELECT id, name, contact FROM vendors")
print("\n=== All Vendors ===")
for row in cursor.fetchall():
    print(f"ID: {row['id']}, Name: {row['name']}, Contact: {row['contact']}")

conn.close()

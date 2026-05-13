import sqlite3

conn = sqlite3.connect('vendor.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Get all products
cursor.execute("""
    SELECT id, name, price, image, availability, vendor
    FROM products 
    ORDER BY vendor, id
""")

print("=== ALL PRODUCTS BY VENDOR ===\n")
current_vendor = None
for row in cursor.fetchall():
    if row['vendor'] != current_vendor:
        current_vendor = row['vendor']
        print(f"\n{current_vendor}:")
    print(f"  ID {row['id']}: {row['name']} | Price: {row['price']} | Image: {row['image']} | Stock: {row['availability']}")

print("\n\n=== IMAGE PATHS CHECK ===")
cursor.execute("SELECT COUNT(*) as count FROM products WHERE image IS NULL OR image = ''")
missing_count = cursor.fetchone()['count']
print(f"Products with missing/empty image: {missing_count}")

conn.close()

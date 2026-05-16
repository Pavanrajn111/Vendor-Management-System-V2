import sqlite3
import re

conn = sqlite3.connect('vendor.db')
cursor = conn.cursor()

print("=" * 70)
print("CLEANING DATABASE - REMOVING ₹ SYMBOLS FROM PRICES")
print("=" * 70)

# Get all products with rupee symbol
cursor.execute("SELECT id, price FROM products WHERE price LIKE '%₹%'")
rows = cursor.fetchall()

print(f"\nFound {len(rows)} products with ₹ symbol in price field")
print("\nCleaning prices...")

cleaned_count = 0
for product_id, price_str in rows:
    # Remove all non-numeric characters except decimal point
    cleaned_price = re.sub(r'[^\d.]', '', str(price_str))
    
    # If price is empty after cleaning, set to 0
    if not cleaned_price:
        cleaned_price = '0'
    
    # Update the database
    cursor.execute("UPDATE products SET price = ? WHERE id = ?", (cleaned_price, product_id))
    cleaned_count += 1
    print(f"  ID {product_id}: '{price_str}' → '{cleaned_price}'")

conn.commit()

print(f"\n✓ Successfully cleaned {cleaned_count} product prices")

# Verify the fix
cursor.execute("SELECT COUNT(*) FROM products WHERE price LIKE '%₹%'")
remaining = cursor.fetchone()[0]
print(f"✓ Remaining prices with ₹ symbol: {remaining}")

# Show sample of cleaned prices
cursor.execute("SELECT id, price FROM products LIMIT 10")
print(f"\nSample of cleaned prices:")
for product_id, price in cursor.fetchall():
    print(f"  ID {product_id}: {repr(price)}")

conn.close()
print("\n" + "=" * 70)
print("DATABASE CLEANUP COMPLETE")
print("=" * 70)

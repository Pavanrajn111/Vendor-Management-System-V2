import sqlite3

conn = sqlite3.connect('vendor.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM products')
count = cursor.fetchone()[0]
cursor.execute("SELECT id, name, price FROM products LIMIT 20")
rows = cursor.fetchall()
print(f'Total products: {count}')
print(f'\nFirst 20 product prices:')
for i, row in enumerate(rows, 1):
    product_id, product_name, price_val = row
    has_rupee = '₹' in str(price_val)
    print(f'  {i}. {product_name:30} = {repr(price_val):15} {"[HAS RUPEE]" if has_rupee else ""}')

print(f'\nTotal with rupee symbol in price: {count}')  # Will update after checking all

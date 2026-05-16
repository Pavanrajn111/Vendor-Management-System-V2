import sqlite3

conn = sqlite3.connect('vendor.db')
cursor = conn.cursor()

# Check all prices to see if any contain rupee symbol
cursor.execute("SELECT COUNT(*) FROM products")
total = cursor.fetchone()[0]

cursor.execute("SELECT price FROM products WHERE price LIKE '%₹%'")
with_rupee = cursor.fetchall()

print(f'Total products: {total}')
print(f'Products with rupee symbol in price: {len(with_rupee)}')

if with_rupee:
    print('\nProducts with rupee symbol:')
    for row in with_rupee:
        print(f'  {repr(row[0])}')

# Get all unique price values to see pattern
cursor.execute('SELECT DISTINCT price FROM products ORDER BY price')
prices = cursor.fetchall()
print(f'\nUnique prices in database (first 15):')
for i, p in enumerate(prices[:15]):
    print(f'  {i+1}. {repr(p[0])}')

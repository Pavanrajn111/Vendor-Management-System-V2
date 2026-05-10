import sqlite3

conn = sqlite3.connect('vendor.db')
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(products)")
products_columns = [info[1] for info in cursor.fetchall()]
print("Products Columns:", products_columns)

cursor.execute("PRAGMA table_info(orders)")
orders_columns = [info[1] for info in cursor.fetchall()]
print("Orders Columns:", orders_columns)

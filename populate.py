import sqlite3

conn=sqlite3.connect('vendor.db')
try:
    conn.execute("INSERT INTO users (username, password, role) VALUES ('v1', '123', 'vendor')")
    conn.execute("INSERT INTO users (username, password, role) VALUES ('c1', '123', 'customer')")
    conn.execute("INSERT INTO products (vendor, name, price, image, availability) VALUES ('v1', 'p1', '10', '', 'In Stock')")
    conn.execute("INSERT INTO orders (customer, vendor, product_name, price, status, product_image) VALUES ('c1', 'v1', 'p1', '10', 'Pending', '')")
    conn.commit()
except Exception as e:
    print(e)

from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"

# -----------------------------
# Database Connection
# -----------------------------
def get_db():
    conn = sqlite3.connect("vendor.db")
    conn.row_factory = sqlite3.Row
    return conn

# -----------------------------
# CREATE TABLES (ADDED)
# -----------------------------
def create_tables():
    conn = sqlite3.connect("vendor.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vendors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        contact TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price REAL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vendor_id INTEGER,
        product_id INTEGER,
        status TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        amount REAL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vendor_id INTEGER,
        rating INTEGER,
        comment TEXT
    )
    """)

    conn.commit()
    conn.close()

# -----------------------------
# Login
# -----------------------------
@app.route('/', methods=['GET', 'POST'])
def login():

    conn = get_db()

    error = ""

    if request.method == 'POST':

        username = request.form['username']

        password = request.form['password']

        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        ).fetchone()

        if user:

            session['user'] = username

            return redirect('/dashboard')

        else:

            error = "Invalid Username or Password"

    return render_template(
        'login.html',
        error=error
    )

# -----------------------------
# Register
# -----------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():

    conn = get_db()

    error = ""

    if request.method == 'POST':

        username = request.form['username']

        password = request.form['password']

        # CHECK IF USERNAME ALREADY EXISTS

        existing_user = conn.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        ).fetchone()

        if existing_user:

            error = "Username already exists"

            return render_template(
                'register.html',
                error=error
            )

        # INSERT NEW USER

        conn.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password)
        )

        conn.commit()

        return redirect('/')

    return render_template(
        'register.html',
        error=error
    )


# -----------------------------
# Dashboard
# -----------------------------
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/')
    return render_template('dashboard.html')


# -----------------------------
# Vendors
# -----------------------------
@app.route('/vendors', methods=['GET', 'POST'])
def vendors():
    conn = get_db()

    if request.method == 'POST':
        name = request.form['name']
        contact = request.form['contact']

        conn.execute(
            "INSERT INTO vendors (name, contact) VALUES (?, ?)",
            (name, contact)
        )
        conn.commit()

    vendors = conn.execute("SELECT * FROM vendors").fetchall()
    return render_template('vendors.html', vendors=vendors)


# -----------------------------
# Products
# -----------------------------
@app.route('/products', methods=['GET', 'POST'])
def products():
    conn = get_db()

    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']

        conn.execute(
            "INSERT INTO products (name, price) VALUES (?, ?)",
            (name, price)
        )
        conn.commit()

    products = conn.execute("SELECT * FROM products").fetchall()
    return render_template('products.html', products=products)


# -----------------------------
# Orders
# -----------------------------
@app.route('/orders', methods=['GET', 'POST'])
def orders():
    conn = get_db()

    if request.method == 'POST':
        vendor_id = request.form['vendor_id']
        product_id = request.form['product_id']
        status = request.form['status']

        conn.execute(
            "INSERT INTO orders (vendor_id, product_id, status) VALUES (?, ?, ?)",
            (vendor_id, product_id, status)
        )
        conn.commit()

    orders = conn.execute("SELECT * FROM orders").fetchall()
    vendors = conn.execute("SELECT * FROM vendors").fetchall()
    products = conn.execute("SELECT * FROM products").fetchall()

    return render_template('orders.html',
                           orders=orders,
                           vendors=vendors,
                           products=products)


# -----------------------------
# Payments
# -----------------------------
@app.route('/payments', methods=['GET', 'POST'])
def payments():
    conn = get_db()

    if request.method == 'POST':
        order_id = request.form['order_id']
        amount = request.form['amount']

        conn.execute(
            "INSERT INTO payments (order_id, amount) VALUES (?, ?)",
            (order_id, amount)
        )
        conn.commit()

    payments = conn.execute("SELECT * FROM payments").fetchall()
    orders = conn.execute("SELECT * FROM orders").fetchall()

    return render_template('payments.html',
                           payments=payments,
                           orders=orders)


# -----------------------------
# Reviews
# -----------------------------
@app.route('/reviews', methods=['GET', 'POST'])
def reviews():
    conn = get_db()

    if request.method == 'POST':
        vendor_id = request.form['vendor_id']
        rating = request.form['rating']
        comment = request.form['comment']

        conn.execute(
            "INSERT INTO reviews (vendor_id, rating, comment) VALUES (?, ?, ?)",
            (vendor_id, rating, comment)
        )
        conn.commit()

    reviews = conn.execute("SELECT * FROM reviews").fetchall()
    vendors = conn.execute("SELECT * FROM vendors").fetchall()

    return render_template('reviews.html',
                           reviews=reviews,
                           vendors=vendors)


# -----------------------------
# Logout
# -----------------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# -----------------------------
# Profile
# -----------------------------
@app.route('/profile')
def profile():

    if 'user' not in session:
        return redirect('/')

    return render_template('profile.html')


# -----------------------------
# Run App
# -----------------------------
if __name__ == '__main__':

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
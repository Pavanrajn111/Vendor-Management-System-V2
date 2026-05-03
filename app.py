from flask import Flask, render_template, request, redirect, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------------------------
# DATABASE CONNECTION
# ---------------------------------

def get_db():
    conn = sqlite3.connect("vendor.db")
    conn.row_factory = sqlite3.Row
    return conn

# ---------------------------------
# CREATE DATABASE TABLES
# ---------------------------------

conn = get_db()

conn.execute('''
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT,
    mobile TEXT
)
''')

conn.execute('''
CREATE TABLE IF NOT EXISTS vendors(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    contact TEXT
)
''')

conn.execute('''
CREATE TABLE IF NOT EXISTS products(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor TEXT,
    name TEXT,
    price TEXT
)
''')

conn.execute('''
CREATE TABLE IF NOT EXISTS orders(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer TEXT,
    vendor TEXT,
    product_name TEXT,
    price TEXT,
    status TEXT
)
''')

conn.execute('''
CREATE TABLE IF NOT EXISTS payments(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER,
    customer TEXT,
    vendor TEXT,
    product_name TEXT,
    amount TEXT,
    status TEXT
)
''')

conn.execute('''
CREATE TABLE IF NOT EXISTS reviews(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor TEXT,
    rating TEXT,
    comment TEXT,
    customer TEXT
)
''')
conn.execute('''
CREATE TABLE IF NOT EXISTS connections(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer TEXT,
    vendor TEXT
)
''')

conn.commit()

# ---------------------------------
# LOGIN
# ---------------------------------

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

            session['user'] = user['username']
            session['role'] = user['role']

            return redirect('/dashboard')

        else:
            error = "Invalid Username or Password"

    return render_template('login.html', error=error)

# ---------------------------------
# REGISTER
# ---------------------------------

@app.route('/register', methods=['GET', 'POST'])
def register():

    conn = get_db()

    error = ""

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

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
        mobile = request.form['mobile']

        conn.execute(
            "INSERT INTO users(username,password,role,mobile) VALUES(?,?,?,?)",
            (username,password,role,mobile)
        )

        conn.commit()

        return redirect('/')

    return render_template('register.html', error=error)

# ---------------------------------
# DASHBOARD
# ---------------------------------

@app.route('/dashboard')
def dashboard():

    if 'user' not in session:
        return redirect('/')

    return render_template('dashboard.html')

# ---------------------------------
# PROFILE
# ---------------------------------

@app.route('/profile')
def profile():

    if 'user' not in session:
        return redirect('/')

    conn = get_db()

    role = session['role']

    # -------------------------
    # VENDOR PROFILE
    # -------------------------

    if role == "vendor":

        total_customers = conn.execute(
        "SELECT COUNT(*) FROM connections WHERE vendor=?",
        (session['user'],)
        ).fetchone()[0]
        connected_customers = conn.execute(
            "SELECT customer FROM connections WHERE vendor=?",
            (session['user'],)
        ).fetchall()

        total_orders = conn.execute(
            "SELECT COUNT(*) FROM orders"
        ).fetchone()[0]

        total_reviews = conn.execute(
            "SELECT COUNT(*) FROM reviews"
        ).fetchone()[0]

        return render_template(
            'vendor_profile.html',
            total_customers=total_customers,
            total_orders=total_orders,
            connected_customers=connected_customers,
            total_reviews=total_reviews
        )

    # -------------------------
    # CUSTOMER PROFILE
    # -------------------------

    else:

        total_vendors = conn.execute(
        "SELECT COUNT(*) FROM users WHERE role='vendor'"
        ).fetchone()[0]

        connected_vendors = conn.execute(
            "SELECT vendor FROM connections WHERE customer=?",
            (session['user'],)
        ).fetchall()

        total_orders = conn.execute(
            "SELECT COUNT(*) FROM orders"
        ).fetchone()[0]

        total_payments = conn.execute(
            "SELECT COUNT(*) FROM payments"
        ).fetchone()[0]

        return render_template(
            'customer_profile.html',
            total_vendors=total_vendors,
            total_orders=total_orders,
            connected_vendors=connected_vendors,
            total_payments=total_payments
        )
# ---------------------------------
# VENDORS
# ---------------------------------

@app.route('/vendors')
def vendors():

    if 'user' not in session:
        return redirect('/')

    conn = get_db()

    vendors = conn.execute(
        "SELECT username,mobile FROM users WHERE role='vendor'"
    ).fetchall()

    connected = conn.execute(
        "SELECT vendor FROM connections WHERE customer=?",
        (session['user'],)
    ).fetchall()

    connected_vendors = [
        v['vendor'] for v in connected
    ]

    return render_template(
        'vendors.html',
        vendors=vendors,
        connected_vendors=connected_vendors
    )

@app.route('/products', methods=['GET', 'POST'])
def products():

    if 'user' not in session:
        return redirect('/')

    conn = get_db()

    role = session['role']

    # -------------------------
    # VENDOR
    # -------------------------

    if role == "vendor":

        if request.method == 'POST':

            name = request.form['name']
            price = request.form['price']

            vendor = session['user']

            conn.execute(
                "INSERT INTO products(vendor,name,price) VALUES(?,?,?)",
                (vendor,name,price)
            )

            conn.commit()

        products = conn.execute(
            "SELECT * FROM products WHERE vendor=?",
            (session['user'],)
        ).fetchall()

        return render_template(
            'products.html',
            products=products
        )

    # -------------------------
    # CUSTOMER
    # -------------------------

    else:

        connected_vendors = conn.execute(
            "SELECT vendor FROM connections WHERE customer=?",
            (session['user'],)
        ).fetchall()

        vendor_names = [v['vendor'] for v in connected_vendors]

        if vendor_names:

            placeholders = ",".join("?" * len(vendor_names))

            query = f"""
                SELECT * FROM products
                WHERE vendor IN ({placeholders})
            """

            products = conn.execute(
                query,
                vendor_names
            ).fetchall()

        else:
            products = []

        return render_template(
            'customer_products.html',
            products=products
        )

@app.route('/orders')
def orders():

    if 'user' not in session:
        return redirect('/')

    conn = get_db()

    role = session['role']

    # -------------------------
    # VENDOR
    # -------------------------

    if role == "vendor":

        orders = conn.execute(
            "SELECT * FROM orders WHERE vendor=?",
            (session['user'],)
        ).fetchall()

    # -------------------------
    # CUSTOMER
    # -------------------------

    else:

        orders = conn.execute(
            "SELECT * FROM orders WHERE customer=?",
            (session['user'],)
        ).fetchall()

    return render_template(
        'orders.html',
        orders=orders
    )
# ---------------------------------
# DELIVERY
# ---------------------------------

@app.route('/delivery')
def delivery():

    if 'user' not in session:
        return redirect('/')

    conn = get_db()

    if session['role'] == 'vendor':

        orders = conn.execute(
            "SELECT * FROM orders WHERE vendor=?",
            (session['user'],)
        ).fetchall()

    else:

        orders = conn.execute(
            "SELECT * FROM orders WHERE customer=?",
            (session['user'],)
        ).fetchall()

    return render_template(
        'delivery.html',
        orders=orders
    )
# ---------------------------------
# PAYMENTS
# ---------------------------------

@app.route('/payments', methods=['GET', 'POST'])
def payments():

    if 'user' not in session:
        return redirect('/')

    conn = get_db()

    # CUSTOMER MAKES PAYMENT

    if request.method == 'POST':

        customer = session['user']

        vendor = request.form['vendor']

        product_name = request.form['product_name']

        amount = request.form['amount']

        order_id = request.form['order_id']

        existing_payment = conn.execute(
            '''
            SELECT * FROM payments
            WHERE order_id=?
            ''',
            (order_id,)
        ).fetchone()

        if not existing_payment:

            conn.execute(
                '''
                INSERT INTO payments
                (
                    order_id,
                    customer,
                    vendor,
                    product_name,
                    amount,
                    status
                )
                VALUES(?,?,?,?,?,?)
                ''',
                (
                    order_id,
                    customer,
                    vendor,
                    product_name,
                    amount,
                    'Pending'
                )
            )

            conn.commit()

    # CUSTOMER VIEW

    if session['role'] == 'customer':

        payments = conn.execute(
            '''
            SELECT * FROM payments
            WHERE customer=?
            ''',
            (session['user'],)
        ).fetchall()

        orders = conn.execute(
            '''
            SELECT * FROM orders
            WHERE customer=?
            ''',
            (session['user'],)
        ).fetchall()

    # VENDOR VIEW

    else:

        payments = conn.execute(
            '''
            SELECT * FROM payments
            WHERE vendor=?
            ''',
            (session['user'],)
        ).fetchall()

        orders = []

    return render_template(
        'payments.html',
        payments=payments,
        orders=orders
    )
@app.route('/update_payment', methods=['POST'])
def update_payment():

    if 'user' not in session:
        return redirect('/')

    payment_id = request.form['payment_id']

    status = request.form['status']

    conn = get_db()

    conn.execute(
        '''
        UPDATE payments
        SET status=?
        WHERE id=?
        ''',
        (status,payment_id)
    )

    conn.commit()

    return redirect('/payments')
# ---------------------------------
# REVIEWS
# ---------------------------------

@app.route('/reviews', methods=['GET', 'POST'])
def reviews():

    if 'user' not in session:
        return redirect('/')

    conn = get_db()

    role = session['role']

    # -------------------------
    # CUSTOMER ADDS REVIEW
    # -------------------------

    if request.method == 'POST' and role == "customer":

        vendor = request.form['vendor']
        rating = request.form['rating']
        comment = request.form['comment']

        conn.execute(
            """
            INSERT INTO reviews(vendor,rating,comment,customer)
            VALUES(?,?,?,?)
            """,
            (vendor, rating, comment, session['user'])
        )

        conn.commit()

    # -------------------------
    # CUSTOMER VIEW
    # -------------------------

    if role == "customer":

        connected_vendors = conn.execute(
            """
            SELECT vendor
            FROM connections
            WHERE customer=?
            """,
            (session['user'],)
        ).fetchall()

        reviews = conn.execute(
            "SELECT * FROM reviews"
        ).fetchall()

        return render_template(
            'reviews.html',
            reviews=reviews,
            vendors=connected_vendors
        )

    # -------------------------
    # VENDOR VIEW
    # -------------------------

    else:

        reviews = conn.execute(
            """
            SELECT * FROM reviews
            WHERE vendor=?
            """,
            (session['user'],)
        ).fetchall()

        return render_template(
            'reviews.html',
            reviews=reviews,
            vendors=[]
        )
# ---------------------------------
# VIEW ALL USERS
# ---------------------------------

@app.route('/allusers')
def allusers():

    if 'user' not in session:
        return redirect('/')

    conn = get_db()

    users = conn.execute(
        "SELECT * FROM users"
    ).fetchall()

    return render_template(
        'allusers.html',
        users=users
    )
@app.route('/select_vendor', methods=['POST'])
def select_vendor():

    if 'user' not in session:
        return redirect('/')

    customer = session['user']

    vendor = request.form['vendor']

    conn = get_db()

    existing = conn.execute(
        "SELECT * FROM connections WHERE customer=? AND vendor=?",
        (customer, vendor)
    ).fetchone()

    if not existing:

        conn.execute(
            "INSERT INTO connections(customer,vendor) VALUES(?,?)",
            (customer, vendor)
        )

        conn.commit()

    return redirect('/vendors')
@app.route('/add_order', methods=['POST'])
def add_order():

    if 'user' not in session:
        return redirect('/')

    product_id = request.form['product_id']

    customer = session['user']

    conn = get_db()

    product = conn.execute(
        "SELECT * FROM products WHERE id=?",
        (product_id,)
    ).fetchone()

    vendor = product['vendor']
    product_name = product['name']
    price = product['price']

    conn.execute(
        '''
        INSERT INTO orders(
            customer,
            vendor,
            product_name,
            price,
            status
        )
        VALUES(?,?,?,?,?)
        ''',
        (
            customer,
            vendor,
            product_name,
            price,
            'Pending'
        )
    )

    conn.commit()

    return redirect('/orders')
@app.route('/update_order', methods=['POST'])
def update_order():

    order_id = request.form['order_id']

    status = request.form['status']

    conn = get_db()

    conn.execute(
        "UPDATE orders SET status=? WHERE id=?",
        (status, order_id)
    )
    if status == "Out Of Stock":

        order = conn.execute(
        "SELECT * FROM orders WHERE id=?",
        (order_id,)
    ).fetchone()

    existing_payment = conn.execute(
        '''
        SELECT * FROM payments
        WHERE order_id=?
        ''',
        (order_id,)
    ).fetchone()

    if not existing_payment:

        conn.execute(
            '''
            INSERT INTO payments
            (
                order_id,
                customer,
                vendor,
                product_name,
                amount,
                status
            )
            VALUES(?,?,?,?,?,?)
            ''',
            (
                order['id'],
                order['customer'],
                order['vendor'],
                order['product_name'],
                order['price'],
                'Out Of Stock'
            )
        )

    conn.commit()

    return redirect('/orders')
# ---------------------------------
# VIEW VENDOR PRODUCTS
# ---------------------------------

@app.route('/vendor_products/<vendor_name>')
def vendor_products(vendor_name):

    if 'user' not in session:
        return redirect('/')

    conn = get_db()

    # CHECK CONNECTION

    connection = conn.execute(
        '''
        SELECT * FROM connections
        WHERE customer=? AND vendor=?
        ''',
        (session['user'], vendor_name)
    ).fetchone()

    connected = False

    if connection:
        connected = True

    # GET PRODUCTS OF THAT VENDOR

    products = conn.execute(
        '''
        SELECT * FROM products
        WHERE vendor=?
        ''',
        (vendor_name,)
    ).fetchall()

    return render_template(
        'vendor_products.html',
        products=products,
        vendor_name=vendor_name,
        connected=connected
    )
# ---------------------------------
# VIEW SINGLE VENDOR REVIEWS
# ---------------------------------

@app.route('/vendor_reviews/<vendor_name>')
def vendor_reviews(vendor_name):

    if 'user' not in session:
        return redirect('/')

    conn = get_db()

    reviews = conn.execute(
        '''
        SELECT * FROM reviews
        WHERE vendor=?
        ''',
        (vendor_name,)
    ).fetchall()

    return render_template(
        'vendor_reviews.html',
        vendor_name=vendor_name,
        reviews=reviews
    )
# ---------------------------------
# DELETE PRODUCT
# ---------------------------------

@app.route('/delete_product/<int:id>')
def delete_product(id):

    if 'user' not in session:
        return redirect('/')

    conn = get_db()

    conn.execute(
        "DELETE FROM products WHERE id=?",
        (id,)
    )

    conn.commit()

    return redirect('/products')

    return redirect('/products')
# ---------------------------------
# LOGOUT
# ---------------------------------

@app.route('/logout')
def logout():

    session.clear()

    return redirect('/')

# ---------------------------------
# RUN APP
# ---------------------------------

if __name__ == '__main__':
    app.run(debug=True)
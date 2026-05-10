from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret123"

UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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
    status TEXT,
    payment_date DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

conn.execute('''
CREATE TABLE IF NOT EXISTS reviews(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor TEXT,
    rating TEXT,
    comment TEXT,
    customer TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
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
# APPLY SCHEMA MIGRATIONS
# ---------------------------------
try:
    conn.execute('ALTER TABLE products ADD COLUMN image TEXT DEFAULT ""')
except:
    pass
try:
    conn.execute('ALTER TABLE products ADD COLUMN availability TEXT DEFAULT "In Stock"')
except:
    pass
try:
    conn.execute('ALTER TABLE orders ADD COLUMN product_image TEXT DEFAULT ""')
except:
    pass
try:
    conn.execute('ALTER TABLE orders ADD COLUMN expected_delivery TEXT DEFAULT ""')
except:
    pass
try:
    conn.execute('ALTER TABLE orders ADD COLUMN delivered_date TEXT DEFAULT ""')
except:
    pass
def ensure_column_exists(conn, table, column, definition):
    columns = [row['name'] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

try:
    ensure_column_exists(conn, 'payments', 'payment_date', 'TEXT DEFAULT ""')
except:
    pass
try:
    ensure_column_exists(conn, 'reviews', 'created_at', 'DATETIME DEFAULT CURRENT_TIMESTAMP')
except:
    pass
conn.commit()

# ---------------------------------
# CUSTOM FILTERS
# ---------------------------------
@app.template_filter('time_ago')
def time_ago(dt_str):
    if not dt_str:
        return ""
    try:
        dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
    except:
        return dt_str
    
    now = datetime.now()
    diff = now - dt
    
    if diff.days > 365:
        return f"{diff.days // 365} year{'s' if diff.days // 365 > 1 else ''} ago"
    elif diff.days > 30:
        return f"{diff.days // 30} month{'s' if diff.days // 30 > 1 else ''} ago"
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        return f"{diff.seconds // 3600} hour{'s' if diff.seconds // 3600 > 1 else ''} ago"
    elif diff.seconds > 60:
        return f"{diff.seconds // 60} minute{'s' if diff.seconds // 60 > 1 else ''} ago"
    else:
        return "Just now"

# ---------------------------------
# LANDING PAGE
# ---------------------------------

@app.route('/')
def index():
    return render_template('index.html')

# ---------------------------------
# LOGIN & SETTINGS
# ---------------------------------

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user' not in session:
        return redirect('/login')
        
    conn = get_db()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_password':
            new_password = request.form['new_password']
            conn.execute("UPDATE users SET password=? WHERE username=?", (new_password, session['user']))
            conn.commit()
            
        elif action == 'update_mobile':
            mobile = request.form['mobile']
            conn.execute("UPDATE users SET mobile=? WHERE username=?", (mobile, session['user']))
            conn.commit()
            
        return redirect('/settings?success=1')
        
    user = conn.execute("SELECT * FROM users WHERE username=?", (session['user'],)).fetchone()
    return render_template('settings.html', user=user)

@app.route('/login', methods=['GET', 'POST'])
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

        return redirect('/login')

    return render_template('register.html', error=error)

# ---------------------------------
# DASHBOARD
# ---------------------------------

@app.route('/dashboard')
def dashboard():

    if 'user' not in session:
        return redirect('/login')

    return render_template('dashboard.html')

# ---------------------------------
# PROFILE
# ---------------------------------

@app.route('/profile')
def profile():

    if 'user' not in session:
        return redirect('/login')

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
        return redirect('/login')

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
        return redirect('/login')

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
            image_path = ""

            if 'image' in request.files:
                file = request.files['image']
                if file.filename != '':
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    image_path = f"uploads/{filename}"

            conn.execute(
                "INSERT INTO products(vendor,name,price,image,availability) VALUES(?,?,?,?,?)",
                (vendor,name,price,image_path,"In Stock")
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

@app.route('/edit_product/<int:id>', methods=['POST'])
def edit_product(id):
    if 'user' not in session or session.get('role') != 'vendor':
        return redirect('/login')

    conn = get_db()
    name = request.form['name']
    price = request.form['price']
    availability = request.form['availability']
    
    # Check if a new image was uploaded
    if 'image' in request.files:
        file = request.files['image']
        if file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_path = f"uploads/{filename}"
            conn.execute(
                "UPDATE products SET name=?, price=?, availability=?, image=? WHERE id=? AND vendor=?",
                (name, price, availability, image_path, id, session['user'])
            )
            conn.commit()
            return redirect('/products')
            
    conn.execute(
        "UPDATE products SET name=?, price=?, availability=? WHERE id=? AND vendor=?",
        (name, price, availability, id, session['user'])
    )
    conn.commit()
    return redirect('/products')

@app.route('/delete_product/<int:id>')
def delete_product(id):
    if 'user' not in session or session.get('role') != 'vendor':
        return redirect('/login')

    conn = get_db()
    conn.execute("DELETE FROM products WHERE id=? AND vendor=?", (id, session['user']))
    conn.commit()
    return redirect('/products')

@app.route('/orders')
def orders():

    if 'user' not in session:
        return redirect('/login')

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
        return redirect('/login')

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
        return redirect('/login')

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
                    status,
                    payment_date
                )
                VALUES(?,?,?,?,?,?,?)
                ''',
                (
                    order_id,
                    customer,
                    vendor,
                    product_name,
                    amount,
                    'Completed',
                    datetime.now().strftime('%d-%m-%Y %H:%M')
                )
            )

            conn.commit()

    # CUSTOMER VIEW
    if session['role'] == 'customer':
        payments = conn.execute(
            '''
            SELECT p.*, o.product_image, o.status as delivery_status, o.delivered_date 
            FROM payments p
            LEFT JOIN orders o ON p.order_id = o.id
            WHERE p.customer=?
            ORDER BY p.payment_date DESC, p.id DESC
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
            SELECT p.*, o.product_image, o.status as delivery_status, o.delivered_date 
            FROM payments p
            LEFT JOIN orders o ON p.order_id = o.id
            WHERE p.vendor=?
            ORDER BY p.payment_date DESC, p.id DESC
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
        return redirect('/login')

    payment_id = request.form['payment_id']

    status = request.form['status']

    conn = get_db()

    conn.execute(
        '''
        UPDATE payments
        SET status=?, payment_date=?
        WHERE id=?
        ''',
        (status, datetime.now().strftime('%d-%m-%Y %H:%M'), payment_id)
    )

    conn.commit()

    return redirect('/payments')

@app.route('/process_refund', methods=['POST'])
def process_refund():
    if 'user' not in session or session.get('role') != 'vendor':
        return redirect('/login')
        
    payment_id = request.form['payment_id']
    conn = get_db()
    conn.execute("UPDATE payments SET status='Refund Completed', payment_date=? WHERE id=?", (datetime.now().strftime('%d-%m-%Y %H:%M'), payment_id))
    conn.commit()
    return redirect('/payments')
# ---------------------------------
# REVIEWS
# ---------------------------------

@app.route('/reviews', methods=['GET', 'POST'])
def reviews():

    if 'user' not in session:
        return redirect('/login')

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
        return redirect('/login')

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
        return redirect('/login')

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
        return redirect('/login')

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
            status,
            product_image
        )
        VALUES(?,?,?,?,?,?)
        ''',
        (
            customer,
            vendor,
            product_name,
            price,
            'Pending',
            product['image']
        )
    )

    conn.commit()

    return redirect('/orders')
@app.route('/update_order', methods=['POST'])
def update_order():
    if 'user' not in session or session.get('role') != 'vendor':
        return redirect('/login')

    order_id = request.form['order_id']
    status = request.form['status']
    expected_delivery = request.form.get('expected_delivery', '')
    delivered_date = request.form.get('delivered_date', '')

    conn = get_db()

    conn.execute(
        "UPDATE orders SET status=?, expected_delivery=?, delivered_date=? WHERE id=?",
        (status, expected_delivery, delivered_date, order_id)
    )

    if status == "Out Of Stock":
        order = conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
        existing_payment = conn.execute("SELECT * FROM payments WHERE order_id=?", (order_id,)).fetchone()
        
        if not existing_payment:
            conn.execute(
                '''
                INSERT INTO payments(order_id, customer, vendor, product_name, amount, status, payment_date)
                VALUES(?,?,?,?,?,?,?)
                ''',
                (order['id'], order['customer'], order['vendor'], order['product_name'], order['price'], 'Out Of Stock', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            )
        else:
            conn.execute("UPDATE payments SET status='Out Of Stock' WHERE order_id=?", (order_id,))

    conn.commit()
    return redirect('/orders')

@app.route('/cancel_order', methods=['POST'])
def cancel_order():
    if 'user' not in session:
        return redirect('/login')

    order_id = request.form['order_id']
    conn = get_db()
    
    order = conn.execute("SELECT * FROM orders WHERE id=? AND customer=?", (order_id, session['user'])).fetchone()
    if order and order['status'] not in ['Shipped', 'Out For Delivery', 'Delivered', 'Cancelled']:
        conn.execute("UPDATE orders SET status='Cancelled' WHERE id=?", (order_id,))
        
        # Check if payment exists
        payment = conn.execute("SELECT * FROM payments WHERE order_id=?", (order_id,)).fetchone()
        if payment and payment['status'] in ['Completed', 'Accepted']:
            conn.execute("UPDATE payments SET status='Refund Pending', payment_date=? WHERE order_id=?", (datetime.now().strftime('%d-%m-%Y %H:%M'), order_id))
            
        conn.commit()

    return redirect('/orders')
# ---------------------------------
# VIEW VENDOR PRODUCTS
# ---------------------------------

@app.route('/vendor_products/<vendor_name>')
def vendor_products(vendor_name):

    if 'user' not in session:
        return redirect('/login')

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
        return redirect('/login')

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
# LOGOUT
# ---------------------------------

@app.route('/logout')
def logout():

    session.clear()

    return redirect('/')

# ---------------------------------
# RUN APP
# ---------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
import re
import base64
import io
from urllib.parse import quote
from werkzeug.utils import secure_filename
from datetime import datetime

try:
    import qrcode
except ImportError:
    qrcode = None

app = Flask(__name__)
app.secret_key = "secret123"

# Date/datetime strings we may read from SQLite or legacy rows
_INDIAN_DISPLAY_DT = '%d/%m/%Y, %I:%M %p'
_INDIAN_DISPLAY_D = '%d/%m/%Y'
_PARSE_FORMATS_DT = [
    '%d/%m/%Y, %I:%M %p',
    '%d/%m/%Y, %I:%M%p',
    '%d/%m/%Y %I:%M %p',
    '%d-%m-%Y %H:%M',
    '%Y-%m-%d %H:%M:%S',
    '%Y-%m-%d %H:%M',
    '%Y-%m-%dT%H:%M:%S',
    '%Y-%m-%dT%H:%M:%S.%f',
]
_PARSE_FORMATS_D = [
    '%Y-%m-%d',
    '%d/%m/%Y',
    '%d-%m-%Y',
]


def _parse_datetime(date_str):
    """Return datetime or None."""
    if not date_str:
        return None
    s = str(date_str).strip()
    for fmt in _PARSE_FORMATS_DT:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    for fmt in _PARSE_FORMATS_D:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def format_indian_date(date_str):
    """Display in Indian format: DD/MM/YYYY, HH:MM AM/PM (date-only when no time in source)."""
    if not date_str:
        return ""
    s = str(date_str).strip()
    dt = _parse_datetime(s)
    if not dt:
        return s
    date_only = (
        (len(s) <= 10 and ' ' not in s and 'T' not in s and ',' not in s)
        or re.match(r'^\d{4}-\d{2}-\d{2}$', s)
    )
    if date_only:
        return dt.strftime(_INDIAN_DISPLAY_D)
    return dt.strftime(_INDIAN_DISPLAY_DT)


def to_input_date(date_str):
    """HTML date input value (YYYY-MM-DD) from stored order dates."""
    if not date_str:
        return ""
    dt = _parse_datetime(str(date_str).strip())
    if not dt:
        return ""
    return dt.strftime('%Y-%m-%d')


# Demo collect UPI VPA for QR (override with env COLLECT_UPI_VPA in production)
COLLECT_UPI_FALLBACK = os.environ.get('COLLECT_UPI_VPA', 'merchant.vms@ptyes')

UPI_PLATFORM_SLUGS = {
    'gpay': 'Google Pay',
    'phonepe': 'PhonePe',
    'paytm': 'Paytm',
}


def _digits_only_amount(price_str):
    s = re.sub(r'[^\d.]', '', str(price_str or ''))
    try:
        return f'{float(s):.2f}' if s else '0.00'
    except ValueError:
        return '0.00'


def _luhn_valid(number_str):
    digits = [int(c) for c in re.sub(r'\D', '', number_str)]
    if len(digits) < 13 or len(digits) > 19:
        return False
    checksum = 0
    parity = len(digits) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


def _card_expiry_valid(mm_yy):
    if not mm_yy or not re.match(r'^\d{2}/\d{2}$', mm_yy.strip()):
        return False
    mm, yy = mm_yy.strip().split('/')
    try:
        m, y = int(mm), int(yy)
    except ValueError:
        return False
    if m < 1 or m > 12:
        return False
    y_full = 2000 + y if y < 100 else y
    now = datetime.now()
    if y_full > now.year + 20 or y_full < now.year - 1:
        return False
    if y_full < now.year or (y_full == now.year and m < now.month):
        return False
    return True


def _upi_format_valid(upi):
    upi = (upi or '').strip().lower()
    return bool(re.match(r'^[a-z0-9._-]{2,64}@[a-z0-9.-]{2,64}$', upi))


def _mask_upi_id(upi):
    upi = (upi or '').strip()
    if '@' not in upi:
        return '***'
    local, _, domain = upi.partition('@')
    if len(local) <= 3:
        masked = local[0] + '**' if local else '**'
    else:
        masked = local[:2] + '***' + local[-1]
    return f'{masked}@{domain}'


def _vendor_collect_vpa(conn, vendor_username):
    row = conn.execute(
        "SELECT upi_vpa FROM users WHERE username=?",
        (vendor_username,),
    ).fetchone()
    if row and row['upi_vpa'] and str(row['upi_vpa']).strip():
        return str(row['upi_vpa']).strip()
    return COLLECT_UPI_FALLBACK


def _build_upi_uri(vpa, payee_name, amount, note):
    return (
        'upi://pay?'
        f'pa={quote(vpa)}&pn={quote(payee_name)}&am={quote(amount)}&cu=INR&tn={quote(note)}'
    )


def _qr_data_uri(text):
    if not qrcode:
        return None
    try:
        qr = qrcode.QRCode(version=1, box_size=6, border=2)
        qr.add_data(text)
        qr.make(fit=True)
        img = qr.make_image(fill_color='black', back_color='white')
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode('ascii')
    except Exception:
        return None


def _payment_order_state(conn, order_id, customer):
    """Returns (order_row_or_None, state) where state is new|retry|awaiting|blocked|invalid."""
    o = conn.execute(
        "SELECT * FROM orders WHERE id=? AND customer=?",
        (order_id, customer),
    ).fetchone()
    if not o or o['status'] != 'Accepted':
        return None, 'invalid'
    pay = conn.execute("SELECT * FROM payments WHERE order_id=?", (order_id,)).fetchone()
    if not pay:
        return o, 'new'
    st = pay['status']
    if st == 'Payment Not Received':
        return o, 'retry'
    if st in ('Accepted', 'Verified', 'Refund Completed', 'Out Of Stock', 'Refund Pending'):
        return o, 'blocked'
    if st in ('Pending Vendor Verification', 'Completed'):
        return o, 'awaiting'
    return o, 'unknown'


def _finalize_customer_payment(
    conn,
    order_id,
    customer,
    vendor,
    product_name,
    amount,
    payment_method,
    upi_platform,
    upi_flow,
    card_last4,
    upi_masked,
):
    payment_time = datetime.now().strftime('%d/%m/%Y, %I:%M %p')
    existing = conn.execute("SELECT * FROM payments WHERE order_id=?", (order_id,)).fetchone()
    if not existing:
        conn.execute(
            '''
            INSERT INTO payments(
                order_id, customer, vendor, product_name, amount, status, payment_date,
                payment_method, upi_platform, upi_flow, card_last4, upi_masked
            )
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
            ''',
            (
                order_id,
                customer,
                vendor,
                product_name,
                amount,
                'Pending Vendor Verification',
                payment_time,
                payment_method or '',
                upi_platform or '',
                upi_flow or '',
                card_last4 or '',
                upi_masked or '',
            ),
        )
    elif existing['status'] == 'Payment Not Received':
        conn.execute(
            '''
            UPDATE payments SET
                vendor=?, product_name=?, amount=?, status=?, payment_date=?,
                payment_method=?, upi_platform=?, upi_flow=?, card_last4=?, upi_masked=?
            WHERE order_id=?
            ''',
            (
                vendor,
                product_name,
                amount,
                'Pending Vendor Verification',
                payment_time,
                payment_method or '',
                upi_platform or '',
                upi_flow or '',
                card_last4 or '',
                upi_masked or '',
                order_id,
            ),
        )
    else:
        return False
    conn.commit()
    return True

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
for _col, _def in [
    ('payment_method', 'TEXT DEFAULT ""'),
    ('upi_platform', 'TEXT DEFAULT ""'),
    ('upi_flow', 'TEXT DEFAULT ""'),
    ('card_last4', 'TEXT DEFAULT ""'),
    ('upi_masked', 'TEXT DEFAULT ""'),
]:
    try:
        ensure_column_exists(conn, 'payments', _col, _def)
    except Exception:
        pass
try:
    ensure_column_exists(conn, 'users', 'upi_vpa', 'TEXT DEFAULT ""')
except Exception:
    pass
conn.commit()

# ---------------------------------
# CUSTOM FILTERS
# ---------------------------------

# Add Indian date format filter
@app.template_filter('indian_date')
def indian_date_filter(date_str):
    return format_indian_date(date_str)


@app.template_filter('input_date')
def input_date_filter(date_str):
    return to_input_date(date_str)

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
    error = ""
    success = ""
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_password':
            current_password = request.form.get('current_password', '')
            new_password = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_password', '')
            
            # Get user from database
            user = conn.execute("SELECT * FROM users WHERE username=?", (session['user'],)).fetchone()
            
            # Validate current password
            if current_password != user['password']:
                error = "Current password is incorrect"
            elif new_password != confirm_password:
                error = "New passwords do not match"
            elif len(new_password) < 8:
                error = "Password must be at least 8 characters"
            elif not any(c.isupper() for c in new_password):
                error = "Password must contain at least one uppercase letter"
            elif not any(c.islower() for c in new_password):
                error = "Password must contain at least one lowercase letter"
            elif not any(c.isdigit() for c in new_password):
                error = "Password must contain at least one number"
            elif not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in new_password):
                error = "Password must contain at least one special character"
            else:
                # Password is valid, update it
                conn.execute("UPDATE users SET password=? WHERE username=?", (new_password, session['user']))
                conn.commit()
                success = "Password updated successfully"
            
        elif action == 'update_mobile':
            mobile = request.form.get('mobile', '')
            conn.execute("UPDATE users SET mobile=? WHERE username=?", (mobile, session['user']))
            conn.commit()
            success = "Mobile number updated successfully"
        
        if success:
            return redirect('/settings?success=1')
        
    user = conn.execute("SELECT * FROM users WHERE username=?", (session['user'],)).fetchone()
    return render_template('settings.html', user=user, error=error)

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
            "SELECT customer FROM connections WHERE vendor=? ORDER BY id DESC",
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
            "SELECT vendor FROM connections WHERE customer=? ORDER BY id DESC",
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
        "SELECT username,mobile FROM users WHERE role='vendor' ORDER BY id DESC"
    ).fetchall()

    connected = conn.execute(
        "SELECT vendor FROM connections WHERE customer=? ORDER BY id DESC",
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
            "SELECT * FROM products WHERE vendor=? ORDER BY id DESC",
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
            "SELECT vendor FROM connections WHERE customer=? ORDER BY id DESC",
            (session['user'],)
        ).fetchall()

        vendor_names = [v['vendor'] for v in connected_vendors]

        if vendor_names:

            placeholders = ",".join("?" * len(vendor_names))

            query = f"""
                SELECT * FROM products
                WHERE vendor IN ({placeholders})
                ORDER BY id DESC
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
            "SELECT * FROM orders WHERE vendor=? ORDER BY id DESC",
            (session['user'],)
        ).fetchall()

    # -------------------------
    # CUSTOMER
    # -------------------------

    else:

        orders = conn.execute(
            "SELECT * FROM orders WHERE customer=? ORDER BY id DESC",
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
            "SELECT * FROM orders WHERE vendor=? ORDER BY id DESC",
            (session['user'],)
        ).fetchall()

    else:

        orders = conn.execute(
            "SELECT * FROM orders WHERE customer=? ORDER BY id DESC",
            (session['user'],)
        ).fetchall()

    return render_template(
        'delivery.html',
        orders=orders
    )
# ---------------------------------
# PAYMENTS
# ---------------------------------

@app.route('/payment/order/<int:order_id>')
def payment_checkout(order_id):
    if 'user' not in session or session.get('role') != 'customer':
        return redirect('/login')
    conn = get_db()
    o, state = _payment_order_state(conn, order_id, session['user'])
    if state == 'invalid':
        return redirect('/payments?pay=invalid')
    if state == 'blocked':
        return redirect('/payments?pay=done')
    if state == 'awaiting':
        return redirect('/payments?pay=pending')
    return render_template('payment_checkout.html', order=o)


@app.route('/payment/order/<int:order_id>/card', methods=['GET', 'POST'])
def payment_card(order_id):
    if 'user' not in session or session.get('role') != 'customer':
        return redirect('/login')
    conn = get_db()
    o, state = _payment_order_state(conn, order_id, session['user'])
    if state not in ('new', 'retry'):
        return redirect('/payments?pay=invalid')
    err = ''
    if request.method == 'POST':
        holder = (request.form.get('card_holder') or '').strip()
        pan = re.sub(r'\D', '', request.form.get('card_number') or '')
        exp = (request.form.get('expiry') or '').strip()
        cvv = (request.form.get('cvv') or '').strip()
        if len(holder) < 2:
            err = 'Enter the card holder name.'
        elif not _luhn_valid(pan):
            err = 'Invalid card number.'
        elif not _card_expiry_valid(exp):
            err = 'Invalid or expired card (use MM/YY).'
        elif not re.match(r'^\d{3,4}$', cvv):
            err = 'CVV must be 3 or 4 digits.'
        else:
            last4 = pan[-4:]
            ok = _finalize_customer_payment(
                conn,
                order_id,
                session['user'],
                o['vendor'],
                o['product_name'],
                o['price'],
                'Credit/Debit Card',
                '',
                '',
                last4,
                '',
            )
            if ok:
                return redirect('/payments?pay=success')
            err = 'Unable to record payment. Please try again.'
    return render_template('payment_card.html', order=o, error=err)


@app.route('/payment/order/<int:order_id>/upi')
def payment_upi_platforms(order_id):
    if 'user' not in session or session.get('role') != 'customer':
        return redirect('/login')
    conn = get_db()
    o, state = _payment_order_state(conn, order_id, session['user'])
    if state not in ('new', 'retry'):
        return redirect('/payments?pay=invalid')
    return render_template('payment_upi_platforms.html', order=o)


@app.route('/payment/order/<int:order_id>/upi/<platform>')
def payment_upi_flow(order_id, platform):
    if 'user' not in session or session.get('role') != 'customer':
        return redirect('/login')
    if platform not in UPI_PLATFORM_SLUGS:
        return redirect('/payments?pay=invalid')
    conn = get_db()
    o, state = _payment_order_state(conn, order_id, session['user'])
    if state not in ('new', 'retry'):
        return redirect('/payments?pay=invalid')
    label = UPI_PLATFORM_SLUGS[platform]
    return render_template(
        'payment_upi_flow.html',
        order=o,
        platform=platform,
        platform_label=label,
    )


@app.route('/payment/order/<int:order_id>/upi/<platform>/qr', methods=['GET', 'POST'])
def payment_upi_qr(order_id, platform):
    if 'user' not in session or session.get('role') != 'customer':
        return redirect('/login')
    if platform not in UPI_PLATFORM_SLUGS:
        return redirect('/payments?pay=invalid')
    conn = get_db()
    o, state = _payment_order_state(conn, order_id, session['user'])
    if state not in ('new', 'retry'):
        return redirect('/payments?pay=invalid')
    label = UPI_PLATFORM_SLUGS[platform]
    vpa = _vendor_collect_vpa(conn, o['vendor'])
    amt = _digits_only_amount(o['price'])
    uri = _build_upi_uri(vpa, o['vendor'], amt, f"{o['product_name'][:80]} — Order #{order_id}")
    qr_src = _qr_data_uri(uri)
    err = ''
    if request.method == 'POST':
        ok = _finalize_customer_payment(
            conn,
            order_id,
            session['user'],
            o['vendor'],
            o['product_name'],
            o['price'],
            'UPI',
            label,
            'QR',
            '',
            '',
        )
        if ok:
            return redirect('/payments?pay=success')
        err = 'Unable to record payment.'
    return render_template(
        'payment_upi_qr.html',
        order=o,
        platform=platform,
        platform_label=label,
        qr_src=qr_src,
        upi_uri=uri,
        amount_display=amt,
        error=err,
    )


@app.route('/payment/order/<int:order_id>/upi/<platform>/upi-id', methods=['GET', 'POST'])
def payment_upi_id(order_id, platform):
    if 'user' not in session or session.get('role') != 'customer':
        return redirect('/login')
    if platform not in UPI_PLATFORM_SLUGS:
        return redirect('/payments?pay=invalid')
    conn = get_db()
    o, state = _payment_order_state(conn, order_id, session['user'])
    if state not in ('new', 'retry'):
        return redirect('/payments?pay=invalid')
    label = UPI_PLATFORM_SLUGS[platform]
    err = ''
    if request.method == 'POST':
        u1 = (request.form.get('upi_id') or '').strip().lower()
        u2 = (request.form.get('upi_id_confirm') or '').strip().lower()
        if not u1 or not u2:
            err = 'Enter and confirm your UPI ID.'
        elif u1 != u2:
            err = 'UPI IDs do not match.'
        elif not _upi_format_valid(u1):
            err = 'Invalid UPI ID format (e.g. name@ybl).'
        else:
            masked = _mask_upi_id(u1)
            ok = _finalize_customer_payment(
                conn,
                order_id,
                session['user'],
                o['vendor'],
                o['product_name'],
                o['price'],
                'UPI',
                label,
                'UPI ID',
                '',
                masked,
            )
            if ok:
                return redirect('/payments?pay=success')
            err = 'Unable to record payment.'
    return render_template(
        'payment_upi_id.html',
        order=o,
        platform=platform,
        platform_label=label,
        error=err,
    )


@app.route('/payments', methods=['GET'])
def payments():

    if 'user' not in session:
        return redirect('/login')

    conn = get_db()

    # CUSTOMER VIEW
    if session['role'] == 'customer':
        payments = conn.execute(
            '''
            SELECT p.*, o.product_image, o.status as delivery_status, o.delivered_date 
            FROM payments p
            LEFT JOIN orders o ON p.order_id = o.id
            WHERE p.customer=?
            ORDER BY p.id DESC
            ''',
            (session['user'],)
        ).fetchall()

        orders = conn.execute(
            '''
            SELECT * FROM orders
            WHERE customer=?
            ORDER BY id DESC
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
            ORDER BY p.id DESC
            ''',
            (session['user'],)
        ).fetchall()

        orders = []

    return render_template(
        'payments.html',
        payments=payments,
        orders=orders,
        pay_notice=request.args.get('pay', ''),
    )


@app.route('/update_payment', methods=['POST'])
def update_payment():

    if 'user' not in session or session.get('role') != 'vendor':
        return redirect('/login')

    payment_id = request.form['payment_id']
    status = request.form['status']
    conn = get_db()

    # Get the payment record
    payment = conn.execute(
        "SELECT * FROM payments WHERE id=? AND vendor=?",
        (payment_id, session['user']),
    ).fetchone()
    
    if payment:
        current_time = datetime.now().strftime('%d/%m/%Y, %I:%M %p')
        
        if status in ('Payment Verified Successfully', 'Accepted'):
            conn.execute(
                '''
                UPDATE payments
                SET status=?, payment_date=?
                WHERE id=?
                ''',
                ('Accepted', current_time, payment_id)
            )
        elif status == 'Payment Not Received':
            conn.execute(
                '''
                UPDATE payments
                SET status=?, payment_date=?
                WHERE id=?
                ''',
                ('Payment Not Received', current_time, payment_id)
            )
        else:
            conn.execute(
                '''
                UPDATE payments
                SET status=?, payment_date=?
                WHERE id=?
                ''',
                (status, current_time, payment_id)
            )
        
        conn.commit()

    return redirect('/payments')


@app.route('/process_refund', methods=['POST'])
def process_refund():
    if 'user' not in session or session.get('role') != 'vendor':
        return redirect('/login')
        
    payment_id = request.form['payment_id']
    conn = get_db()
    ts = datetime.now().strftime('%d/%m/%Y, %I:%M %p')
    conn.execute(
        "UPDATE payments SET status='Refund Completed', payment_date=? WHERE id=? AND vendor=?",
        (ts, payment_id, session['user']),
    )
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
            ORDER BY id DESC
            """,
            (session['user'],)
        ).fetchall()

        reviews = conn.execute(
            "SELECT * FROM reviews ORDER BY id DESC"
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
            ORDER BY id DESC
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
        "SELECT * FROM users ORDER BY id DESC"
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
    
    # Check if order is already marked as Out Of Stock
    order = conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
    if order and order['status'] == 'Out Of Stock':
        # Cannot change status of Out Of Stock order
        conn.commit()
        return redirect('/orders')
    
    # Format delivery date in Indian format if provided
    if delivered_date:
        try:
            dt = datetime.strptime(delivered_date, '%Y-%m-%d')
            delivered_date = dt.strftime('%d/%m/%Y')
        except:
            pass
    
    if expected_delivery:
        try:
            dt = datetime.strptime(expected_delivery, '%Y-%m-%d')
            expected_delivery = dt.strftime('%d/%m/%Y')
        except:
            pass

    conn.execute(
        "UPDATE orders SET status=?, expected_delivery=?, delivered_date=? WHERE id=?",
        (status, expected_delivery, delivered_date, order_id)
    )

    if status == "Out Of Stock":
        order = conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
        existing_payment = conn.execute("SELECT * FROM payments WHERE order_id=?", (order_id,)).fetchone()
        
        # Format current time in Indian format
        current_time = datetime.now().strftime('%d/%m/%Y, %I:%M %p')
        
        if not existing_payment:
            conn.execute(
                '''
                INSERT INTO payments(
                    order_id, customer, vendor, product_name, amount, status, payment_date,
                    payment_method, upi_platform, upi_flow, card_last4, upi_masked
                )
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                ''',
                (
                    order['id'],
                    order['customer'],
                    order['vendor'],
                    order['product_name'],
                    order['price'],
                    'Out Of Stock',
                    current_time,
                    '',
                    '',
                    '',
                    '',
                    '',
                ),
            )
        else:
            conn.execute("UPDATE payments SET status='Out Of Stock', payment_date=? WHERE order_id=?", (current_time, order_id))

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
        if payment and payment['status'] in ['Completed', 'Pending Vendor Verification', 'Accepted']:
            conn.execute(
                "UPDATE payments SET status='Refund Pending', payment_date=? WHERE order_id=?",
                (datetime.now().strftime('%d/%m/%Y, %I:%M %p'), order_id),
            )
            
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
        ORDER BY id DESC
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
        ORDER BY id DESC
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
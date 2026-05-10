import traceback
from app import app
from flask import render_template

try:
    with app.test_request_context():
        # Fake data
        orders = [
            {'id': 1, 'product_name': 'Test', 'vendor': 'Vendor1', 'customer': 'Cust1', 'price': '10', 'status': 'Pending', 'product_image': '', 'expected_delivery': '', 'delivered_date': ''},
            {'id': 2, 'product_name': 'Test2', 'vendor': 'Vendor2', 'customer': 'Cust2', 'price': '20', 'status': 'Accepted', 'product_image': '', 'expected_delivery': '', 'delivered_date': ''}
        ]
        render_template('orders.html', orders=orders)
        print("Render Success!")
except Exception as e:
    traceback.print_exc()

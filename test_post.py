import traceback
from app import app

try:
    with app.test_client() as c:
        with c.session_transaction() as sess:
            sess['user'] = 'testvendor'
            sess['role'] = 'vendor'
        
        # Test edit_product
        response = c.post('/edit_product/1', data={
            'name': 'Test',
            'price': '10',
            'availability': 'In Stock'
        })
        print("Edit Product Status:", response.status_code)
        
        # Test update_order
        response = c.post('/update_order', data={
            'order_id': '1',
            'status': 'Processing',
            'expected_delivery': '2023-12-01',
            'delivered_date': ''
        })
        print("Update Order Status:", response.status_code)
        
        # Test add product
        response = c.post('/products', data={
            'name': 'New Test',
            'price': '20'
        })
        print("Add Product Status:", response.status_code)

except Exception as e:
    traceback.print_exc()

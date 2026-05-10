import traceback
from app import app

try:
    with app.test_client() as c:
        with c.session_transaction() as sess:
            sess['user'] = 'testvendor'
            sess['role'] = 'vendor'
        
        response = c.get('/orders')
        print("Vendor Orders Route Status:", response.status_code)
        if response.status_code >= 400:
            print(response.data.decode('utf-8'))
            
except Exception as e:
    traceback.print_exc()

import urllib.request
import urllib.parse
import http.cookiejar
import sys

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
urllib.request.install_opener(opener)

# login as v1
print("Logging in as v1")
opener.open('http://localhost:5000/login', data=urllib.parse.urlencode({'username':'v1','password':'123'}).encode())

# get products
try:
    r1 = opener.open('http://localhost:5000/products')
    print("Products OK")
except urllib.error.HTTPError as e:
    print("Products Error:", e.code)
    print(e.read().decode())
    sys.exit(1)

# get vendor orders
try:
    r1 = opener.open('http://localhost:5000/orders')
    print("Vendor Orders OK")
except urllib.error.HTTPError as e:
    print("Vendor Orders Error:", e.code)
    print(e.read().decode())
    sys.exit(1)

# login as c1
print("Logging in as c1")
opener.open('http://localhost:5000/login', data=urllib.parse.urlencode({'username':'c1','password':'123'}).encode())

# get customer orders
try:
    r2 = opener.open('http://localhost:5000/orders')
    print("Customer Orders OK")
except urllib.error.HTTPError as e:
    print("Customer Orders Error:", e.code)
    print(e.read().decode())
    sys.exit(1)

from flask import Flask, url_for
app = Flask(__name__)
app.config['SERVER_NAME'] = 'localhost'
with app.app_context():
    try:
        url = url_for('static', filename='')
        print("Success:", url)
    except Exception as e:
        print("Error:", repr(e))

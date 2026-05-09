from app.extensions import db
from app.models import User


def test_register_and_login(client, app):
    # Register
    r = client.post("/register", data={
        "username": "alice", "password": "supersecret1",
        "confirm": "supersecret1", "role": "customer", "mobile": "1234567",
    }, follow_redirects=True)
    assert r.status_code == 200

    with app.app_context():
        u = User.query.filter_by(username="alice").first()
        assert u is not None
        assert u.password_hash != "supersecret1"  # hashed!
        assert u.check_password("supersecret1")

    # Login
    r = client.post("/login", data={"username": "alice", "password": "supersecret1"},
                    follow_redirects=True)
    assert r.status_code == 200
    assert b"Hello, alice" in r.data


def test_login_rejects_bad_password(client, app):
    with app.app_context():
        u = User(username="bob", role="vendor")
        u.set_password("rightpassword")
        db.session.add(u); db.session.commit()
    r = client.post("/login", data={"username": "bob", "password": "wrongpass"},
                    follow_redirects=True)
    assert b"Invalid username or password" in r.data

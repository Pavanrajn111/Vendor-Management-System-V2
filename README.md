# Vendor Management System

A Flask-based vendor & customer marketplace with products, orders, payments, and reviews.

## What's new in this refactor

| Area | Before | After |
|---|---|---|
| Architecture | One 880-line `app.py` | App factory + 7 blueprints |
| ORM | Raw `sqlite3` everywhere | SQLAlchemy models with foreign keys |
| Passwords | **Plain text** 🔴 | `werkzeug` PBKDF2 hash |
| Secret key | Hardcoded `"secret123"` | `SECRET_KEY` env var |
| CSRF | None | Flask-WTF on every form |
| Forms | Manual `request.form[...]` | Validated WTForms |
| Auth | DIY session role check | Flask-Login + `@role_required` |
| Rate limiting | None | Flask-Limiter on login/register |
| Schema | `price`/`rating` as TEXT, no FKs | `Numeric`/`Integer`, FKs + cascades |
| Migrations | None | Flask-Migrate (Alembic) |
| Templates | 16 standalone HTML files with inline CSS | One `base.html` + shared `static/css/main.css` |
| Tests | None | Pytest suite |
| Config | Hardcoded | `.env` + `python-dotenv` |
| Lint | None | Ruff config in `pyproject.toml` |

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then edit SECRET_KEY
flask db init                 # first time only
flask db migrate -m "init"
flask db upgrade
flask run
```

Or just `python wsgi.py` for dev (auto-creates SQLite tables).

## Project layout

```
app/
  __init__.py        # create_app()
  config.py          # env-driven config
  extensions.py      # db, login_manager, csrf, limiter
  models.py          # SQLAlchemy: User, Product, Order, Payment, Review, Connection
  forms.py           # WTForms with validation
  decorators.py      # @role_required("vendor"|"customer")
  blueprints/
    auth.py main.py vendors.py products.py orders.py payments.py reviews.py
templates/
  base.html  + auth/  vendors/  products/  orders/  payments/  reviews/
static/css/main.css
tests/
wsgi.py
```

## Tests

```bash
pytest
```

## Production deploy

```bash
gunicorn wsgi:app
```

Set these env vars in production:
- `SECRET_KEY` — long random string
- `DATABASE_URL` — e.g. `postgresql://...` (swap SQLite for Postgres)
- `FLASK_ENV=production`

## Migrating data from the old `vendor.db`

The old DB stored plain-text passwords. Best path:
1. Export users via SQLite: `SELECT username, role, mobile FROM users;`
2. Re-import them and ask users to reset their passwords (or create new accounts).
3. Don't import the old hashes — they aren't hashes, they are the actual passwords.

## Security checklist (now satisfied)

- [x] Hashed passwords (PBKDF2)
- [x] CSRF tokens on all POST forms
- [x] Rate-limited auth endpoints
- [x] HttpOnly + SameSite cookies; Secure in prod
- [x] Role enforced server-side on every protected route
- [x] FK constraints + cascades
- [x] No DB file in git (see `.gitignore`)
- [x] Secret key from env

## Suggested next steps

- Add **pagination** to vendor/product/order lists
- Add **search/filter** (by vendor name, product name, status)
- Real **payment gateway** (Stripe/Razorpay) instead of fake status
- **Image uploads** for products (S3 or local)
- **Email notifications** on new orders / status changes
- **Admin dashboard** with charts
- **API layer** (Flask-RESTful) for a future mobile app

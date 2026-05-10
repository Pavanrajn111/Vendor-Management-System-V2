from flask import Blueprint, render_template
from flask_login import current_user, login_required
from sqlalchemy import func

from ..extensions import db
from ..models import Connection, Order, Payment, Product, Review, User

bp = Blueprint("main", __name__)


@bp.route("/dashboard")
@login_required
def dashboard():
    if current_user.is_vendor:
        stats = {
            "customers": db.session.query(func.count(Connection.id))
                .filter_by(vendor_id=current_user.id).scalar(),
            "orders": db.session.query(func.count(Order.id))
                .filter_by(vendor_id=current_user.id).scalar(),
            "reviews": db.session.query(func.count(Review.id))
                .filter_by(vendor_id=current_user.id).scalar(),
            "revenue": db.session.query(func.coalesce(func.sum(Payment.amount), 0))
                .filter_by(vendor_id=current_user.id, status="Paid").scalar(),
            "products": db.session.query(func.count(Product.id))
                .filter_by(vendor_id=current_user.id).scalar(),
        }
        connected = (db.session.query(User).join(Connection, Connection.customer_id == User.id)
                     .filter(Connection.vendor_id == current_user.id).all())
        recent_products = (Product.query
            .filter_by(vendor_id=current_user.id)
            .order_by(Product.created_at.desc())
            .limit(5)
            .all())
        return render_template("dashboard_vendor.html", stats=stats, connected=connected, recent_products=recent_products)

    stats = {
        "vendors_total": db.session.query(func.count(User.id)).filter_by(role="vendor").scalar(),
        "orders": db.session.query(func.count(Order.id))
            .filter_by(customer_id=current_user.id).scalar(),
        "payments": db.session.query(func.count(Payment.id))
            .filter_by(customer_id=current_user.id).scalar(),
    }
    connected = (db.session.query(User).join(Connection, Connection.vendor_id == User.id)
                 .filter(Connection.customer_id == current_user.id).all())
    return render_template("dashboard_customer.html", stats=stats, connected=connected)

from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from ..decorators import role_required
from ..extensions import db
from ..models import Connection, Product, Review, User

bp = Blueprint("vendors", __name__, url_prefix="/vendors")


@bp.route("/")
@login_required
@role_required("customer")
def list_vendors():
    vendors = User.query.filter_by(role="vendor").order_by(User.username).all()
    connected_ids = {c.vendor_id for c in
                     Connection.query.filter_by(customer_id=current_user.id).all()}
    return render_template("vendors/list.html", vendors=vendors, connected_ids=connected_ids)


@bp.post("/<int:vendor_id>/connect")
@login_required
@role_required("customer")
def connect(vendor_id: int):
    vendor = User.query.filter_by(id=vendor_id, role="vendor").first_or_404()
    exists = Connection.query.filter_by(customer_id=current_user.id, vendor_id=vendor.id).first()
    if not exists:
        db.session.add(Connection(customer_id=current_user.id, vendor_id=vendor.id))
        db.session.commit()
        flash(f"Connected to {vendor.username}.", "success")
    return redirect(url_for("vendors.list_vendors"))


@bp.route("/<int:vendor_id>/products")
@login_required
def vendor_products(vendor_id: int):
    vendor = User.query.filter_by(id=vendor_id, role="vendor").first_or_404()
    products = Product.query.filter_by(vendor_id=vendor.id).all()
    connected = Connection.query.filter_by(
        customer_id=current_user.id, vendor_id=vendor.id
    ).first() is not None if current_user.is_customer else False
    return render_template("vendors/products.html", vendor=vendor,
                           products=products, connected=connected)


@bp.route("/<int:vendor_id>/reviews")
@login_required
def vendor_reviews(vendor_id: int):
    vendor = User.query.filter_by(id=vendor_id, role="vendor").first_or_404()
    reviews = Review.query.filter_by(vendor_id=vendor.id).order_by(Review.created_at.desc()).all()
    return render_template("vendors/reviews.html", vendor=vendor, reviews=reviews)

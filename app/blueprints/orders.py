from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..decorators import role_required
from ..extensions import db
from ..models import Order, Payment, Product

bp = Blueprint("orders", __name__, url_prefix="/orders")


@bp.route("/")
@login_required
def index():
    if current_user.is_vendor:
        items = Order.query.filter_by(vendor_id=current_user.id).order_by(
            Order.created_at.desc()).all()
    else:
        items = Order.query.filter_by(customer_id=current_user.id).order_by(
            Order.created_at.desc()).all()
    return render_template("orders/list.html", orders=items, statuses=Order.STATUSES)


@bp.post("/place")
@login_required
@role_required("customer")
def place():
    product_id = int(request.form["product_id"])
    product = Product.query.get_or_404(product_id)
    order = Order(customer_id=current_user.id, vendor_id=product.vendor_id,
                  product_id=product.id, product_name=product.name,
                  price=product.price, status="Pending")
    db.session.add(order)
    db.session.commit()
    flash(f"Order placed for {product.name}.", "success")
    return redirect(url_for("orders.index"))


@bp.post("/<int:order_id>/status")
@login_required
@role_required("vendor")
def update_status(order_id: int):
    order = Order.query.get_or_404(order_id)
    if order.vendor_id != current_user.id:
        abort(403)
    status = request.form.get("status", "")
    if status not in Order.STATUSES:
        abort(400)
    order.status = status

    # Out-of-stock auto-creates a payment record so customer is informed
    if status == "Out Of Stock":
        existing = Payment.query.filter_by(order_id=order.id).first()
        if not existing:
            db.session.add(Payment(order_id=order.id, customer_id=order.customer_id,
                                   vendor_id=order.vendor_id, product_name=order.product_name,
                                   amount=order.price, status="Out Of Stock"))
    db.session.commit()
    flash("Order updated.", "success")
    return redirect(url_for("orders.index"))


@bp.route("/delivery")
@login_required
def delivery():
    if current_user.is_vendor:
        items = Order.query.filter_by(vendor_id=current_user.id).all()
    else:
        items = Order.query.filter_by(customer_id=current_user.id).all()
    return render_template("orders/delivery.html", orders=items)

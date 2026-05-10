from decimal import Decimal

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..decorators import role_required
from ..extensions import db
from ..models import Order, Payment

bp = Blueprint("payments", __name__, url_prefix="/payments")


@bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST" and current_user.is_customer:
        order_id = int(request.form["order_id"])
        order = Order.query.get_or_404(order_id)
        if order.customer_id != current_user.id:
            abort(403)
        if not Payment.query.filter_by(order_id=order.id).first():
            db.session.add(Payment(order_id=order.id, customer_id=order.customer_id,
                                   vendor_id=order.vendor_id,
                                   product_name=order.product_name,
                                   amount=Decimal(order.price), status="Pending"))
            db.session.commit()
            flash("Payment initiated.", "success")
        return redirect(url_for("payments.index"))

    if current_user.is_customer:
        items = Payment.query.filter_by(customer_id=current_user.id).order_by(
            Payment.created_at.desc()).all()
        unpaid_orders = (Order.query.filter_by(customer_id=current_user.id)
                         .outerjoin(Payment, Payment.order_id == Order.id)
                         .filter(Payment.id.is_(None)).all())
        return render_template("payments/customer.html",
                               payments=items, orders=unpaid_orders)

    items = Payment.query.filter_by(vendor_id=current_user.id).order_by(
        Payment.created_at.desc()).all()
    return render_template("payments/vendor.html",
                           payments=items, statuses=Payment.STATUSES)


@bp.post("/<int:payment_id>/status")
@login_required
@role_required("vendor")
def update_status(payment_id: int):
    payment = Payment.query.get_or_404(payment_id)
    if payment.vendor_id != current_user.id:
        abort(403)
    status = request.form.get("status", "")
    if status not in Payment.STATUSES:
        abort(400)
    payment.status = status
    db.session.commit()
    flash("Payment updated.", "success")
    return redirect(url_for("payments.index"))

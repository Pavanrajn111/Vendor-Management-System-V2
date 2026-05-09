from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from ..decorators import role_required
from ..extensions import db
from ..forms import ReviewForm
from ..models import Connection, Review, User

bp = Blueprint("reviews", __name__, url_prefix="/reviews")


@bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    if current_user.is_customer:
        connected_vendors = (db.session.query(User)
                             .join(Connection, Connection.vendor_id == User.id)
                             .filter(Connection.customer_id == current_user.id).all())
        form = ReviewForm()
        form.vendor_id.choices = [(v.id, v.username) for v in connected_vendors]

        if form.validate_on_submit():
            # Ensure customer is connected to that vendor
            if not Connection.query.filter_by(customer_id=current_user.id,
                                              vendor_id=form.vendor_id.data).first():
                flash("You can only review vendors you've connected with.", "danger")
            else:
                db.session.add(Review(vendor_id=form.vendor_id.data,
                                      customer_id=current_user.id,
                                      rating=form.rating.data,
                                      comment=form.comment.data))
                db.session.commit()
                flash("Review submitted.", "success")
                return redirect(url_for("reviews.index"))

        my_reviews = Review.query.filter_by(customer_id=current_user.id).order_by(
            Review.created_at.desc()).all()
        return render_template("reviews/customer.html", form=form, reviews=my_reviews)

    items = Review.query.filter_by(vendor_id=current_user.id).order_by(
        Review.created_at.desc()).all()
    return render_template("reviews/vendor.html", reviews=items)

import os
from datetime import datetime

from flask import Blueprint, abort, flash, redirect, render_template, url_for, current_app
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from ..decorators import role_required
from ..extensions import db
from ..forms import ProductForm
from ..models import Connection, Product

bp = Blueprint("products", __name__, url_prefix="/products")


def allowed_image(filename: str) -> bool:
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in current_app.config.get("ALLOWED_IMAGE_EXTENSIONS", set())


def save_product_image(file_storage, vendor_id: int) -> str | None:
    filename = secure_filename(file_storage.filename)
    if not allowed_image(filename):
        return None
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    safe_name = f"vendor{vendor_id}_{timestamp}_{filename}"
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_folder, exist_ok=True)
    path = os.path.join(upload_folder, safe_name)
    file_storage.save(path)
    return safe_name


@bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    if current_user.is_vendor:
        form = ProductForm()
        if form.validate_on_submit():
            image_filename = None
            if form.image.data:
                image_filename = save_product_image(form.image.data, current_user.id)
            db.session.add(Product(
                vendor_id=current_user.id,
                name=form.name.data,
                price=form.price.data,
                image_filename=image_filename,
            ))
            db.session.commit()
            flash("Product added.", "success")
            return redirect(url_for("products.index"))
        items = Product.query.filter_by(vendor_id=current_user.id).all()
        return render_template("products/vendor.html", products=items, form=form)

    # Customer: products from connected vendors only
    vendor_ids = [c.vendor_id for c in
                  Connection.query.filter_by(customer_id=current_user.id).all()]
    items = Product.query.filter(Product.vendor_id.in_(vendor_ids)).all() if vendor_ids else []
    return render_template("products/customer.html", products=items)


@bp.post("/<int:product_id>/delete")
@login_required
@role_required("vendor")
def delete(product_id: int):
    product = Product.query.get_or_404(product_id)
    if product.vendor_id != current_user.id:
        abort(403)
    db.session.delete(product)
    db.session.commit()
    flash("Product deleted.", "info")
    return redirect(url_for("products.index"))

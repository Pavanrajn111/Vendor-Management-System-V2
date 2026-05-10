import os
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, render_template

from .config import Config
from .extensions import csrf, db, limiter, login_manager, migrate

load_dotenv()


def create_app(config_class: type = Config) -> Flask:
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "..", "templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "..", "static"),
    )
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    @app.template_filter("relative_time")
    def relative_time(value):
        if not value:
            return ""
        now = datetime.utcnow()
        delta = now - value if now >= value else value - now
        seconds = int(delta.total_seconds())
        if seconds < 60:
            return "Just now"
        if seconds < 3600:
            minutes = seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        if seconds < 86400:
            hours = seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        days = seconds // 86400
        if days == 1:
            return "Yesterday"
        if days < 7:
            return f"{days} days ago"
        weeks = days // 7
        if weeks < 5:
            return f"{weeks} week{'s' if weeks != 1 else ''} ago"
        return value.strftime("%b %d, %Y")

    # Blueprints
    from .blueprints.auth import bp as auth_bp
    from .blueprints.main import bp as main_bp
    from .blueprints.vendors import bp as vendors_bp
    from .blueprints.products import bp as products_bp
    from .blueprints.orders import bp as orders_bp
    from .blueprints.payments import bp as payments_bp
    from .blueprints.reviews import bp as reviews_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(vendors_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(reviews_bp)

    @app.errorhandler(403)
    def forbidden(_e):
        return render_template("error.html", code=403, message="Forbidden"), 403

    @app.errorhandler(404)
    def not_found(_e):
        return render_template("error.html", code=404, message="Page not found"), 404

    # Auto-create tables on first run for SQLite dev convenience
    with app.app_context():
        db.create_all()

    return app

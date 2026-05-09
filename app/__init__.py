import os

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

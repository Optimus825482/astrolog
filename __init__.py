import os
import sys
import logging

from flask import Flask, send_from_directory, jsonify
import config
from extensions import cors, init_extensions
from flask_talisman import Talisman


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    # Config yükle
    app_config = config.get_config()
    app.config.from_object(app_config)

    if test_config is not None:
        app.config.from_mapping(test_config)

    # Blueprintleri kaydet
    from routes import bp, legal_bp

    app.register_blueprint(bp)
    app.register_blueprint(legal_bp)

    # Push Notification routes
    try:
        from routes.push_routes import push_bp

        app.register_blueprint(push_bp)
    except ImportError as e:
        logging.warning(f"Push routes yüklenemedi: {e}")

    # Admin Dashboard routes
    try:
        from routes.admin import admin_bp

        app.register_blueprint(admin_bp)
    except ImportError as e:
        logging.warning(f"Admin routes yüklenemedi: {e}")

    # Android App Links - assetlinks.json
    @app.route("/.well-known/assetlinks.json")
    def assetlinks():
        return send_from_directory(
            os.path.join(app.static_folder, ".well-known"),
            "assetlinks.json",
            mimetype="application/json",
        )

    # Filtreleri ekle
    import utils

    app.jinja_env.filters["date"] = utils.format_date
    app.jinja_env.filters["time"] = utils.format_time
    app.jinja_env.filters["safe_round"] = utils.safe_round

    # Health Check Endpoint (Docker/Coolify için)
    @app.route("/api/health")
    def health_check():
        return jsonify({
            "status": "healthy",
            "service": "orbis-backend",
            "version": "1.0.0"
        }), 200

    # Extension'ları başlat
    init_extensions(app)

    # Security headers and HTTPS enforcement
    if os.getenv("FLASK_ENV") == "production":
        # Production'da Talisman aktif - HTTP security headers
        Talisman(
            app,
            force_https=True,
            strict_transport_security=True,
            session_cookie_secure=True,
            session_cookie_httponly=True,
            session_cookie_samesite='Lax',
            content_security_policy={
                'default-src': "'self'",
                'script-src': "'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdn.tailwindcss.com",
                'style-src': "'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdn.tailwindcss.com",
                'img-src': "'self' data: https: blob:",
                'font-src': "'self' data: https:",
                'connect-src': "'self' https://fcm.googleapis.com https://*.firebaseio.com",
                'frame-src': "'none'",
            },
            force_https_permanent=True
        )
    else:
        # Development'da TLS skip et (HTTP için)
        Talisman(
            app,
            force_https=False,
            session_cookie_secure=False,
        )
    
    # CSRF protection için secret key kontrolü
    if not app.config.get("SECRET_KEY"):
        app.logger.warning("SECRET_KEY not set! Using temporary key.")
        app.config["SECRET_KEY"] = os.urandom(32)

    # Tailwind CSS varlık kontrolü (bir kez yapalım)
    tailwind_path = (
        os.path.join(app.static_folder, "css/tailwind.css")
        if app.static_folder
        else None
    )
    tailwind_exists = os.path.exists(tailwind_path) if tailwind_path else False

    @app.context_processor
    def inject_tailwind_css():
        return dict(tailwind_exists=tailwind_exists)

    return app

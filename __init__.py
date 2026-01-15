import os
import sys
import logging

# Modül yolu sorununu çözmek için ana dizini sys.path'e ekleyelim
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from flask import Flask, send_from_directory, jsonify
import config
from extensions import cors, init_extensions

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
    @app.route('/.well-known/assetlinks.json')
    def assetlinks():
        return send_from_directory(
            os.path.join(app.static_folder, '.well-known'),
            'assetlinks.json',
            mimetype='application/json'
        )
    
    # Filtreleri ekle
    import utils
    app.jinja_env.filters["date"] = utils.format_date
    app.jinja_env.filters["time"] = utils.format_time
    app.jinja_env.filters["safe_round"] = utils.safe_round
    
    # Extension'ları başlat
    init_extensions(app)
    
    @app.context_processor
    def inject_tailwind_css():
        tailwind_exists = False
        if app.static_folder:
            try:
                # Sadece varlığını kontrol et
                if os.path.exists(os.path.join(app.static_folder, 'css/tailwind.css')):
                    tailwind_exists = True
            except Exception:
                tailwind_exists = False
        return dict(tailwind_exists=tailwind_exists)
    
    return app

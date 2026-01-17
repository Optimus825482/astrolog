import os

# Uygulama factory fonksiyonunu import et
try:
    from __init__ import create_app
except ImportError:
    from app import app

    def create_app():
        return app


app = create_app()

if __name__ == "__main__":
    # Railway ve benzeri platformlar PORT env değişkenini kullanır
    port = int(os.environ.get("PORT", 5005))
    app.run(host="0.0.0.0", debug=True, port=port)

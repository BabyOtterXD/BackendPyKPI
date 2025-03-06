from app import Flask
from app.api import api_bp  # Assuming you have a valid Blueprint setup in api.py
from app import CORS

def create_app():
    app = Flask(__name__)
    CORS(app)  # Apply CORS to all routes
    app.register_blueprint(api_bp, url_prefix="/api")
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)


# python -m app.app

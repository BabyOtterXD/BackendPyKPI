from flask import Flask
from app.api import api_bp  # นำเข้า Blueprint จาก api.py

def create_app():
    app = Flask(__name__)
    # ลงทะเบียน Blueprint
    app.register_blueprint(api_bp, url_prefix="/api")
    return app

if __name__ == "__main__":
    # รันเซิร์ฟเวอร์ Flask
    app = create_app()
    app.run(debug=True)

# psql -U postgres -d template1
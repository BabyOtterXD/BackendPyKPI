from flask import Flask, request, jsonify
import psycopg2
import joblib
from pythainlp.tokenize import word_tokenize

app = Flask(__name__)

# โหลดโมเดลและ vectorizer เมื่อเริ่ม API
model = joblib.load("kpi_model.pkl")
vectorizer = joblib.load("tfidf_vectorizer.pkl")

def preprocess_text(text):
    words = word_tokenize(str(text), keep_whitespace=False)
    return " ".join(words)

# ฟังก์ชันเชื่อมต่อกับ PostgreSQL
def get_db_connection():
    conn = psycopg2.connect(
        dbname="postgres",    # ชื่อฐานข้อมูล
        user="postgres",      # ชื่อผู้ใช้
        password="123456",    # รหัสผ่าน
        host="localhost",     # host
        port="5432"           # port
    )
    return conn

def create_tables(conn):
    with conn.cursor() as cur:
        # สร้างตาราง employees
        cur.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                emp_id VARCHAR PRIMARY KEY,
                department VARCHAR
            );
        """)
        # สร้างตาราง missions พร้อม FOREIGN KEY เชื่อมกับ employees
        cur.execute("""
            CREATE TABLE IF NOT EXISTS missions (
                id SERIAL PRIMARY KEY,
                emp_id VARCHAR NOT NULL,
                mission_name VARCHAR,
                FOREIGN KEY (emp_id) REFERENCES employees(emp_id)
            );
        """)
        # สร้างตาราง kpis พร้อมเพิ่มคอลัมน์ kpi_category
        cur.execute("""
            CREATE TABLE IF NOT EXISTS kpis (
                id SERIAL PRIMARY KEY,
                mission_id INTEGER NOT NULL,
                kpi_name VARCHAR,
                kpi_category VARCHAR,
                FOREIGN KEY (mission_id) REFERENCES missions(id)
            );
        """)
        # สร้างตาราง definitions พร้อม FOREIGN KEY เชื่อมกับ kpis
        cur.execute("""
            CREATE TABLE IF NOT EXISTS definitions (
                id SERIAL PRIMARY KEY,
                kpi_id INTEGER NOT NULL,
                definition_text VARCHAR,
                weight FLOAT,
                score FLOAT,
                FOREIGN KEY (kpi_id) REFERENCES kpis(id)
            );
        """)
    conn.commit()



# if __name__ == '__main__':
#     # สร้างตาราง (ถ้ายังไม่มี)
#     conn = get_db_connection()
#     create_tables(conn)
#     conn.close()
#     app.run(debug=True)

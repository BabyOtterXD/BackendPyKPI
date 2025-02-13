import psycopg2
import joblib
from pythainlp.tokenize import word_tokenize

def preprocess_text(text):
    # ฟังก์ชันตัดคำ (tokenize)
    words = word_tokenize(str(text), keep_whitespace=False)
    return " ".join(words)

def main():
    # 1) โหลดโมเดลและ vectorizer
    model = joblib.load("kpi_model.pkl")
    vectorizer = joblib.load("tfidf_vectorizer.pkl")

    # 2) เชื่อมต่อฐานข้อมูล
    conn = psycopg2.connect(
        dbname="postgres",
        user="postgres",
        password="123456",
        host="localhost",
        port="5432"
    )
    cur = conn.cursor()

    # 3) ดึงรายการ kpi_name ที่ยังไม่มี kpi_category
    cur.execute("""
        SELECT id, kpi_name
        FROM kpis
        WHERE kpi_category IS NULL
    """)
    rows = cur.fetchall()

    # 4) วนลูปทำนายหมวดหมู่แล้วอัปเดตลง db
    for row in rows:
        kpi_id = row[0]
        kpi_name = row[1]

        # ทำนาย
        processed_text = preprocess_text(kpi_name)
        vectorized_text = vectorizer.transform([processed_text])
        predicted_category = model.predict(vectorized_text)[0]

        # อัปเดต kpi_category ในตาราง kpis
        cur.execute("""
            UPDATE kpis
            SET kpi_category = %s
            WHERE id = %s
        """, (predicted_category, kpi_id))

    conn.commit()
    cur.close()
    conn.close()
    print("✅ อัปเดต kpi_category สำเร็จ!")

if __name__ == "__main__":
    main()

import pandas as pd
import joblib
import numpy as np
from scipy.sparse import hstack
from gensim.models import FastText
from pythainlp.tokenize import word_tokenize  # ใช้ pythainlp สำหรับตัดคำไทย
import re

# 1️⃣ โหลดไฟล์ข้อมูล KPI
file_path = "../files/kpi (1).xlsx"  
df_input = pd.read_excel(file_path)

# 2️⃣ โหลดโมเดลและออบเจกต์ที่บันทึกไว้
ensemble_model = joblib.load("../models/ensemble_kpi_model.pkl")  
fasttext_model = FastText.load("../models/fasttext_model.bin")      
vectorizer = joblib.load("../models/tfidf_vectorizer.pkl")          
label_encoder = joblib.load("../models/label_encoder.pkl")          

# 3️⃣ ฟังก์ชันแยกคำด้วย `pythainlp`
def improved_tokenizer(text):
    """แยกคำไทย + อังกฤษ + ตัวเลข ให้ถูกต้อง"""
    if not isinstance(text, str) or text.strip() == "":
        return ""

    text = text.strip()

    # 1️⃣ แยกตัวเลขออกจากคำ
    text = re.sub(r"(\d+)([ก-๙a-zA-Z])", r"\1 \2", text)  # "50ครั้ง" → "50 ครั้ง"
    text = re.sub(r"([ก-๙a-zA-Z])(\d+)", r"\1 \2", text)  # "พนักงาน3คน" → "พนักงาน 3 คน"

    # 2️⃣ แยกคำภาษาอังกฤษ เช่น "CostSaving" → "Cost Saving"
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)

    # 3️⃣ แยกคำภาษาไทยโดยใช้ `pythainlp`
    words = word_tokenize(text, keep_whitespace=False)  
    text = " ".join(words)  # รวมคำใหม่หลังแยก

    return text

# 4️⃣ ตรวจสอบค่า NaN และสร้าง standardized_kpi
df_input["kpi"] = df_input["kpi"].fillna("")
df_input["standardized_kpi"] = df_input["kpi"].apply(improved_tokenizer)

# 5️⃣ ฟังก์ชันทำนาย KPI
def preprocess_and_predict(text):
    """ประมวลผลข้อความและทำนายหมวดหมู่ KPI"""
    if pd.isna(text) or text == "":
        return "ไม่ทราบ"

    # Vectorize ด้วย TF-IDF
    vectorized_text_tfidf = vectorizer.transform([text])
    
    # Tokenize และประมวลผลด้วย FastText
    tokenized_text = text.split()  # ใช้แบบที่ถูกปรับให้เหมาะสมแล้ว
    word_vectors = [fasttext_model.wv[word] for word in tokenized_text if word in fasttext_model.wv]
    
    if not word_vectors:
        vectorized_text_fasttext = np.zeros((1, fasttext_model.vector_size))
    else:
        vectorized_text_fasttext = np.mean(word_vectors, axis=0).reshape(1, -1)

    # รวมเวกเตอร์ TF-IDF และ FastText
    vectorized_text_combined = hstack([vectorized_text_tfidf, vectorized_text_fasttext])

    # ทำนายหมวดหมู่ KPI
    predicted_label = ensemble_model.predict(vectorized_text_combined.toarray())[0]
    predicted_category = label_encoder.inverse_transform([predicted_label])[0]

    return predicted_category

# 6️⃣ ใช้ฟังก์ชันทำนายกับคอลัมน์ standardized_kpi
df_input["Predicted KPI Category"] = df_input["standardized_kpi"].apply(preprocess_and_predict)

# 7️⃣ **ลบ standardized_kpi ออกจาก DataFrame ก่อนบันทึก**
df_input.drop(columns=["standardized_kpi"], inplace=True)

#  บันทึกผลลัพธ์
output_file_path = "../files/predicted_kpi_output.xlsx"
df_input.to_excel(output_file_path, index=False)

print(f"บันทึกผลลัพธ์เรียบร้อยที่: {output_file_path}")

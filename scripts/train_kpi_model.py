import pandas as pd
import joblib
from pythainlp.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# 1️⃣ โหลดข้อมูล KPI
file_path ="TrianModel.xlsx"  # ต้องมีคอลัมน์ standardized_kpi และ category
sheets = pd.read_excel(file_path, sheet_name=None) 

# รวมข้อมูลจากทุก Sheet
df_list = []
for sheet_name, df in sheets.items():
    # print(f"📄 กำลังอ่านข้อมูลจาก: {sheet_name} (จำนวน {len(df)} แถว)")
    df_list.append(df)

df = pd.concat(df_list, ignore_index=True)
# print(f"✅ โหลดข้อมูลทั้งหมดสำเร็จ! รวมได้ {len(df)} แถว")

# 2️⃣ ตัดคำภาษาไทย
def preprocess_text(text):
    words = word_tokenize(str(text), keep_whitespace=False)  # ตัดคำ
    return " ".join(words)

df["processed_kpi"] = df["KPI"].apply(preprocess_text)

# 3️⃣ แปลงข้อความเป็นตัวเลข (TF-IDF)
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(df["processed_kpi"])
y = df["KPI Category"]

# 4️⃣ แบ่งข้อมูล Train/Test
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# from imblearn.over_sampling import SMOTE

# smote = SMOTE(random_state=42)
# X_resampled, y_resampled = smote.fit_resample(X_train, y_train)

# 5️⃣ ฝึกโมเดล Naïve Bayes
# model = MultinomialNB()
# model.fit(X_train, y_train)
# model.fit(X_resampled, y_resampled)


from sklearn.ensemble import RandomForestClassifier

# # เปลี่ยนจาก Naïve Bayes เป็น Random Forest
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)
# model.fit(X_resampled, y_resampled)


# 6️⃣ ทดสอบโมเดล
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"✅ Model Accuracy: {accuracy:.2f}")

# 7️⃣ บันทึกโมเดล & Vectorizer
joblib.dump(model, "kpi_model.pkl")
joblib.dump(vectorizer, "tfidf_vectorizer.pkl")
print("✅ Model saved successfully!")

print("🔍 จำนวน KPI ในแต่ละหมวดหมู่:")
print(df["KPI Category"].value_counts())

test_kpi = ["Cost Saving Cost Saving and cost reduction per year", "ติดตาม เอกสาร รับรอง มาตรฐาน หรือ เอกสาร ที่ เกี่ยวข้อง กับ ระบบ ISO ของ ผู้ขาย Supplier ให้ได้ ของ ทุก ไตรมาส ภายใน ปี ของ ทุก ไตรมาส", "จำนวน ผู้ขาย ผู้ให้บริการ ที่ มี การใช้งาน และ ถูก ประเมิน จำนวน ผู้ขาย ผู้ให้บริการ ที่ มี การใช้งาน ประเมิน คุณภาพ เพื่อ เพิ่ม คุณภาพ และ บริการ"]
for kpi in test_kpi:
    processed_text = preprocess_text(kpi)
    vectorized_text = vectorizer.transform([processed_text])
    predicted_category = model.predict(vectorized_text)[0]
    print(f"KPI: {kpi} → Predicted Category: {predicted_category}")



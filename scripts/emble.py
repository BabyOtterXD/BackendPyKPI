import pandas as pd
import joblib
import numpy as np
import time  # Import time module for tracking execution time
from collections import Counter
from pythainlp.tokenize import word_tokenize
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from xgboost import XGBClassifier
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.preprocessing import LabelEncoder, StandardScaler
from gensim.models import FastText
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.sparse import hstack, csr_matrix
from imblearn.under_sampling import RandomUnderSampler
from imblearn.over_sampling import SMOTE  # Import SMOTE

# ⏳ Start tracking total runtime
start_time = time.time()

# 1️⃣ Load KPI Data from Excel
file_path = "../excel/TrianModel (29).xlsx"
sheets = pd.read_excel(file_path, sheet_name=None)

df_list = []
for sheet_name, df_sheet in sheets.items():
    df_list.append(df_sheet)
df = pd.concat(df_list, ignore_index=True)

# 2️⃣ Combine KPI & Definition (if available)
if "Definition" in df.columns:
    df["combined_text"] = df["KPI"].astype(str) + " " + df["Definition"].astype(str)
else:
    df["combined_text"] = df["KPI"].astype(str)

# 3️⃣ Preprocessing: Tokenization
def preprocess_text(text):
    words = word_tokenize(str(text), keep_whitespace=False)
    return ' '.join(words)

df["processed_text"] = df["combined_text"].apply(preprocess_text)
df["tokenized_text"] = df["processed_text"].apply(lambda x: x.split())

# 4️⃣ Train FastText Model
fasttext_model = FastText(sentences=df["tokenized_text"], vector_size=100, window=5, min_count=1, workers=4)

# 5️⃣ Convert Text to Vectors using FastText
def text_to_vector(words):
    word_vectors = [fasttext_model.wv[word] for word in words if word in fasttext_model.wv]
    return np.mean(word_vectors, axis=0) if word_vectors else np.zeros(100)

df["vectorized_text_fasttext"] = df["tokenized_text"].apply(text_to_vector)
X_fasttext = np.vstack(df["vectorized_text_fasttext"].values)

# 6️⃣ TF‑IDF Vectorization
vectorizer = TfidfVectorizer()
X_tfidf = vectorizer.fit_transform(df["processed_text"])

# 7️⃣ Scale FastText Features
scaler = StandardScaler()
X_fasttext_scaled = scaler.fit_transform(X_fasttext)
X_fasttext_sparse = csr_matrix(X_fasttext_scaled)

# 8️⃣ Combine TF‑IDF & FastText Features
X_combined = hstack([X_tfidf, X_fasttext_sparse])

# 9️⃣ Encode KPI Categories
label_encoder = LabelEncoder()
df["KPI Category Encoded"] = label_encoder.fit_transform(df["KPI Category"])
y = df["KPI Category Encoded"]

# 🔟 Split Data into Train/Test Sets
X_train, X_test, y_train, y_test = train_test_split(X_combined, y, test_size=0.2, random_state=42)

# 1️⃣1️⃣ Apply Undersampling
X_train_dense = X_train.toarray()
class_counts = Counter(y_train)
sampling_strategy = {cls: max(count, 3) for cls, count in class_counts.items()}  # Ensure at least 3 samples per class

undersample = RandomUnderSampler(sampling_strategy=sampling_strategy, random_state=42)
X_train_under, y_train_under = undersample.fit_resample(X_train_dense, y_train)

print("Distribution after Undersampling:")
print(pd.Series(y_train_under).value_counts())

# 1️⃣2️⃣ Apply SMOTE (Re-added)
smote = SMOTE(sampling_strategy="auto", random_state=42)
X_train_res, y_train_res = smote.fit_resample(X_train_under, y_train_under)

print("Distribution after SMOTE:")
print(pd.Series(y_train_res).value_counts())

# ⏳ Track time for Data Processing
data_processing_time = time.time()
print(f"✅ Data Processing Time: {data_processing_time - start_time:.2f} seconds")

# 🔹 ใช้ SVC() แทน CalibratedClassifierCV
svc_model = SVC(kernel='linear', C=1.5, probability=True)

# 🔹 สร้าง VotingClassifier ใหม่
base_models = [
    ('rf', RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42, class_weight='balanced')),
    ('svm', svc_model),  # ✅ ใช้ SVC() แทน CalibratedClassifierCV
    ('xgb', XGBClassifier(eval_metric="mlogloss", learning_rate=0.05, max_depth=6)),
    ('logreg', LogisticRegression(max_iter=2000, class_weight='balanced')),
    ('gnb', GaussianNB())
]

ensemble_model = VotingClassifier(estimators=base_models, voting='soft', weights=[1, 2, 1, 2, 1])

# 🔥 ฝึกโมเดล
ensemble_model.fit(X_train_res, y_train_res)

# ⏳ Track time for Model Training
train_time = time.time()
print(f"✅ Training Time: {train_time - data_processing_time:.2f} seconds")

# 1️⃣4️⃣ Evaluate Model on Test Set
X_test_array = X_test.toarray()
y_pred = ensemble_model.predict(X_test_array)

# ⏳ Track time for Model Testing
test_time = time.time()
print(f"✅ Testing Time: {test_time - train_time:.2f} seconds")

accuracy = accuracy_score(y_test, y_pred)
print(f"✅ Ensemble Model Accuracy: {accuracy:.2f}")
print("\nClassification Report:")
print(classification_report(y_test, y_pred))
print("Confusion Matrix:")
print(confusion_matrix(y_test, y_pred))

# 1️⃣5️⃣ Save Model & Objects
save_start_time = time.time()
joblib.dump(ensemble_model, "ensemble_kpi_model.pkl")
fasttext_model.save("fasttext_model.bin")
joblib.dump(vectorizer, "tfidf_vectorizer.pkl")
joblib.dump(label_encoder, "label_encoder.pkl")
joblib.dump(scaler, "fasttext_scaler.pkl")
save_end_time = time.time()

print(f"✅ Model Saving Time: {save_end_time - save_start_time:.2f} seconds")

# 📌 Total Runtime
total_time = time.time() - start_time
print(f"🚀 Total Runtime: {total_time:.2f} seconds")

# 1️⃣6️⃣ Model Prediction Test
test_kpi = [
    "พนักงาน จัดซื้อ จะ ต้อง มี การ ตรวจ เยี่ยม Supplier รวม ให้ได้ ราย ภายใน ปี",
    "Able to manage all projects under responsibility Number of projects that can be managed",
    "จำนวน ครั้ง ของ ความผิดพลาด ใน การนำ ข้อมูล คีย์ เข้า ระบบ EBMS"
]

print("\n🔍 Testing Ensemble Model")
for kpi in test_kpi:
    processed_text = preprocess_text(kpi)
    vectorized_text_tfidf = vectorizer.transform([processed_text])

    tokenized_text = processed_text.split()
    vectorized_text_fasttext = text_to_vector(tokenized_text)
    vectorized_text_fasttext_scaled = scaler.transform(vectorized_text_fasttext.reshape(1, -1))
    vectorized_text_fasttext_sparse = csr_matrix(vectorized_text_fasttext_scaled)

    vectorized_text_combined = hstack([vectorized_text_tfidf, vectorized_text_fasttext_sparse])

    predicted_label = ensemble_model.predict(vectorized_text_combined.toarray())[0]
    predicted_category = label_encoder.inverse_transform([predicted_label])[0]
    print(f"KPI: {kpi} → Predicted Category: {predicted_category}")

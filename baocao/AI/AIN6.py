from flask import Flask, request, jsonify, send_from_directory
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
import os
import random
import difflib
import platform
import psutil
import socket
import getpass
import requests
from bs4 import BeautifulSoup
import numpy as np

import greeting
import creator
import bye
import story
import math_logic

app = Flask(__name__)

# ------------------ Hàm xử lý văn bản ------------------
def clean_text(text):
    return text.lower().strip()

# ------------------ Dữ liệu offline ------------------
training_sentences = [clean_text(s) for s in greeting.training_sentences
                      + story.training_sentences
                      + creator.training_sentences
                      + bye.training_sentences]
training_labels = ["offline"] * len(training_sentences)
responses = {}
responses.update(greeting.responses)
responses.update(story.responses)
responses.update(creator.responses)
responses.update(bye.responses)

# ------------------ Log câu chưa học ------------------
def log_unlearned(sentence: str, label="unknown"):
    sentence = sentence.strip()
    if not sentence:
        return
    file_path = "unlearned.txt"
    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("DANH SÁCH CÂU CHƯA HỌC:\n")
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
    if not any(sentence in line for line in lines):
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(f"{sentence}||{label}\n")
        print(f"📝 Đã lưu câu mới vào unlearned.txt: {sentence}||{label}")

# ------------------ Nạp câu chưa học ------------------
def load_unlearned():
    file_path = "unlearned.txt"
    new_sentences = []
    new_labels = []
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
        for line in lines[1:]:
            if "||" in line:
                sentence, label = line.split("||", 1)
                new_sentences.append(clean_text(sentence))
                new_labels.append(label)
    return new_sentences, new_labels

# ------------------ Fuzzy match ------------------
def fuzzy_match(sentence, choices, cutoff=0.6):
    matches = difflib.get_close_matches(sentence, choices, n=1, cutoff=cutoff)
    return matches[0] if matches else None

# ------------------ Thông tin hệ thống ------------------
def system_info():
    info = {}
    info['OS'] = f"{platform.system()} {platform.release()} ({platform.version()})"
    info['Architecture'] = platform.machine()
    info['Processor'] = platform.processor()
    info['CPU Cores'] = psutil.cpu_count(logical=False)
    info['Logical CPUs'] = psutil.cpu_count(logical=True)
    info['RAM'] = f"{round(psutil.virtual_memory().total / (1024**3), 2)} GB"
    info['Hostname'] = socket.gethostname()
    info['IP Address'] = socket.gethostbyname(socket.gethostname())
    info['User'] = getpass.getuser()
    return info

# ------------------ Load câu chưa học và huấn luyện offline ------------------
new_sentences, new_labels = load_unlearned()
training_sentences += new_sentences
training_labels += new_labels

# Đồng bộ số lượng
min_len = min(len(training_sentences), len(training_labels))
training_sentences = training_sentences[:min_len]
training_labels = training_labels[:min_len]

# Huấn luyện mô hình Naive Bayes offline
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(training_sentences)
model = MultinomialNB()
model.fit(X, training_labels)

print(f"✅ Mô hình offline đã được huấn luyện với {len(training_sentences)} câu, bao gồm {len(new_sentences)} câu chưa học")

# ------------------ Fetch website theo topic ------------------
topic_urls = {
    "AI": ["https://en.wikipedia.org/wiki/Artificial_intelligence"],
    "Toán học": ["https://en.wikipedia.org/wiki/Mathematics"],
    "Lịch sử": ["https://en.wikipedia.org/wiki/History"],
    "Thể thao": ["https://en.wikipedia.org/wiki/Sport"],
    "Tin tức": ["https://en.wikipedia.org/wiki/World_news"]
}

topic_chunks = {}       # lưu các đoạn văn theo topic
topic_vectorizers = {}  # vectorizer riêng cho mỗi topic
topic_X = {}            # ma trận TF-IDF cho mỗi topic

def fetch_website_text(url):
    try:
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        text = soup.get_text(separator=" ")
        words = text.split()
        chunk_size = 50
        chunks = [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]
        return chunks
    except Exception as e:
        print("❌ Lỗi khi đọc website:", e)
        return []

# Fetch từng topic
for topic, urls in topic_urls.items():
    all_chunks = []
    for url in urls:
        chunks = fetch_website_text(url)
        all_chunks += chunks
    topic_chunks[topic] = all_chunks
    vectorizer_topic = TfidfVectorizer()
    if all_chunks:
        X_topic = vectorizer_topic.fit_transform(all_chunks)
    else:
        X_topic = None
    topic_vectorizers[topic] = vectorizer_topic
    topic_X[topic] = X_topic
    print(f"[INFO] Topic '{topic}' nạp {len(all_chunks)} chunks.")

# ------------------ Cosine similarity ------------------
def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def answer_from_online_topics(question):
    best_score = 0
    best_answer = None
    for topic, chunks in topic_chunks.items():
        if not chunks or topic_X[topic] is None:
            continue
        q_vec = topic_vectorizers[topic].transform([question])
        scores = (topic_X[topic] @ q_vec.T).toarray().ravel()
        idx = np.argmax(scores)
        score = scores[idx]
        if score > best_score:
            best_score = score
            best_answer = chunks[idx]
    if best_score < 0.1:
        return "Mình chưa tìm được thông tin từ online."
    return best_answer

# ------------------ Routes ------------------
@app.route("/")
def home():
    web_dir = r"D:\git\AI_chat_box\baocao\AI\web"
    return send_from_directory(web_dir, "index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_input = clean_text(data.get("message", ""))
    reply = "Mình chưa hiểu câu này."  # default fallback

    # Kiểm tra toán học
    math_result = math_logic.try_math(user_input)
    if math_result:
        reply = math_result
        return jsonify({"response": reply})

    # Kiểm tra thông tin hệ thống
    if any(keyword in user_input for keyword in ["thông tin máy", "cấu hình", "system info", "máy"]):
        info = system_info()
        reply = "\n".join([f"{k}: {v}" for k, v in info.items()])
        return jsonify({"response": reply})

    # --- Offline: Fuzzy match ---
    match = fuzzy_match(user_input, training_sentences)
    if match:
        idx = training_sentences.index(match)
        predicted_label = training_labels[idx]
        reply = random.choice(responses.get(predicted_label, [reply]))
    else:
        # Dùng Naive Bayes dự đoán
        X_test = vectorizer.transform([user_input])
        probs = model.predict_proba(X_test)[0]
        max_prob = max(probs)
        predicted_label = model.classes_[probs.argmax()]

        if max_prob < 0.5:
            # fallback: tìm trong online theo topic
            reply = answer_from_online_topics(user_input)
            log_unlearned(user_input, label="online")
        else:
            reply = random.choice(responses.get(predicted_label, [reply]))

    print(f"[DEBUG] input: {user_input}, label: {predicted_label}")
    return jsonify({"response": reply})

# ------------------ Chạy server ------------------
if __name__ == "__main__":
    print("Chatbot AAIN6 đang hoạt động!")
    print("🌐 Mở trình duyệt và vào: http://127.0.0.1:5000")
    app.run(port=5000)

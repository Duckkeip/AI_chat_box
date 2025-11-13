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

import greeting
import creator
import bye
import story
import math_logic

app = Flask(__name__)

def clean_text(text):
    return text.lower().strip()

# ------------------ Chuẩn bị dữ liệu ban đầu ------------------
training_sentences = [clean_text(s) for s in greeting.training_sentences
                      + story.training_sentences
                      + creator.training_sentences
                      + bye.training_sentences]
training_labels = greeting.training_labels + story.training_labels + creator.training_labels + bye.training_labels

if len(training_sentences) != len(training_labels):
    min_len = min(len(training_sentences), len(training_labels))
    training_sentences = training_sentences[:min_len]
    training_labels = training_labels[:min_len]

responses = {}
responses.update(greeting.responses)
responses.update(story.responses)
responses.update(creator.responses)
responses.update(bye.responses)

# ------------------ Hàm log câu chưa học ------------------
def log_unlearned(sentence: str):
    sentence = sentence.strip()
    if not sentence:
        return
    file_path = "unlearned.txt"
    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("DANH SÁCH CÂU CHƯA HỌC:\n")
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
    # Lưu câu + nhãn tạm "unknown" nếu chưa tồn tại
    if not any(sentence in line for line in lines):
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(f"{sentence}||unknown\n")
        print(f"📝 Đã lưu câu mới vào unlearned.txt: {sentence}")

# ------------------ Hàm nạp câu chưa học ------------------
def load_unlearned():
    file_path = "unlearned.txt"
    new_sentences = []
    new_labels = []
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
        for line in lines[1:]:  # bỏ dòng tiêu đề
            if "||" in line:
                sentence, label = line.split("||", 1)
                new_sentences.append(clean_text(sentence))
                new_labels.append(label)
    return new_sentences, new_labels

# ------------------ Hàm fuzzy match ------------------
def fuzzy_match(sentence, choices, cutoff=0.8):
    matches = difflib.get_close_matches(sentence, choices, n=1, cutoff=cutoff)
    return matches[0] if matches else None

# ------------------ Hàm lấy thông tin hệ thống ------------------
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

# ------------------ Nạp câu chưa học và huấn luyện mô hình ------------------
new_sentences, new_labels = load_unlearned()
training_sentences += new_sentences
training_labels += new_labels

vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(training_sentences)
model = MultinomialNB()
model.fit(X, training_labels)
print(f"✅ Mô hình đã được huấn luyện với {len(training_sentences)} câu, bao gồm {len(new_sentences)} câu chưa học")

# ------------------ Routes ------------------
@app.route("/")
def home():
    web_dir = r"E:\pycode\baocao\AI\web"
    return send_from_directory(web_dir, "index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_input = clean_text(data.get("message", ""))

    # Kiểm tra toán học
    math_result = math_logic.try_math(user_input)
    if math_result:
        return jsonify({"response": math_result})

    # Kiểm tra thông tin thiết bị
    if any(keyword in user_input for keyword in ["thông tin máy", "cấu hình", "system info", "máy"]):
        info = system_info()
        reply = "\n".join([f"{k}: {v}" for k, v in info.items()])
        return jsonify({"response": reply})

    # Fuzzy match
    match = fuzzy_match(user_input, training_sentences, cutoff=0.6)
    if match:
        idx = training_sentences.index(match)
        predicted_label = training_labels[idx]
        reply = random.choice(responses.get(predicted_label, ["Mình chưa hiểu câu này."]))
    else:
        X_test = vectorizer.transform([user_input])
        probs = model.predict_proba(X_test)[0]
        max_prob = max(probs)
        predicted_label = model.classes_[probs.argmax()]

        if max_prob < 0.5:
            reply = "Mình chưa hiểu câu này, bạn có thể nói lại không?"
            log_unlearned(user_input)
        else:
            reply = random.choice(responses.get(predicted_label, ["Mình chưa hiểu câu này."]))
            # Nếu nhãn không có response, coi như chưa học
            if predicted_label not in responses:
                log_unlearned(user_input)

    print(f"[DEBUG] input: {user_input}, label: {predicted_label}")
    return jsonify({"response": reply})

# ------------------ Chạy server ------------------
if __name__ == "__main__":
    print("Chatbot AAIN6 đang hoạt động!")
    print("🌐 Mở trình duyệt và vào: http://127.0.0.1:5000")
    app.run(port=5000)

from flask import Flask, request, jsonify, send_from_directory
import os
import requests
import json
import time
from typing import List, Dict, Any
import firebase_admin
from firebase_admin import credentials, firestore, auth

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'

try:
    cred = credentials.Certificate('firebaseConfig.json')
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("✅ Firebase Admin SDK initialized successfully")
except Exception as e:
    print(f"❌ Firebase initialization error: {e}")
    db = None

GEMINI_API_KEY = "AIzaSyAZKgQBRoR6akrk0nTjhvHVNSgNJTQkE0o"
GEMINI_ENDPOINTS = [
    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}",
    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent?key={GEMINI_API_KEY}",
]

def clean_text(text: str) -> str:
    return text.lower().strip()

def save_message_to_firestore(user_id: str, user_message: str, bot_reply: str, source: str, confidence: float):
    if not db:
        return False
    try:
        doc_ref = db.collection('chat_history').document()
        doc_ref.set({
            'user_id': user_id,
            'user_message': user_message,
            'bot_reply': bot_reply,
            'source': source,
            'confidence': confidence,
            'timestamp': firestore.SERVER_TIMESTAMP
        })
        return True
    except Exception as e:
        print(f"❌ Error saving to Firestore: {e}")
        return False

def get_user_history(user_id: str, limit: int = 20):
    if not db:
        return []
    try:
        docs = db.collection('chat_history') \
            .where('user_id', '==', user_id) \
            .order_by('timestamp', direction=firestore.Query.DESCENDING) \
            .limit(limit) \
            .stream()
        history = []
        for doc in docs:
            data = doc.to_dict()
            history.append({
                'user': data.get('user_message', ''),
                'bot': data.get('bot_reply', ''),
                'source': data.get('source', ''),
                'confidence': data.get('confidence'),
                'timestamp': data.get('timestamp')
            })
        return list(reversed(history))
    except Exception as e:
        print(f"❌ Error loading history: {e}")
        return []

def clear_user_history(user_id: str):
    if not db:
        return False
    try:
        docs = db.collection('chat_history').where('user_id', '==', user_id).stream()
        batch = db.batch()
        count = 0
        for doc in docs:
            batch.delete(doc.reference)
            count += 1
        if count > 0:
            batch.commit()
            print(f"✅ Deleted {count} messages for user {user_id}")
        return True
    except Exception as e:
        print(f"❌ Error clearing history: {e}")
        return False

def format_history_for_gemini(user_message: str, history: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    gemini_contents = []
    for item in history:
        if item.get("user"):
            gemini_contents.append({
                "role": "user",
                "parts": [{"text": item["user"]}]
            })
        if item.get("bot"):
            gemini_contents.append({
                "role": "model",
                "parts": [{"text": item["bot"]}]
            })
    gemini_contents.append({
        "role": "user",
        "parts": [{"text": user_message}]
    })
    return gemini_contents[-30:]

def call_gemini_api(user_message: str, history: List[Dict[str, str]]) -> (str | None, str):
    if not GEMINI_API_KEY or "YOUR_GEMINI_API_KEY_HERE" in GEMINI_API_KEY:
        return None, "no_api_key"
    max_retries = 3
    base_delay = 1
    API_TIMEOUT = 10
    gemini_contents = format_history_for_gemini(user_message, history)
    for endpoint in GEMINI_ENDPOINTS:
        for attempt in range(max_retries):
            try:
                system_instruction = "Bạn là một trợ lý ảo hữu ích. Hãy duy trì ngữ cảnh dựa trên lịch sử hội thoại và trả lời ngắn gọn, thân thiện bằng tiếng Việt."
                payload = {
                    "contents": gemini_contents,
                    "systemInstruction": {"parts": [{"text": system_instruction}]},
                    "generationConfig": {"temperature": 0.7, "maxOutputTokens": 1024, "topP": 0.8, "topK": 40}
                }
                response = requests.post(endpoint, headers={"Content-Type": "application/json"}, data=json.dumps(payload), timeout=API_TIMEOUT)
                if response.status_code == 200:
                    data = response.json()
                    if "candidates" in data and len(data["candidates"]) > 0:
                        candidate = data["candidates"][0]
                        text_part = candidate.get("content", {}).get("parts", [{}])[0].get("text", "")
                        bot_reply = text_part.strip()
                        if bot_reply:
                            return bot_reply, "gemini"
                        else:
                            break
                    else:
                        break
                elif response.status_code in [429, 503]:
                    if attempt < max_retries - 1:
                        time.sleep(base_delay * (2 ** attempt))
                        continue
                    else:
                        break
                else:
                    print(f"Gemini API Error {response.status_code}: {response.text}")
                    break
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    time.sleep(base_delay * (2 ** attempt))
                    continue
                else:
                    break
            except Exception as e:
                print(f"Exception calling Gemini: {e}")
                break
    return None, "all_endpoints_failed"

@app.route("/")
def home():
    web_dir = os.path.join(os.getcwd(), "web")
    if os.path.exists(web_dir) and os.path.exists(os.path.join(web_dir, "index.html")):
        return send_from_directory(web_dir, "index.html")
    else:
        return "Chatbot Server is running.", 200

@app.route("/login.html")
def login_page():
    web_dir = os.path.join(os.getcwd(), "web")
    return send_from_directory(web_dir, "login.html")

@app.route("/firebase-config.js")
def firebase_config():
    web_dir = os.path.join(os.getcwd(), "web")
    return send_from_directory(web_dir, "firebase-config.js")

@app.route("/verify_token", methods=["POST"])
def verify_token():
    data = request.get_json()
    id_token = data.get("idToken")
    if not id_token:
        return jsonify({"error": "No token provided"}), 401
    try:
        decoded_token = auth.verify_id_token(id_token)
        user_id = decoded_token['uid']
        email = decoded_token.get('email', '')
        name = decoded_token.get('name', email.split('@')[0])
        return jsonify({"success": True, "user": {"uid": user_id, "email": email, "name": name}})
    except Exception as e:
        print(f"❌ Token verification error: {e}")
        return jsonify({"error": "Invalid token"}), 401

@app.route("/get_history", methods=["POST"])
def get_history():
    data = request.get_json()
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "No user_id provided"}), 400
    history = get_user_history(user_id, limit=40)
    return jsonify({"history": history})

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_input = clean_text(data.get("message", ""))
    user_id = data.get("user_id", "anonymous")
    current_history = data.get("history", [])
    if not user_input:
        return jsonify({"response": "Bạn chưa nhập câu hỏi.", "source": "system", "confidence": None})
    gemini_reply, gemini_source = call_gemini_api(user_input, current_history)
    if gemini_reply and gemini_source == "gemini":
        reply = gemini_reply
        source = "gemini"
        confidence = 0.85
    else:
        if gemini_source == "no_api_key":
            reply = "Xin lỗi, mình không thể trả lời câu hỏi phức tạp này vì API Key chưa được cấu hình."
            source = "api_error"
            confidence = None
        else:
            reply = "Xin lỗi, mình chưa hiểu câu này lắm. Bạn có thể diễn đạt lại không?"
            source = "unknown"
            confidence = None
    save_message_to_firestore(user_id, user_input, reply, source, float(confidence) if confidence else 0)
    return jsonify({"response": reply, "source": source, "confidence": float(confidence) if confidence else None})

@app.route("/clear_history", methods=["POST"])
def clear_history():
    data = request.get_json()
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "No user_id provided"}), 400
    success = clear_user_history(user_id)
    return jsonify({"success": success})

if __name__ == "__main__":
    print("=" * 60)
    print("Chatbot AAIN6 với Firebase Authentication")
    print("=" * 60)
    print(f"🔑 Gemini API: {'✅ CONFIGURED' if GEMINI_API_KEY else '❌ NOT CONFIGURED'}")
    print(f"🔥 Firebase: {'✅ CONNECTED' if db else '❌ NOT CONNECTED'}")
    print("=" * 60)

    app.run(
        host="0.0.0.0",
        port=5001,
        debug=True,
        use_reloader=False
    )

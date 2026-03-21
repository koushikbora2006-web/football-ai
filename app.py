from flask import Flask, render_template, request, jsonify
import json
from datetime import datetime
import os
import google.generativeai as genai

app = Flask(__name__)

# -----------------------------
# Gemini API (FIXED ✅)
# -----------------------------
genai.configure(api_key=os.getenv("AIzaSyB16m-xIonmonMQRQLlzJqZ3phRgl1RcHo"))
model = genai.GenerativeModel("gemini-2.5-flash")

CHAT_FILE = "chat_history.json"

# -----------------------------
# AI Prompt
# -----------------------------
FOOTBALL_DOMAIN_PROMPT = """
You are Football AI ⚽, a professional football analyst.

Rules:
- Only answer football related questions.
- Topics allowed: teams, players, leagues, world cup, tactics, history.
- Use bullet points if needed.
- Be concise and clear.

At the end suggest 3 related football questions.
"""

# -----------------------------
# Helper Functions
# -----------------------------

def load_chats():
    if os.path.exists(CHAT_FILE):
        try:
            with open(CHAT_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print("Load error:", e)
            return []
    return []

def save_chats(chats):
    try:
        with open(CHAT_FILE, "w") as f:
            json.dump(chats, f, indent=4)
    except Exception as e:
        print("Save error:", e)

# -----------------------------
# Conversation Memory
# -----------------------------

def get_memory(limit=5):
    chats = load_chats()
    memory = ""

    for chat in chats[-limit:]:
        memory += f"User: {chat['user_message']}\n"
        memory += f"Bot: {chat['bot_reply']}\n"

    return memory

# -----------------------------
# Routes
# -----------------------------

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/history", methods=["GET"])
def history():
    return jsonify(load_chats())

@app.route("/search", methods=["GET"])
def search_chat():
    query = request.args.get("q", "").lower()
    chats = load_chats()

    results = [
        chat for chat in chats
        if query in chat["user_message"].lower()
    ]

    return jsonify(results)

# -----------------------------
# Suggestions (SAFE)
# -----------------------------

def generate_suggestions(question):
    prompt = f"""
Suggest 3 short football related questions similar to:
{question}

Return only the questions.
"""
    try:
        res = model.generate_content(prompt)
        text = getattr(res, "text", "")
        return [q.strip() for q in text.split("\n") if q.strip()][:3]
    except Exception as e:
        print("Suggestion error:", e)
        return []

# -----------------------------
# Chat API (FIXED ✅)
# -----------------------------

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        user_message = data.get("message", "")

        memory = get_memory()

        prompt = f"""
{FOOTBALL_DOMAIN_PROMPT}

Conversation:
{memory}

User Question:
{user_message}

At the end write:
Suggested Football Questions:
- question
- question
- question
"""

        response = model.generate_content(prompt)
        text = getattr(response, "text", "Sorry, AI failed to respond.")

        answer = text
        suggestions = []

        if "Suggested Football Questions:" in text:
            parts = text.split("Suggested Football Questions:")
            answer = parts[0].strip()

            suggestions = [
                q.replace("-", "").replace("*", "").strip()
                for q in parts[1].split("\n")
                if q.strip()
            ][:3]

        now = datetime.now()

        chat_entry = {
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "user_message": user_message,
            "bot_reply": answer
        }

        chats = load_chats()
        chats.append(chat_entry)
        save_chats(chats)

        return jsonify({
            "reply": answer,
            "suggestions": suggestions
        })

    except Exception as e:
        print("CHAT ERROR:", e)
        return jsonify({"error": str(e)}), 500

# -----------------------------
# Delete Chat
# -----------------------------

@app.route("/delete", methods=["POST"])
def delete_chat():
    data = request.get_json()
    user_message = data.get("user_message")
    time = data.get("time")

    chats = load_chats()

    updated_chats = [
        chat for chat in chats
        if not (chat["user_message"] == user_message and chat["time"] == time)
    ]

    save_chats(updated_chats)
    return jsonify({"status": "deleted"})

# -----------------------------
# Rename Chat
# -----------------------------

@app.route("/rename", methods=["POST"])
def rename_chat():
    data = request.get_json()

    old_message = data.get("old_message")
    time = data.get("time")
    new_name = data.get("new_name")

    chats = load_chats()

    for chat in chats:
        if chat["user_message"] == old_message and chat["time"] == time:
            chat["user_message"] = new_name

    save_chats(chats)
    return jsonify({"status": "renamed"})

# -----------------------------
# Render Entry Point (CRITICAL FIX ✅)
# -----------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

from flask import Flask, render_template, request, jsonify
import json
from datetime import datetime
import os
import google.generativeai as genai

app = Flask(__name__)

# -----------------------------
# Gemini API
# -----------------------------

genai.configure(api_key="YOUR API KEY")
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
        except json.JSONDecodeError:
            return []
    return []

def save_chats(chats):
    with open(CHAT_FILE, "w") as f:
        json.dump(chats, f, indent=4)

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

# -----------------------------
# Get Chat History
# -----------------------------

@app.route("/history", methods=["GET"])
def history():
    chats = load_chats()
    return jsonify(chats)

# -----------------------------
# Chat Search API
# -----------------------------

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
# Smart Suggestions
# -----------------------------

def generate_suggestions(question):

    prompt = f"""
Suggest 3 short football related questions similar to:
{question}

Return only the questions.
"""

    try:
        res = model.generate_content(prompt)

        suggestions = res.text.split("\n")

        return suggestions[:3]

    except:
        return []



# -----------------------------
# Chat API
# -----------------------------

@app.route("/chat", methods=["POST"])
def chat():

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

    try:

        response = model.generate_content(prompt)

        text = response.text

        # Split answer and suggestions
        answer = text
        suggestions = []

        if "Suggested Football Questions:" in text:

            parts = text.split("Suggested Football Questions:")

            answer = parts[0].strip()

            suggestions = [
                q.replace("-", "").replace("*","").strip()
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
        return jsonify({"error": str(e)})

    # Conversation Memory
    memory = get_memory()

    prompt = f"""
{FOOTBALL_DOMAIN_PROMPT}

Conversation:
{memory}

User Question:
{user_message}
"""

    try:

        response = model.generate_content(prompt)

        bot_reply = response.text if response.text else "No response from AI"

        now = datetime.now()

        chat_entry = {
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "user_message": user_message,
            "bot_reply": bot_reply
        }

        chats = load_chats()
        chats.append(chat_entry)

        save_chats(chats)

        suggestions = generate_suggestions(user_message)

        return jsonify({
            "reply": bot_reply,
            "suggestions": suggestions
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -----------------------------
# DELETE CHAT API
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
# RENAME CHAT API
# -----------------------------

@app.route("/rename", methods=["POST"])
def rename_chat():

    data = request.json

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
# Run App
# -----------------------------

if __name__ == "__main__":
    app.run(debug=True)

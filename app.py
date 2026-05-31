from flask import Flask, render_template, request, jsonify
from google import genai
import json
from datetime import datetime
import os

app = Flask(__name__)

# =========================================
# GEMINI API SETUP
# =========================================

# OPTION 1 (Recommended)
# Set environment variable:
# Windows CMD:
# set GEMINI_API_KEY=your_api_key

API_KEY = "PASTE_YOUR_REAL_GEMINI_API_KEY_HERE"

# OPTION 2 (Quick Testing)
# Uncomment below and paste your key directly
# API_KEY = "YOUR_GEMINI_API_KEY"

if not API_KEY:
    raise ValueError("GEMINI_API_KEY is missing")

# Create Gemini client
client = genai.Client(api_key=API_KEY)

# =========================================
# CHAT STORAGE FILE
# =========================================

CHAT_FILE = "chat_history.json"

# =========================================
# FOOTBALL AI SYSTEM PROMPT
# =========================================

FOOTBALL_DOMAIN_PROMPT = """
You are Football AI ⚽, a professional football analyst.

RULES:
- Only answer football related questions.
- Allowed topics:
  teams, players, leagues, world cup,
  tactics, transfers, football history.
- Keep answers concise and clean.
- Use bullet points when needed.

At the end suggest 3 football questions.
"""

# =========================================
# HELPER FUNCTIONS
# =========================================

def load_chats():

    if os.path.exists(CHAT_FILE):

        try:
            with open(CHAT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)

        except Exception as e:
            print("Load Error:", e)
            return []

    return []


def save_chats(chats):

    try:
        with open(CHAT_FILE, "w", encoding="utf-8") as f:
            json.dump(chats, f, indent=4)

    except Exception as e:
        print("Save Error:", e)


def get_memory(limit=5):

    chats = load_chats()

    memory = ""

    for chat in chats[-limit:]:

        memory += f"User: {chat['user_message']}\n"
        memory += f"Bot: {chat['bot_reply']}\n"

    return memory

# =========================================
# HOME PAGE
# =========================================

@app.route("/")
def home():
    return render_template("index.html")

# =========================================
# CHAT HISTORY
# =========================================

@app.route("/history", methods=["GET"])
def history():
    return jsonify(load_chats())

# =========================================
# SEARCH CHAT
# =========================================

@app.route("/search", methods=["GET"])
def search_chat():

    query = request.args.get("q", "").lower()

    chats = load_chats()

    results = [

        chat for chat in chats

        if query in chat["user_message"].lower()

    ]

    return jsonify(results)

# =========================================
# CHAT API
# =========================================

@app.route("/chat", methods=["POST"])
def chat():

    try:

        data = request.get_json()

        if not data:
            return jsonify({
                "error": "No JSON data received"
            }), 400

        user_message = data.get("message", "").strip()

        if not user_message:
            return jsonify({
                "error": "Message is empty"
            }), 400

        # Conversation memory
        memory = get_memory()

        # Final prompt
        prompt = f"""
{FOOTBALL_DOMAIN_PROMPT}

Conversation Memory:
{memory}

User Question:
{user_message}

At the end write:

Suggested Football Questions:
- question
- question
- question
"""

        # Gemini Response
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        text = response.text

        answer = text
        suggestions = []

        # Extract suggestions
        if "Suggested Football Questions:" in text:

            parts = text.split(
                "Suggested Football Questions:"
            )

            answer = parts[0].strip()

            suggestions = [

                q.replace("-", "")
                 .replace("*", "")
                 .strip()

                for q in parts[1].split("\n")

                if q.strip()

            ][:3]

        # Save chat
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

        return jsonify({
            "error": str(e)
        }), 500

# =========================================
# DELETE CHAT
# =========================================

@app.route("/delete", methods=["POST"])
def delete_chat():

    data = request.get_json()

    user_message = data.get("user_message")

    time = data.get("time")

    chats = load_chats()

    updated_chats = [

        chat for chat in chats

        if not (

            chat["user_message"] == user_message

            and

            chat["time"] == time

        )

    ]

    save_chats(updated_chats)

    return jsonify({
        "status": "deleted"
    })

# =========================================
# RENAME CHAT
# =========================================

@app.route("/rename", methods=["POST"])
def rename_chat():

    data = request.get_json()

    old_message = data.get("old_message")

    time = data.get("time")

    new_name = data.get("new_name")

    chats = load_chats()

    for chat in chats:

        if (

            chat["user_message"] == old_message

            and

            chat["time"] == time

        ):

            chat["user_message"] = new_name

    save_chats(chats)

    return jsonify({
        "status": "renamed"
    })

# =========================================
# RUN FLASK APP
# =========================================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=True
    )

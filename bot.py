from flask import Flask, request, jsonify
from telegram import Bot, Update
import os
import json

app = Flask(__name__)
bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))

LEAVE_REQUESTS_FILE = 'leave_requests.json'

def load_leave_requests():
    try:
        with open(LEAVE_REQUESTS_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return []

def save_leave_requests(leave_requests):
    with open(LEAVE_REQUESTS_FILE, 'w') as file:
        json.dump(leave_requests, file)

leave_requests = load_leave_requests()

@app.route('/')
def home():
    return "Telegram Bot is running!"

@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    chat_id = update.message.chat.id
    message_text = update.message.text

    if message_text.lower().startswith("/addleave"):
        parts = message_text.split(maxsplit=5)
        if len(parts) >= 6:
            leave_request = {
                "leaveId": parts[1],
                "visitPlace": parts[2],
                "reason": parts[3],
                "fromDate": parts[4],
                "toDate": parts[5]
            }
            leave_requests.append(leave_request)
            save_leave_requests(leave_requests)
            response = f"Leave request submitted!\nLeave ID: {leave_request['leaveId']}"
        else:
            response = "Usage: /addleave <LeaveID> <VisitPlace> <Reason> <FromDate> <ToDate>"
    else:
        response = "I didn't understand that. Try /addleave."

    bot.send_message(chat_id=chat_id, text=response)
    return "OK"

@app.route('/leave-requests', methods=['GET'])
def get_leave_requests():
    return jsonify(leave_requests)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

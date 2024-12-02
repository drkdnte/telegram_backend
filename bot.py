from flask import Flask, request, jsonify
from telegram import Bot, Update
import os
import firebase_admin
from firebase_admin import credentials, db

app = Flask(__name__)
bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))

firebase_key = os.getenv("FIREBASE_KEY")
firebase_cred = json.loads(firebase_key)

# Initialize Firebase
ccred = credentials.Certificate(firebase_cred)
initialize_app(cred, {
    "databaseURL": "https://tg-bot-ba554.firebaseio.com/"
})

# Reference to the "leave_requests" node in the database
leave_requests_ref = db.reference("leave_requests")

@app.route('/')
def home():
    return "Telegram Bot is running with Firebase!"

@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    chat_id = update.message.chat.id
    message_text = update.message.text

    if message_text.lower() == "/start":
        response = "Welcome to the Leave Management Bot! Use /help to see all available commands."
    elif message_text.lower() == "/help":
        response = "Here are the available commands:\n" \
                   "/start - Start the bot\n" \
                   "/addleave - Add a leave request\n" \
                   "/viewleaves - View submitted leave requests"
    elif message_text.lower().startswith("/addleave"):
        parts = message_text.split(maxsplit=5)
        if len(parts) == 6:
            leave_request = {
                "leaveId": parts[1],
                "visitPlace": parts[2],
                "reason": parts[3],
                "fromDate": parts[4],
                "toDate": parts[5]
            }
            # Store the leave request in Firebase
            leave_requests_ref.push(leave_request)
            response = f"Leave request submitted!\nLeave ID: {leave_request['leaveId']}"
        else:
            response = "Usage: /addleave <LeaveID> <VisitPlace> <Reason> <FromDate> <ToDate>"
    elif message_text.lower() == "/viewleaves":
        # Fetch leave requests from Firebase
        leave_requests = leave_requests_ref.get()
        if leave_requests:
            response = "Here are your leave requests:\n"
            for i, (key, leave) in enumerate(leave_requests.items(), start=1):
                response += f"{i}. Leave ID: {leave['leaveId']} | Visit Place: {leave['visitPlace']} | From: {leave['fromDate']} | To: {leave['toDate']}\n"
        else:
            response = "No leave requests found."
    else:
        response = "I didn't understand that. Use /help to see available commands."

    bot.send_message(chat_id=chat_id, text=response)
    return "OK"

@app.route('/leave-requests', methods=['GET'])
def get_leave_requests():
    leave_requests = leave_requests_ref.get()
    if leave_requests:
        return jsonify([leave for leave in leave_requests.values()])
    return jsonify([])  # Return an empty list if no requests are found

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

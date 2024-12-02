from flask import Flask, request
from telegram import Bot, Update
import os

# Initialize Flask app
app = Flask(__name__)

# Initialize Telegram bot using token from environment variables
bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))

# Root route for health check
@app.route('/')
def home():
    return "Telegram Bot is running!"

# Webhook route to handle Telegram updates
@app.route('/webhook', methods=['POST'])
def webhook():
    # Parse incoming Telegram update
    update = Update.de_json(request.get_json(force=True), bot)
    
    # Get the chat ID and message text
    chat_id = update.message.chat.id
    message_text = update.message.text
    
    # Example response logic
    if message_text.lower() == "/start":
        response = "Welcome to the Leave Management Bot! Use /addleave to submit a leave request."
    elif message_text.lower().startswith("/addleave"):
        # Extract leave details from the message
        parts = message_text.split(maxsplit=5)
        if len(parts) >= 5:
            leave_id, visit_place, reason, from_date, to_date = parts[1:]
            response = (f"Leave request received!\n"
                        f"Leave ID: {leave_id}\n"
                        f"Visit Place: {visit_place}\n"
                        f"Reason: {reason}\n"
                        f"From: {from_date}\n"
                        f"To: {to_date}")
        else:
            response = "Usage: /addleave <LeaveID> <VisitPlace> <Reason> <FromDate> <ToDate>"
    else:
        response = "I didn't understand that. Try /start or /addleave."

    # Send response back to the user
    bot.send_message(chat_id=chat_id, text=response)
    return "OK"

# Run the app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

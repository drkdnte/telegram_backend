from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from telegram import Bot, Update
import os
import firebase_admin
from firebase_admin import credentials, db, initialize_app
import json

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins; adjust this in production for security
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Initialize the Telegram Bot
token = os.getenv("TELEGRAM_BOT_TOKEN")
if not token:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set")
bot = Bot(token)

# Load Firebase credentials from the environment variable
firebase_key = os.getenv("FIREBASE_KEY")
if not firebase_key:
    raise ValueError("FIREBASE_KEY environment variable is not set")

firebase_cred = json.loads(firebase_key)

# Initialize Firebase credentials
cred = credentials.Certificate(firebase_cred)

# Initialize Firebase App
initialize_app(cred, {
    "databaseURL": "https://tg-bot-5241b-default-rtdb.firebaseio.com/"  # Update to your new database URL
})

# Reference to the "leave_requests" node in the database
leave_requests_ref = db.reference("leave_requests")

# Dictionary to hold user data
user_data = {}

@app.get("/")
async def home():
    return {"message": "Telegram Bot is running with Firebase!"}

@app.post("/webhook")  # Ensure this is the correct path
async def webhook(request: Request):
    update = Update.de_json(await request.json(), bot)  # Await the JSON request
    chat_id = update.message.chat.id
    message_text = update.message.text

    # Handle commands
    if message_text.lower() == "/start":
        response = "Welcome to the Leave Management Bot! Use /help to see all available commands."
    elif message_text.lower() == "/help":
        response = "Here are the available commands:\n" \
                   "/start - Start the bot\n" \
                   "/addleave - Add a leave request\n" \
                   "/viewleaves - View submitted leave requests"
    elif message_text.lower() == "/addleave":
        # Start the leave request process
        user_data[chat_id] = {}  # Initialize user data
        await ask_leave_id(chat_id)  # Ask for Leave ID
        return {"status": "ok"}

    elif chat_id in user_data:
        # Handle user input based on expected fields
        if "leaveId" not in user_data[chat_id]:
            user_data[chat_id]["leaveId"] = message_text.strip('"')
            await ask_visit_place(chat_id)  # Ask for Visit Place
        elif "visitPlace" not in user_data[chat_id]:
            user_data[chat_id]["visitPlace"] = message_text.strip('"')
            await ask_reason(chat_id)  # Ask for Reason
        elif "reason" not in user_data[chat_id]:
            user_data[chat_id]["reason"] = message_text.strip('"')
            await ask_leave_type(chat_id)  # Ask for Leave Type
        elif "leaveType" not in user_data[chat_id]:
            user_data[chat_id]["leaveType"] = message_text.strip('"')
            await ask_from_date(chat_id)  # Ask for From Date
        elif "fromDate" not in user_data[chat_id]:
            user_data[chat_id]["fromDate"] = message_text.strip('"')
            await ask_to_date(chat_id)  # Ask for To Date
        elif "toDate" not in user_data[chat_id]:
            user_data[chat_id]["toDate"] = message_text.strip('"')
            await ask_remark(chat_id)  # Ask for Remark
        elif "remark" not in user_data[chat_id]:
            user_data[chat_id]["remark"] = message_text.strip('"')
            await confirm_leave_request(chat_id)  # Confirm the request

    else:
        response = "I didn't understand that. Use /help to see available commands."

    await bot.send_message(chat_id=chat_id, text=response)  # Await the send_message coroutine
    return {"status": "ok"}

# Function to ask for Leave ID
async def ask_leave_id(chat_id):
    await bot.send_message(chat_id, "Please enter your Leave ID:")

# Function to ask for Visit Place
async def ask_visit_place(chat_id):
    await bot.send_message(chat_id, "Please enter the Visit Place:")

# Function to ask for Reason
async def ask_reason(chat_id):
    await bot.send_message(chat_id, "Please enter the Reason:")

# Function to ask for Leave Type
async def ask_leave_type(chat_id):
    await bot.send_message(chat_id, "Please enter the Leave Type:")

# Function to ask for From Date
async def ask_from_date(chat_id):
    await bot.send_message(chat_id, "Please enter the From Date and Time (e.g., 01-DEC-2024 06:30 AM):")

# Function to ask for To Date
async def ask_to_date(chat_id):
    await bot.send_message(chat_id, "Please enter the To Date and Time (e.g., 02-DEC-2024 09:00 PM):")

# Function to ask for Remark
async def ask_remark(chat_id):
    await bot.send_message(chat_id, "Please enter any remarks (leave blank if none):")

# Function to confirm leave request
async def confirm_leave_request(chat_id):
    leave_request = user_data[chat_id]
    response = (
        f"Please confirm your leave request:\n"
        f"Leave ID: {leave_request['leaveId']}\n"
        f"Visit Place: {leave_request['visitPlace']}\n"
        f"Reason: {leave_request['reason']}\n"
        f"Leave Type: {leave_request['leaveType']}\n"
        f"From: {leave_request['fromDate']}\n"
        f"To: {leave_request['toDate']}\n"
        f"Remark: {leave_request['remark']}\n"
        f"Status: Pending\n"  # Explicitly include status
        "Is this correct? (yes/no)"
    )
    await bot.send_message(chat_id, response)

@app.get("/leave-requests")
async def get_leave_requests():
    leave_requests = leave_requests_ref.get()
    if leave_requests:
        return [leave for leave in leave_requests.values()]
    return []  # Return an empty list if no requests are found

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)

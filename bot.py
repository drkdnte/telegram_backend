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
    elif message_text.lower().startswith("/addleave"):
        # Get everything after the command as a single input
        command_parts = message_text.split(maxsplit=1)

        if len(command_parts) < 2:
            response = "Usage: /addleave <LeaveID> <VisitPlace> <Reason> <LeaveType> <FromDateTime> <ToDateTime>"
            await bot.send_message(chat_id=chat_id, text=response)
            return {"status": "ok"}
        
        # Split the input values by comma
        inputs = command_parts[1].split(",")  # Adjust this to whatever delimiter you choose
        if len(inputs) == 6:  # We expect 6 inputs
            leave_request = {
                "leaveId": inputs[0].strip(),  # Leave ID
                "visitPlace": inputs[1].strip(),  # Visit Place
                "reason": inputs[2].strip(),  # Reason
                "leaveType": inputs[3].strip().upper(),  # Leave Type (converted to uppercase)
                "fromDate": inputs[4].strip().upper(),  # From DateTime (converted to uppercase)
                "toDate": inputs[5].strip().upper(),  # To DateTime (converted to uppercase)
                "status": "REQUEST APPROVED",  # Automatically set status to "Pending"
                "remark": "Approved by [ 100254 ] [ KANNAN S ]"  # Automatically set remark to an empty string
            }
            leave_requests_ref.push(leave_request)
            response = f"Leave request submitted!\nLeave ID: {leave_request['leaveId']}"
        else:
            response = "Usage: /addleave <LeaveID>, <VisitPlace>, <Reason>, <LeaveType>, <FromDateTime>, <ToDateTime>"
    elif message_text.lower() == "/viewleaves":
        leave_requests = leave_requests_ref.get()
        if leave_requests:
            # Reverse the order of leave requests
            reversed_requests = list(leave_requests.items())[::-1]
            response = "Here are your leave requests (most recent first):\n"
            for i, (key, leave) in enumerate(reversed_requests, start=1):
                response += f"{i}. Leave ID: {leave['leaveId']} | Visit Place: {leave['visitPlace']} | From: {leave['fromDate']} | To: {leave['toDate']} | Status: {leave['status']} | Remark: {leave['remark']}\n"
        else:
            response = "No leave requests found."
    else:
        response = "I didn't understand that. Use /help to see available commands."

    await bot.send_message(chat_id=chat_id, text=response)  # Await the send_message coroutine
    return {"status": "ok"}

@app.get("/leave-requests")
async def get_leave_requests():
    leave_requests = leave_requests_ref.get()
    if leave_requests:
        # Reverse the order of leave requests
        reversed_requests = list(leave_requests.items())[::-1]
        return [leave for _, leave in reversed_requests]  # Return the reversed leave requests
    return []  # Return an empty list if no requests are found

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)

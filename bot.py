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
        # Splitting the command based on 'to' to separate From and To entries
        parts = message_text.split(" to ")
        if len(parts) == 2:
            details = parts[0].split(maxsplit=6)  # Split the first part to get other parameters
            if len(details) == 7:  # Expecting all parameters including FromDateTime
                leave_request = {
                    "leaveId": details[1],
                    "visitPlace": details[2],
                    "reason": details[3],
                    "leaveType": details[4],
                    "fromDate": details[5].strip(),  # This will capture the full From date-time
                    "toDate": parts[1].strip(),
                "status": "REQUEST APPROVED",  # Automatically set status to "Pending"
                "remark": "Approved by [ 100254 ] [ KANNAN S ]"  # Automatically set remark to an empty string
            }
                leave_requests_ref.push(leave_request)
                response = f"Leave request submitted!\nLeave ID: {leave_request['leaveId']}"
            else:
                response = "Usage: /addleave <LeaveID> <VisitPlace> <Reason> <LeaveType> <FromDateTime> to <ToDateTime>"
        else:
            response = "Usage: /addleave <LeaveID> <VisitPlace> <Reason> <LeaveType> <FromDateTime> to <ToDateTime>"
    elif message_text.lower() == "/viewleaves":
        leave_requests = leave_requests_ref.get()
        if leave_requests:
            response = "Here are your leave requests:\n"
            for i, (key, leave) in enumerate(leave_requests.items(), start=1):
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
        return [leave for leave in leave_requests.values()]
    return []  # Return an empty list if no requests are found

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)

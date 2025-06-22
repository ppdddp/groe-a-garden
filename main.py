from fastapi import FastAPI, Request
import httpx
import os

app = FastAPI()

LINE_TOKEN = os.getenv("LINE_TOKEN")
USER_ID = os.getenv("USER_ID")
ARDUINO_URL = os.getenv("ARDUINO_URL")

@app.get("/")
async def root():
    return {"message": "FastAPI is working!"}

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    message = data["events"][0]["message"]["text"]

    if message == "ขอค่าความชื้น":
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{ARDUINO_URL}/moisture")
            moisture = response.json()["moisture"]

        await reply_to_line(f"ค่าความชื้นปัจจุบันคือ {moisture}%")
    return {"status": "ok"}

async def reply_to_line(msg: str):
    headers = {
        "Authorization": f"Bearer {LINE_TOKEN}",
        "Content-Type": "application/json"
    }
    body = {
        "to": USER_ID,
        "messages": [{"type": "text", "text": msg}]
    }

    async with httpx.AsyncClient() as client:
        await client.post("https://api.line.me/v2/bot/message/push", headers=headers, json=body)

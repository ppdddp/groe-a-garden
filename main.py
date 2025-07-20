from fastapi import FastAPI, Request, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import datetime
import os
import httpx

app = FastAPI()

latest_moisture = {
    "moisture": None,
    "sensor_id": None,
    "timestamp": None
}

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

class MoistureData(BaseModel):
    moisture: float
    sensor_id: str

@app.post("/report-moisture")
async def receive_moisture(data: MoistureData):
    global latest_moisture
    now = datetime.datetime.now()
    latest_moisture = {
        "moisture": data.moisture,
        "sensor_id": data.sensor_id,
        "timestamp": now
    }
    print(f"[{now}] Received moisture: {data.moisture}% from {data.sensor_id}")
    return {"status": "received"}

class LineMessage(BaseModel):
    type: str
    text: str

class LineEvent(BaseModel):
    type: str
    replyToken: str
    message: LineMessage

class LineWebhook(BaseModel):
    events: list[LineEvent]

@app.post("/webhook")
async def line_webhook(request: Request, x_line_signature: str = Header(None)):
    body = await request.json()
    data = LineWebhook.parse_obj(body)

    for event in data.events:
        user_msg = event.message.text.strip().lower()
        if user_msg == "ขอค่าความชื้น":
            if latest_moisture["moisture"] is not None and latest_moisture["timestamp"] is not None:
                now = datetime.datetime.now()
                delta = now - latest_moisture["timestamp"]
                if delta.total_seconds() <= 60:
                    reply = f"ค่าความชื้น: {latest_moisture['moisture']:.1f}%"
                else:
                    reply = "ยังไม่มีข้อมูลความชื้นครับ"
            else:
                reply = "ไม่สามารถรับข้อมูลจาก Arduino ได้ในช่วง 1 นาทีที่ผ่านมา อาจเกิดจากแบตหมดหรืออุปกรณ์ขัดข้อง"
        else:
            reply = "พิมพ์ว่า 'ขอค่าความชื้น' เพื่อดูข้อมูล"

        await reply_to_line(event.replyToken, reply)

    return JSONResponse(content={"status": "ok"})

async def reply_to_line(token: str, message: str):
    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "replyToken": token,
        "messages": [{"type": "text", "text": message}]
    }
    async with httpx.AsyncClient() as client:
        await client.post("https://api.line.me/v2/bot/message/reply", headers=headers, json=payload)

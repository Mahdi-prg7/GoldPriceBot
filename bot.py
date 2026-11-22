import os
import requests

TOKEN = os.environ["BOT_TOKEN"]
CHANNEL = "@goldpricen"

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

response = requests.post(url, data={
    "chat_id": CHANNEL,
    "text": "✅ تست ربات نوروزی\n\nربات با موفقیت به کانال متصل شد و ارسال پیام انجام شد."
})

print(response.text)

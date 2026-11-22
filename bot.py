
import os
import requests
from datetime import datetime

TOKEN = os.environ["BOT_TOKEN"]
CHANNEL = "@goldpricen"

API_URL = "https://nerkhara.com/api/v1/latest.json"
TELEGRAM_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

def money(value):
    if value is None:
        return "ناموجود"
    return f"{float(value):,.0f}"

def change(value):
    if value is None:
        return "—"
    value = float(value)
    arrow = "🟢 ▲" if value > 0 else "🔴 ▼" if value < 0 else "⚪"
    return f"{arrow} {abs(value):.2f}%"

def main():
    response = requests.get(API_URL, timeout=20)
    response.raise_for_status()
    data = response.json()

    items = {
        item["id"]: item
        for item in data.get("items", [])
    }

    def get_item(item_id):
        return items.get(item_id)

    def line(item_id, title, toman=True):
        item = get_item(item_id)
        if not item:
            return None

        price = item.get("price_irt") if toman else item.get("price")
        unit = "تومان" if toman else item.get("unit", "")
        return f"{title}: {money(price)} {unit} | {change(item.get('change_pct'))}"

    sections = [
        ("🥇 طلا", [
            line("gold-18k", "طلای ۱۸ عیار"),
            line("gold-24k", "طلای ۲۴ عیار"),
            line("gold-mesghal", "مثقال طلا"),
            line("xau", "اونس جهانی", False),
        ]),
        ("🪙 سکه", [
            line("coin-emami", "سکه امامی"),
            line("coin-bahar-azadi", "سکه بهار آزادی"),
            line("coin-half", "نیم سکه"),
            line("coin-quarter", "ربع سکه"),
            line("coin-gram", "سکه گرمی"),
        ]),
        ("💵 ارز", [
            line("usd", "دلار"),
            line("eur", "یورو"),
            line("usdt", "تتر"),
        ]),
        ("₿ رمزارز", [
            line("btc", "بیت‌کوین"),
            line("eth", "اتریوم"),
        ]),
    ]

    message = ["📊 قیمت لحظه‌ای بازار", ""]

    for title, rows in sections:
        available_rows = [row for row in rows if row]
        if available_rows:
            message.append(title)
            message.extend(available_rows)
            message.append("")

    message.extend([
        "⏱ بروزرسانی خودکار هر ۱۵ دقیقه",
        "⚠️ قیمت‌ها تقریبی هستند و ملاک معامله نیستند.",
        "منبع: nerkhara.com"
    ])

    telegram_response = requests.post(
        TELEGRAM_URL,
        data={
            "chat_id": CHANNEL,
            "text": "\n".join(message)
        },
        timeout=20
    )
    telegram_response.raise_for_status()

    result = telegram_response.json()
    if not result.get("ok"):
        raise RuntimeError(result)

    print("Message sent successfully!")

if __name__ == "__main__":
    main()


import os
import requests

TOKEN = os.environ["BOT_TOKEN"]
CHANNEL = "@goldpricen"

API_URL = "https://nerkhara.com/api/v1/latest.json"
TELEGRAM_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"


def format_price(value):
    if value is None or float(value) <= 0:
        return None
    return f"{float(value):,.0f}"


def format_change(value):
    if value is None:
        return "—"

    value = float(value)

    if value > 0:
        return f"🟢 ▲ {value:.2f}%"
    if value < 0:
        return f"🔴 ▼ {abs(value):.2f}%"

    return "⚪ 0.00%"


def main():
    response = requests.get(API_URL, timeout=25)
    response.raise_for_status()

    data = response.json()

    if data.get("stale") is True:
        raise RuntimeError("API data is stale. Message not sent.")

    items = {
        item["id"]: item
        for item in data.get("items", [])
    }

    def make_line(item_id, title, toman=True):
        item = items.get(item_id)

        if not item or item.get("stale") is True:
            return None

        price = (
            item.get("price_irt")
            if toman and item.get("price_irt") is not None
            else item.get("price")
        )

        formatted = format_price(price)

        if formatted is None:
            return None

        unit = "تومان" if toman else item.get("unit", "")

        return (
            f"{title}: {formatted} {unit}"
            f" | {format_change(item.get('change_pct'))}"
        )

    sections = [
        ("🥇 طلا", [
            make_line("gold-18k", "طلای ۱۸ عیار"),
            make_line("gold-24k", "طلای ۲۴ عیار"),
            make_line("gold-mesghal", "مثقال طلا"),
            make_line("xau", "اونس جهانی", False),
        ]),
        ("🪙 سکه", [
            make_line("coin-emami", "سکه امامی"),
            make_line("coin-bahar-azadi", "سکه بهار آزادی"),
            make_line("coin-half", "نیم سکه"),
            make_line("coin-quarter", "ربع سکه"),
            make_line("coin-gram", "سکه گرمی"),
        ]),
        ("💵 ارز", [
            make_line("usd", "دلار"),
            make_line("eur", "یورو"),
            make_line("usdt", "تتر"),
        ]),
        ("₿ رمزارز", [
            make_line("btc", "بیت‌کوین"),
            make_line("eth", "اتریوم"),
        ]),
    ]

    message = ["📊 قیمت روز بازار", ""]

    for title, rows in sections:
        rows = [row for row in rows if row]

        if rows:
            message.append(title)
            message.extend(rows)
            message.append("")

    if len(message) <= 2:
        raise RuntimeError("No valid prices found. Message not sent.")

    message.extend([
        "🔄 بروزرسانی خودکار",
        "",
        "🛠️ پشتیبانی و ارتباط با ما",
        "📩 https://t.me/abshodenoroozi",
        "منبع: nerkhara.com"
    ])

    telegram_response = requests.post(
        TELEGRAM_URL,
        data={
            "chat_id": CHANNEL,
            "text": "\n".join(message)
        },
        timeout=25
    )

    telegram_response.raise_for_status()

    result = telegram_response.json()

    if not result.get("ok"):
        raise RuntimeError(result)

    print("Price message sent successfully!")


if __name__ == "__main__":
    main()

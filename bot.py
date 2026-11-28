
import os
import requests
import jdatetime
from datetime import datetime
from zoneinfo import ZoneInfo

TOKEN = os.environ["BOT_TOKEN"]
CHANNEL = "@abshodenoroozi"

API_URL = "https://nerkhara.com/api/v1/latest.json"
TELEGRAM_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

OUNCE_GRAMS = 31.1034768


def format_price(value):
    if value is None:
        return None

    value = float(value)

    if value < 1000:
        return None

    return f"{value:,.0f}"


def format_change(value):
    if value is None:
        return "—"

    value = float(value)

    if value > 0:
        return f"🟢 ▲ {value:.2f}%"
    if value < 0:
        return f"🔴 ▼ {abs(value):.2f}%"

    return "⚪ 0.00%"


def get_gold_market_status(item=None):
    now_ny = datetime.now(ZoneInfo("America/New_York"))

    weekday = now_ny.weekday()
    current_time = now_ny.time()

    # Saturday: market closed
    if weekday == 5:
        return " (بسته)"

    # Friday after 17:00 New York
    if weekday == 4 and current_time.hour >= 17:
        return " (بسته)"

    # Sunday before 18:00 New York
    if weekday == 6 and current_time.hour < 18:
        return " (بسته)"

    return ""


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

    def get_item(item_id):
        item = items.get(item_id)

        if not item or item.get("stale") is True:
            return None

        return item

    def get_price(item_id):
        item = get_item(item_id)

        if not item:
            return None

        return item.get("price_irt") or item.get("price")

    def make_line(item_id, title):
        item = get_item(item_id)

        if not item:
            return None

        price = item.get("price_irt")
        if price is None:
            price = item.get("price")

        formatted = format_price(price)

        if formatted is None:
            return None

        return (
            f"{title}: {formatted} تومان"
            f" | {format_change(item.get('change_pct'))}"
        )

    gold18 = get_price("gold-18k")
    usd = get_price("usd")

    ounce_item = get_item("xau")
    ounce = ounce_item.get("price") if ounce_item else None

    # Calculate 24k gold from 18k
    gold24 = None

    if gold18 is not None and float(gold18) > 0:
        gold24 = float(gold18) * 999 / 750

    # Calculate theoretical 18k price per gram
    theoretical_gold18 = None

    if (
        ounce is not None
        and usd is not None
        and float(ounce) > 0
        and float(usd) > 0
    ):
        theoretical_gold18 = (
            float(ounce) * float(usd) * 750
            / (OUNCE_GRAMS * 999)
        )

    # Calculate positive or negative bubble
    bubble = None
    bubble_percent = None

    if (
        gold18 is not None
        and theoretical_gold18 is not None
        and theoretical_gold18 > 0
    ):
        bubble = float(gold18) - theoretical_gold18
        bubble_percent = bubble / theoretical_gold18 * 100

    # Iran date and time
    now = datetime.now(ZoneInfo("Asia/Tehran"))
    jalali_now = jdatetime.datetime.fromgregorian(datetime=now)

    message = [
        "📊 قیمت روز بازار",
        f"📅 تاریخ: {jalali_now.strftime('%Y/%m/%d')}",
        f"🕒 ساعت: {now.strftime('%H:%M')}",
        "",
        "🥇 طلا",
    ]

    line18 = make_line("gold-18k", "طلای ۱۸ عیار")
    if line18:
        message.append(line18)

    formatted24 = format_price(gold24)

    if formatted24:
        message.append(
            f"طلای ۲۴ عیار: {formatted24} تومان"
        )

    line_mesghal = make_line(
        "gold-mesghal",
        "مظنه داخلی ۱۷"
    )

    if line_mesghal:
        message.append(line_mesghal)

    # Global ounce and market status
    if ounce is not None:
        formatted_ounce = f"{float(ounce):,.2f}"
        status = get_gold_market_status(ounce_item)

        message.append(
            f"اونس جهانی: {formatted_ounce} دلار{status}"
        )

    # Gold bubble
    if bubble is not None:
        bubble_text = f"{abs(bubble):,.0f}"
        bubble_percent_text = f"{abs(bubble_percent):.2f}%"

        if bubble > 0:
            message.append(
                f"حباب طلا: مثبت {bubble_text} تومان "
                f"(+{bubble_percent_text})"
            )
        elif bubble < 0:
            message.append(
                f"حباب طلا: منفی {bubble_text} تومان "
                f"(-{bubble_percent_text})"
            )
        else:
            message.append("حباب طلا: صفر")

    message.append("")
    message.append("🪙 سکه")

    coin_lines = [
        make_line("coin-emami", "سکه امامی"),
        make_line("coin-bahar-azadi", "سکه بهار آزادی"),
        make_line("coin-half", "نیم سکه"),
        make_line("coin-quarter", "ربع سکه"),
        make_line("coin-gram", "سکه گرمی"),
    ]

    message.extend(line for line in coin_lines if line)

    message.append("")
    message.append("💵 ارز")

    currency_lines = [
        make_line("usd", "دلار"),
        make_line("eur", "یورو"),
    ]

    message.extend(line for line in currency_lines if line)

    message.extend([
        "",
        "قیمت‌ها حدودی بوده و ملاک معاملات نیستند.",
        "",
        "🛠️ پشتیبانی و ارتباط با ما",
        "@abshodenoroozi",
    ])

    # Send message to new channel
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

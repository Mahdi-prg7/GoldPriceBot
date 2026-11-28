
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

    if weekday == 5:
        return " (بسته)"

    if weekday == 4 and current_time.hour >= 17:
        return " (بسته)"

    if weekday == 6 and current_time.hour < 18:
        return " (بسته)"

    return ""


def price_line(item_id, title):
    item = ITEMS.get(item_id)

    if not item or item.get("stale") is True:
        return None

    price = item.get("price_irt")
    if price is None:
        price = item.get("price")

    formatted = format_price(price)

    if formatted is None:
        return None

    return (
        f"{title}: <b>{formatted} تومان</b>  "
        f"{format_change(item.get('change_pct'))}"
    )


ITEMS = {}


def main():
    global ITEMS

    response = requests.get(API_URL, timeout=25)
    response.raise_for_status()

    data = response.json()

    if data.get("stale") is True:
        raise RuntimeError("API data is stale. Message not sent.")

    ITEMS = {
        item["id"]: item
        for item in data.get("items", [])
    }

    def get_item(item_id):
        item = ITEMS.get(item_id)

        if not item or item.get("stale") is True:
            return None

        return item

    def get_price(item_id):
        item = get_item(item_id)

        if not item:
            return None

        price = item.get("price_irt")
        if price is None:
            price = item.get("price")

        return price

    gold18 = get_price("gold-18k")
    usd = get_price("usd")

    ounce_item = get_item("xau")
    ounce = ounce_item.get("price") if ounce_item else None

    # محاسبه طلای 24 عیار از طلای 18 عیار
    gold24 = None

    if gold18 is not None and float(gold18) > 0:
        gold24 = float(gold18) * 999 / 750

    # محاسبه قیمت نظری طلای 18 عیار از اونس جهانی
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

    # محاسبه حباب مثبت یا منفی
    bubble = None
    bubble_percent = None

    if (
        gold18 is not None
        and theoretical_gold18 is not None
        and theoretical_gold18 > 0
    ):
        bubble = float(gold18) - theoretical_gold18
        bubble_percent = bubble / theoretical_gold18 * 100

    # تاریخ و ساعت ایران
    now = datetime.now(ZoneInfo("Asia/Tehran"))
    jalali_now = jdatetime.datetime.fromgregorian(datetime=now)

    date_text = jalali_now.strftime("%Y/%m/%d")
    time_text = now.strftime("%H:%M")

    message = [
        "📊 <b>گزارش لحظه‌ای بازار</b>",
        "<b>قیمت طلا و ارز</b>",
        f"📅 {date_text}  |  🕒 {time_text}",
        "",
        "━━━━━━━━━━━━━━",
        "🥇 <b>بازار طلا</b>",
        "━━━━━━━━━━━━━━",
    ]

    # طلای 18 عیار
    line18 = price_line("gold-18k", "طلای ۱۸ عیار")
    if line18:
        message.append(line18)

    # طلای 24 عیار محاسبه‌شده
    formatted24 = format_price(gold24)
    if formatted24:
        message.append(
            f"طلای ۲۴ عیار: <b>{formatted24} تومان</b>"
        )

    # مظنه داخلی 17
    mesghal_line = price_line(
        "gold-mesghal",
        "مظنه داخلی ۱۷"
    )
    if mesghal_line:
        message.append(mesghal_line)

    # اونس جهانی
    if ounce is not None:
        formatted_ounce = f"{float(ounce):,.2f}"
        status = get_gold_market_status(ounce_item)

        message.append(
            f"اونس جهانی: <b>{formatted_ounce} دلار</b>{status}"
        )

    # حباب طلا
    if bubble is not None:
        bubble_text = f"{abs(bubble):,.0f}"
        percent_text = f"{abs(bubble_percent):.2f}%"

        if bubble > 0:
            message.append(
                f"📈 حباب طلا: <b>مثبت {bubble_text} تومان "
                f"(+{percent_text})</b>"
            )
        elif bubble < 0:
            message.append(
                f"📉 حباب طلا: <b>منفی {bubble_text} تومان "
                f"(-{percent_text})</b>"
            )
        else:
            message.append("حباب طلا: <b>صفر</b>")

    # بخش سکه
    message.extend([
        "",
        "━━━━━━━━━━━━━━",
        "🪙 <b>بازار سکه</b>",
        "━━━━━━━━━━━━━━",
    ])

    coin_lines = [
        price_line("coin-emami", "سکه امامی"),
        price_line("coin-bahar-azadi", "سکه بهار آزادی"),
        price_line("coin-half", "نیم سکه"),
        price_line("coin-quarter", "ربع سکه"),
        price_line("coin-gram", "سکه گرمی"),
    ]

    message.extend(line for line in coin_lines if line)

    # بخش ارز
    message.extend([
        "",
        "━━━━━━━━━━━━━━",
        "💱 <b>بازار ارز</b>",
        "━━━━━━━━━━━━━━",
    ])

    currency_lines = [
        price_line("usd", "دلار"),
        price_line("eur", "یورو"),
    ]

    message.extend(line for line in currency_lines if line)

    # پایین پیام
    message.extend([
        "",
        "━━━━━━━━━━━━━━",
        "⚠️ <i>قیمت‌ها حدودی بوده و ملاک معاملات نیستند.</i>",
        "",
        "🛠️ <b>پشتیبانی و ارتباط با ما</b>",
        "@abshodenoroozi",
    ])

    # ارسال به کانال
    telegram_response = requests.post(
        TELEGRAM_URL,
        data={
            "chat_id": CHANNEL,
            "text": "\n".join(message),
            "parse_mode": "HTML"
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

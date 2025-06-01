import requests
from bs4 import BeautifulSoup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update
import os
import time

BOT_TOKEN = os.getenv("BOT_TOKEN", "7735637505:AAHgO5rkzSUQWvEgeUWWK1m-Z6GfuyZnwcA")

def get_eurusd_price():
    url = "https://www.investing.com/currencies/eur-usd"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.content, "html.parser")
    price_elem = soup.find("span", {"data-test": "instrument-price-last"})
    if price_elem:
        try:
            return float(price_elem.text.replace(",", ""))
        except Exception:
            return None
    return None

async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("جاري جلب الإشارة ...")
    price = get_eurusd_price()
    if price is None:
        await update.message.reply_text("تعذر جلب السعر حالياً.")
        return
    # مثال بسيط لإشارة بناءً على سعر واحد فقط
    signal = "شراء" if price < 1.08 else "بيع" if price > 1.09 else "انتظر"
    now = time.strftime('%Y-%m-%d %H:%M')
    amount = 50
    msg = f"الإشارة: {signal}\nالسعر الحالي: {price}\nالوقت: {now}\nالمبلغ المقترح: {amount} $"
    await update.message.reply_text(msg)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("اكتب /signal لجلب الإشارة.")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("signal", signal))
    app.run_polling()

if __name__ == "__main__":
    main()

import os
import time
import requests
import pandas as pd
import ta
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# إعدادات
BOT_TOKEN = os.getenv("BOT_TOKEN", "7735637505:AAGRzIHJPBoJz4sz5PT7mTG0tPbAyek7kN8")
ADMIN_ID = 0  # ضع هنا رقم تليجرام حقك لو تريد رسائل خاصة

# جلب سعر EUR/USD من TradingView
def get_eurusd_price():
    url = "https://www.tradingview.com/symbols/EURUSD/"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.content, "html.parser")
    # ابحث عن العنصر الصحيح (قد يتغير حسب تحديثات TradingView)
    price_elem = soup.find("div", {"data-symbol":"EURUSD"})
    if not price_elem:
        # حل بديل: ابحث عن أول عنصر فيه رقم وشكله قريب للسعر
        price_elem = soup.find("div", class_="bigValue")
    if price_elem:
        try:
            price = float(price_elem.text.replace(",", ""))
            return price
        except Exception:
            pass
    # حل أخير: جلب من موقع بديل
    url2 = "https://www.investing.com/currencies/eur-usd"
    r = requests.get(url2, headers=headers)
    soup = BeautifulSoup(r.content, "html.parser")
    price_elem = soup.find("span", {"data-test": "instrument-price-last"})
    if price_elem:
        try:
            price = float(price_elem.text.replace(",", ""))
            return price
        except Exception:
            pass
    return None

# تحليل الإشارة بناء على مؤشرات فنية (مثال: 5 مؤشرات، عدل حتى 20)
def analyze_signal(prices):
    df = pd.DataFrame({'close': prices})
    # مؤشرات فنية
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
    df['macd'] = ta.trend.MACD(df['close']).macd()
    df['ema20'] = ta.trend.EMAIndicator(df['close'], window=20).ema_indicator()
    df['ema50'] = ta.trend.EMAIndicator(df['close'], window=50).ema_indicator()
    df['sma20'] = ta.trend.SMAIndicator(df['close'], window=20).sma_indicator()
    # أضف المزيد حتى 20 مؤشر إذا أحببت

    last = df.iloc[-1]
    buy, sell, wait = 0, 0, 0

    # قواعد بسيطة (طورها حسب رغبتك)
    if last['rsi'] < 30:
        buy += 1
    elif last['rsi'] > 70:
        sell += 1
    else:
        wait += 1

    if last['macd'] > 0:
        buy += 1
    elif last['macd'] < 0:
        sell += 1
    else:
        wait += 1

    if last['close'] > last['ema20']:
        buy += 1
    else:
        sell += 1

    if last['ema20'] > last['ema50']:
        buy += 1
    else:
        sell += 1

    if last['close'] > last['sma20']:
        buy += 1
    else:
        sell += 1

    total = buy + sell + wait
    if max(buy, sell, wait) == wait or abs(buy - sell) <= 1:
        return "السوق متذبذب، ارجع بعد نصف ساعة"
    elif buy > sell:
        return "شراء"
    else:
        return "بيع"

# حساب المبلغ المقترح
def calc_amount(balance=1000):
    return round(balance * 0.05, 2)

# أمر /signal
async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("جاري جلب السعر والتحليل ...")
    prices = []
    # جلب آخر 30 سعر (هنا نكرر نفس السعر لعدم توفر بيانات تاريخية، يمكنك تطويرها بطرق أخرى)
    for _ in range(30):
        price = get_eurusd_price()
        if price:
            prices.append(price)
        else:
            prices.append(prices[-1] if prices else 1.08)
        time.sleep(1)  # انتظر ثانية بين كل محاولة (لتخفيف الضغط على الموقع)
    signal = analyze_signal(prices)
    now = time.strftime('%Y-%m-%d %H:%M')
    amount = calc_amount()
    price_now = prices[-1]
    msg = f"الإشارة: {signal}\nالسعر الحالي: {price_now}\nالوقت: {now}\nالمبلغ المقترح: {amount} $"
    await update.message.reply_text(msg)

# أمر بدء /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("مرحباً! هذا بوت إشارات EUR/USD.\nاكتب /signal لجلب الإشارة الحالية.")

# بوت تليجرام
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("signal", signal))
    print("البوت شغّال ...")
    app.run_polling()

if __name__ == "__main__":
    main()

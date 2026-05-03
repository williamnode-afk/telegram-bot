import os
import requests

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes
)

TOKEN = os.getenv("TOKEN")
NEWS_API = os.getenv("NEWSAPI_KEY")
FMP_API = os.getenv("FMP_API")
CHAT_ID = os.getenv("CHAT_ID")

last_price = None

# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 BOT TRADING ACTIF\n\n"
        "/btc\n/nasdaq\n/macro\n/news\n/decision"
    )

# =========================
# BTC
# =========================
async def btc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = requests.get(
            "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true"
        ).json()["bitcoin"]

        price = data["usd"]
        change = data["usd_24h_change"]

        trend = "📈 Bullish" if change > 1 else "📉 Bearish" if change < -1 else "➡️ Range"
        manipulation = "⚠️ Oui" if abs(change) > 5 else "Non"

        await update.message.reply_text(f"""
💰 BTC

Prix : {price}$
Variation : {round(change,2)}%

Trend : {trend}
Manipulation : {manipulation}
""")

    except:
        await update.message.reply_text("⚠️ BTC indisponible")

# =========================
# NASDAQ
# =========================
async def nasdaq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        r = requests.get(
            "https://query1.finance.yahoo.com/v7/finance/quote?symbols=^IXIC"
        ).json()["quoteResponse"]["result"][0]

        price = r["regularMarketPrice"]
        change = r["regularMarketChangePercent"]

        sens = "📈 Hausse" if change > 0 else "📉 Baisse"

        await update.message.reply_text(f"""
📊 NASDAQ

Prix : {price}
Variation : {round(change,2)}%

{sens}
""")

    except:
        await update.message.reply_text("⚠️ Nasdaq indisponible")

# =========================
# MACRO
# =========================
async def macro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        gold = requests.get(
            f"https://financialmodelingprep.com/api/v3/quote/XAUUSD?apikey={FMP_API}"
        ).json()[0]["price"]

        oil = requests.get(
            f"https://financialmodelingprep.com/api/v3/quote/CLUSD?apikey={FMP_API}"
        ).json()[0]["price"]

        dxy = requests.get(
            "https://query1.finance.yahoo.com/v7/finance/quote?symbols=DX-Y.NYB"
        ).json()["quoteResponse"]["result"][0]["regularMarketPrice"]

        await update.message.reply_text(f"""
🌍 MACRO

🟡 Or : {gold}
🛢 Oil : {oil}
💵 DXY : {dxy}
""")

    except:
        await update.message.reply_text("⚠️ Données macro indisponibles")

# =========================
# NEWS
# =========================
async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = requests.get(
            f"https://newsapi.org/v2/top-headlines?category=business&apiKey={NEWS_API}"
        ).json()

        articles = data["articles"][:3]

        msg = "📰 NEWS\n\n"
        for a in articles:
            msg += f"{a['title']}\n➡️ Impact marché possible\n\n"

        await update.message.reply_text(msg)

    except:
        await update.message.reply_text("⚠️ News indisponibles")

# =========================
# DECISION HEDGE FUND
# =========================
async def decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        btc = requests.get(
            "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true"
        ).json()["bitcoin"]

        btc_change = btc["usd_24h_change"]

        nasdaq = requests.get(
            "https://query1.finance.yahoo.com/v7/finance/quote?symbols=^IXIC"
        ).json()["quoteResponse"]["result"][0]

        nasdaq_change = nasdaq["regularMarketChangePercent"]

        dxy = requests.get(
            "https://query1.finance.yahoo.com/v7/finance/quote?symbols=DX-Y.NYB"
        ).json()["quoteResponse"]["result"][0]["regularMarketPrice"]

        score = 50

        if btc_change > 2:
            score += 15
        elif btc_change < -2:
            score -= 15

        if nasdaq_change > 0:
            score += 10
        else:
            score -= 10

        if dxy > 104:
            score -= 10
        else:
            score += 5

        score = max(0, min(100, score))

        if score > 65:
            signal = "🟢 BUY"
        elif score < 35:
            signal = "🔴 SELL"
        else:
            signal = "🟡 WAIT"

        await update.message.reply_text(f"""
🧠 DÉCISION

Score : {score}/100
Signal : {signal}
""")

    except:
        await update.message.reply_text("❌ Erreur décision")

# =========================
# ALERTES AUTO BTC
# =========================
async def auto_alerts(context: ContextTypes.DEFAULT_TYPE):
    global last_price

    try:
        price = requests.get(
            "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        ).json()["bitcoin"]["usd"]

        if last_price:
            diff = ((price - last_price) / last_price) * 100

            if abs(diff) > 2:
                await context.bot.send_message(
                    chat_id=CHAT_ID,
                    text=f"🚨 BTC MOVE {round(diff,2)}%"
                )

        last_price = price

    except:
        pass

# =========================
# MAIN
# =========================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.bot.delete_webhook(drop_pending_updates=True)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("btc", btc))
    app.add_handler(CommandHandler("nasdaq", nasdaq))
    app.add_handler(CommandHandler("macro", macro))
    app.add_handler(CommandHandler("news", news))
    app.add_handler(CommandHandler("decision", decision))

    app.job_queue.run_repeating(auto_alerts, interval=60, first=10)

    print("BOT LANCÉ 🚀")

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
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
CHAT_ID = os.getenv("CHAT_ID")

# ===== CACHE =====
CACHE = {}

def safe_request(url, key):
    try:
        r = requests.get(url, timeout=3)
        data = r.json()
        CACHE[key] = data
        return data
    except:
        return CACHE.get(key, None)

# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 BOT TRADING ACTIF\n\n"
        "/btc\n/nasdaq\n/macro\n/news\n/decision"
    )

# =========================
# BTC (LIVE + CACHE)
# =========================
async def btc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = safe_request(
        "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true",
        "btc"
    )

    if not data:
        return await update.message.reply_text("⚠️ BTC indisponible")

    try:
        d = data["bitcoin"]
        price = d["usd"]
        change = d["usd_24h_change"]

        trend = "📈 Bullish" if change > 1 else "📉 Bearish" if change < -1 else "➡️ Range"

        await update.message.reply_text(f"""
💰 BTC

Prix : {price}$
Variation : {round(change,2)}%

Trend : {trend}
""")
    except:
        await update.message.reply_text("⚠️ Erreur BTC")

# =========================
# NASDAQ (LIVE + CACHE)
# =========================
async def nasdaq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = safe_request(
        "https://query1.finance.yahoo.com/v7/finance/quote?symbols=^IXIC",
        "nasdaq"
    )

    if not data:
        return await update.message.reply_text("⚠️ Nasdaq indisponible")

    try:
        r = data["quoteResponse"]["result"][0]
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
        await update.message.reply_text("⚠️ Erreur Nasdaq")

# =========================
# MACRO (DXY LIVE)
# =========================
async def macro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = safe_request(
        "https://query1.finance.yahoo.com/v7/finance/quote?symbols=DX-Y.NYB",
        "dxy"
    )

    if not data:
        return await update.message.reply_text("⚠️ Macro indisponible")

    try:
        dxy = data["quoteResponse"]["result"][0]["regularMarketPrice"]

        analyse = "📉 Pression marchés" if dxy > 104 else "📈 Favorable actifs risqués"

        await update.message.reply_text(f"""
🌍 MACRO

💵 Dollar (DXY) : {dxy}

{analyse}
""")
    except:
        await update.message.reply_text("⚠️ Erreur macro")

# =========================
# NEWS
# =========================
async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = safe_request(
        f"https://newsapi.org/v2/top-headlines?category=business&apiKey={NEWS_API}",
        "news"
    )

    if not data:
        return await update.message.reply_text("⚠️ News indisponibles")

    try:
        articles = data.get("articles", [])[:3]

        msg = "📰 NEWS\n\n"

        for a in articles:
            msg += f"{a['title']}\n➡️ Impact marché possible\n\n"

        await update.message.reply_text(msg)
    except:
        await update.message.reply_text("⚠️ Erreur news")

# =========================
# DECISION (SAFE)
# =========================
async def decision(update: Update, context: ContextTypes.DEFAULT_TYPE):

    btc_data = safe_request(
        "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true",
        "btc"
    )

    nasdaq_data = safe_request(
        "https://query1.finance.yahoo.com/v7/finance/quote?symbols=^IXIC",
        "nasdaq"
    )

    dxy_data = safe_request(
        "https://query1.finance.yahoo.com/v7/finance/quote?symbols=DX-Y.NYB",
        "dxy"
    )

    if not btc_data or not nasdaq_data or not dxy_data:
        return await update.message.reply_text("⚠️ Données insuffisantes")

    try:
        btc_change = btc_data["bitcoin"]["usd_24h_change"]
        nasdaq_change = nasdaq_data["quoteResponse"]["result"][0]["regularMarketChangePercent"]
        dxy = dxy_data["quoteResponse"]["result"][0]["regularMarketPrice"]

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

        signal = "🟢 BUY" if score > 65 else "🔴 SELL" if score < 35 else "🟡 WAIT"

        await update.message.reply_text(f"""
🧠 DÉCISION

Score : {score}/100
Signal : {signal}

BTC : {round(btc_change,2)}%
NASDAQ : {round(nasdaq_change,2)}%
DXY : {dxy}
""")
    except:
        await update.message.reply_text("⚠️ Erreur décision")

# =========================
# ALERTES AUTO BTC
# =========================
async def auto_alerts(context: ContextTypes.DEFAULT_TYPE):
    global last_price

    data = safe_request(
        "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd",
        "btc_price"
    )

    if not data:
        return

    try:
        price = data["bitcoin"]["usd"]

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
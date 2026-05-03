import os
import requests
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# =========================
# CACHE
# =========================
CACHE = {}
CACHE_TIME = {}

def fetch(url):
    try:
        return requests.get(url, timeout=3).json()
    except:
        return None

def safe_fetch(key, url):
    data = fetch(url)
    if data:
        CACHE[key] = data
        CACHE_TIME[key] = time.time()
        return data

    return CACHE.get(key)

# =========================
# DATA
# =========================
def get_btc():
    data = safe_fetch(
        "btc",
        "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true"
    )
    try:
        return {
            "price": data["bitcoin"]["usd"],
            "change": data["bitcoin"]["usd_24h_change"]
        }
    except:
        return None

def get_nasdaq():
    data = safe_fetch(
        "nasdaq",
        "https://query1.finance.yahoo.com/v7/finance/quote?symbols=^IXIC"
    )
    try:
        r = data["quoteResponse"]["result"]
        if not r:
            return None
        r = r[0]
        return {
            "price": r.get("regularMarketPrice"),
            "change": r.get("regularMarketChangePercent")
        }
    except:
        return None

def get_dxy():
    data = safe_fetch(
        "dxy",
        "https://query1.finance.yahoo.com/v7/finance/quote?symbols=DX-Y.NYB"
    )
    try:
        r = data["quoteResponse"]["result"]
        if not r:
            return None
        return r[0].get("regularMarketPrice")
    except:
        return None

# =========================
# LOGIQUE
# =========================
def compute_score(btc, nasdaq, dxy):
    score = 50

    if btc["change"] > 2:
        score += 15
    elif btc["change"] < -2:
        score -= 15

    if nasdaq["change"] > 0:
        score += 10
    else:
        score -= 10

    if dxy > 104:
        score -= 10
    else:
        score += 5

    return max(0, min(100, score))

def get_signal(score):
    if score > 65:
        return "🟢 BUY"
    elif score < 35:
        return "🔴 SELL"
    else:
        return "🟡 WAIT"

# =========================
# COMMANDES
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot actif")

async def btc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_btc()
    if not data:
        return await update.message.reply_text("⚠️ BTC indisponible")

    trend = "📈 Bullish" if data["change"] > 0 else "📉 Bearish"

    await update.message.reply_text(f"""
💰 BTC
Prix : {data['price']}$
Variation : {round(data['change'],2)}%
{trend}
""")

async def nasdaq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_nasdaq()
    if not data:
        return await update.message.reply_text("⚠️ Nasdaq indisponible")

    await update.message.reply_text(f"""
📊 NASDAQ
Prix : {data['price']}
Variation : {round(data['change'],2)}%
""")

async def macro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dxy = get_dxy()
    if not dxy:
        return await update.message.reply_text("⚠️ Macro indisponible")

    sentiment = "📉 Risk OFF" if dxy > 104 else "📈 Risk ON"

    await update.message.reply_text(f"""
🌍 MACRO
DXY : {dxy}
{sentiment}
""")

async def decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        btc_data = get_btc()
        nasdaq_data = get_nasdaq()
        dxy = get_dxy()

        if not btc_data or not nasdaq_data or not dxy:
            return await update.message.reply_text("⚠️ Données indisponibles")

        score = compute_score(btc_data, nasdaq_data, dxy)
        signal = get_signal(score)

        await update.message.reply_text(f"""
🧠 DÉCISION

Score : {score}/100
Signal : {signal}

BTC : {round(btc_data['change'],2)}%
NASDAQ : {round(nasdaq_data['change'],2)}%
DXY : {dxy}
""")

    except Exception as e:
        print("Erreur decision:", e)
        await update.message.reply_text("❌ Erreur décision")

# =========================
# ALERTES AUTO
# =========================
last_price = None

async def auto_alert(context: ContextTypes.DEFAULT_TYPE):
    global last_price

    btc = get_btc()
    if not btc:
        return

    price = btc["price"]

    if last_price:
        diff = ((price - last_price) / last_price) * 100
        if abs(diff) > 2:
            await context.bot.send_message(
                chat_id=CHAT_ID,
                text=f"🚨 BTC MOVE {round(diff,2)}%"
            )

    last_price = price

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
    app.add_handler(CommandHandler("decision", decision))

    app.job_queue.run_repeating(auto_alert, interval=60, first=10)

    print("🚀 BOT STABLE LANCÉ")

    app.run_polling()

if __name__ == "__main__":
    main()
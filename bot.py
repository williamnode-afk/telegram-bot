import os
import time
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("TOKEN")
NEWS_API = os.getenv("NEWSAPI_KEY")
CHAT_ID = os.getenv("CHAT_ID")

# =========================
# RESET TELEGRAM
# =========================
def clear_webhook():
    try:
        requests.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook")
    except:
        pass

# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 BOT TRADING ACTIF\n\n"
        "/btc\n/nasdaq\n/macro\n/news\n/decision\n"
        "/correlation\n/timing\n/manipulation\n/risk"
    )

# =========================
# BTC
# =========================
async def btc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = requests.get("https://api.coingecko.com/api/v3/coins/bitcoin").json()
        price = data["market_data"]["current_price"]["usd"]
        change = data["market_data"]["price_change_percentage_24h"]
        volume = data["market_data"]["total_volume"]["usd"]

        manipulation = "🐋 Mouvement suspect" if abs(change) > 5 and volume > 30_000_000_000 else "✅ Stable"

        await update.message.reply_text(
            f"₿ BTC\n\nPrix : {price}$\nVariation : {change:.2f}%\n{manipulation}"
        )
    except:
        await update.message.reply_text("❌ Données BTC indisponibles")

# =========================
# NASDAQ
# =========================
async def nasdaq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        r = requests.get("https://query1.finance.yahoo.com/v7/finance/quote?symbols=^IXIC").json()
        result = r.get("quoteResponse", {}).get("result", [])
        if not result:
            raise Exception()

        data = result[0]
        price = data.get("regularMarketPrice", 0)
        change = data.get("regularMarketChangePercent", 0)

        trend = "🟢 Haussier" if change > 1 else "🔴 Baissier" if change < -1 else "🟡 Stable"

        await update.message.reply_text(
            f"📈 NASDAQ\n\nPrix : {price}\nVariation : {change:.2f}%\n{trend}"
        )
    except:
        await update.message.reply_text("❌ Nasdaq indisponible")

# =========================
# MACRO (Yahoo)
# =========================
async def macro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        gold = requests.get("https://query1.finance.yahoo.com/v7/finance/quote?symbols=GC=F").json()
        brent = requests.get("https://query1.finance.yahoo.com/v7/finance/quote?symbols=BZ=F").json()

        g = gold["quoteResponse"]["result"][0]
        b = brent["quoteResponse"]["result"][0]

        gold_price = g["regularMarketPrice"]
        gold_change = g["regularMarketChangePercent"]
        brent_price = b["regularMarketPrice"]

        score = 0

        gold_state = "🔴 Risque" if gold_change > 0 else "🟢 Confiance"
        score += -1 if gold_change > 0 else 1

        brent_state = "🔴 Inflation" if brent_price > 85 else "🟢 Stable"
        score += -1 if brent_price > 85 else 1

        direction = "🟢 BULLISH" if score >= 2 else "🔴 BEARISH" if score <= -2 else "🟡 NEUTRE"

        await update.message.reply_text(
            f"🌍 MACRO\n\n🟡 Or : {gold_price}$ → {gold_state}\n"
            f"🛢️ Brent : {brent_price}$ → {brent_state}\n\n"
            f"📊 Direction : {direction}"
        )

    except:
        await update.message.reply_text("❌ Données macro indisponibles")

# =========================
# NEWS
# =========================
def analyse_news(t):
    t = t.lower()
    if "oil" in t: return "🛢️ pétrole"
    if "inflation" in t: return "📉 marchés"
    if "bitcoin" in t: return "₿ crypto"
    if "tech" in t: return "📈 Nasdaq"
    if "war" in t: return "⚠️ or"
    return "⚪ neutre"

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        url = f"https://newsapi.org/v2/top-headlines?category=business&language=en&apiKey={NEWS_API}"
        data = requests.get(url).json()

        msg = "📰 NEWS\n\n"
        for a in data.get("articles", [])[:3]:
            title = a["title"]
            impact = analyse_news(title)
            msg += f"{title}\n➡️ {impact}\n\n"

        await update.message.reply_text(msg)
    except:
        await update.message.reply_text("❌ News indisponibles")

# =========================
# DECISION
# =========================
async def decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        score = 50

        btc = requests.get("https://api.coingecko.com/api/v3/coins/bitcoin").json()
        btc_change = btc["market_data"]["price_change_percentage_24h"]

        nasdaq = requests.get("https://query1.finance.yahoo.com/v7/finance/quote?symbols=^IXIC").json()
        n_change = nasdaq["quoteResponse"]["result"][0]["regularMarketChangePercent"]

        score += 15 if btc_change > 1 else -15 if btc_change < -1 else 0
        score += 10 if n_change > 0.5 else -10 if n_change < -0.5 else 0

        signal = "🟢 ACHAT" if score >= 70 else "🔴 VENTE" if score <= 30 else "🟡 ATTENTE"
        timing = "🎯 Bon timing" if score > 65 else "⏳ Attente"

        await update.message.reply_text(
            f"🧠 DÉCISION\n\nScore : {score}/100\nSignal : {signal}\n{timing}"
        )

    except:
        await update.message.reply_text("❌ Erreur décision")

# =========================
# AUTRES COMMANDES
# =========================
async def correlation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        btc = requests.get("https://api.coingecko.com/api/v3/coins/bitcoin").json()
        b = btc["market_data"]["price_change_percentage_24h"]

        nasdaq = requests.get("https://query1.finance.yahoo.com/v7/finance/quote?symbols=^IXIC").json()
        n = nasdaq["quoteResponse"]["result"][0]["regularMarketChangePercent"]

        result = "🟢 Alignement" if (b > 0 and n > 0) else "🔴 Alignement" if (b < 0 and n < 0) else "⚠️ Divergence"

        await update.message.reply_text(f"BTC {b:.2f}% | Nasdaq {n:.2f}%\n{result}")
    except:
        await update.message.reply_text("❌ Erreur corrélation")

async def timing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        btc = requests.get("https://api.coingecko.com/api/v3/coins/bitcoin").json()
        change = btc["market_data"]["price_change_percentage_24h"]

        msg = "🎯 BUY possible" if change > 2 else "🔴 SELL possible" if change < -2 else "⏳ Attente"
        await update.message.reply_text(msg)
    except:
        await update.message.reply_text("❌ Erreur timing")

async def manipulation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        btc = requests.get("https://api.coingecko.com/api/v3/coins/bitcoin").json()
        c = btc["market_data"]["price_change_percentage_24h"]
        v = btc["market_data"]["total_volume"]["usd"]

        msg = "🐋 Suspicion manipulation" if abs(c) > 5 and v > 30_000_000_000 else "✅ Normal"
        await update.message.reply_text(msg)
    except:
        await update.message.reply_text("❌ Erreur")

async def risk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💰 Gestion du risque\n\n1-2% max par trade\nToujours SL\nPas d'overtrade"
    )

# =========================
# ALERTES AUTO
# =========================
async def alertes(context: ContextTypes.DEFAULT_TYPE):
    try:
        btc = requests.get("https://api.coingecko.com/api/v3/coins/bitcoin").json()
        change = btc["market_data"]["price_change_percentage_24h"]

        if abs(change) > 4:
            await context.bot.send_message(
                chat_id=CHAT_ID,
                text=f"🚨 BTC mouvement : {change:.2f}%"
            )
    except:
        pass

# =========================
# MAIN
# =========================
def main():
    clear_webhook()
    time.sleep(2)

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("btc", btc))
    app.add_handler(CommandHandler("nasdaq", nasdaq))
    app.add_handler(CommandHandler("macro", macro))
    app.add_handler(CommandHandler("news", news))
    app.add_handler(CommandHandler("decision", decision))
    app.add_handler(CommandHandler("correlation", correlation))
    app.add_handler(CommandHandler("timing", timing))
    app.add_handler(CommandHandler("manipulation", manipulation))
    app.add_handler(CommandHandler("risk", risk))

    app.job_queue.run_repeating(alertes, interval=900, first=10)

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
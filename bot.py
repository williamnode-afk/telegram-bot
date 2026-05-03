import os
import time
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("TOKEN")
NEWS_API = os.getenv("NEWSAPI_KEY")
FMP_API = os.getenv("FMP_API")
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
        "Commandes :\n"
        "/btc → analyse Bitcoin\n"
        "/nasdaq → analyse Nasdaq\n"
        "/macro → analyse macro\n"
        "/news → actualités\n"
        "/decision → décision marché"
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

        score = 50
        if change > 2:
            score += 20
        elif change < -2:
            score -= 20

        manipulation = "🐋 Mouvement suspect" if abs(change) > 5 and volume > 30_000_000_000 else "✅ Stable"

        signal = "🟢 BUY" if score >= 70 else "🔴 SELL" if score <= 30 else "🟡 WAIT"

        await update.message.reply_text(
            f"₿ BTC\n\nPrix : {price}$\nVariation : {change:.2f}%\n\n"
            f"📊 Score : {score}/100\n🎯 Signal : {signal}\n{manipulation}"
        )

    except:
        await update.message.reply_text("❌ Erreur BTC")

# =========================
# NASDAQ
# =========================
async def nasdaq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        r = requests.get("https://query1.finance.yahoo.com/v7/finance/quote?symbols=^IXIC").json()
        data = r["quoteResponse"]["result"][0]

        price = data["regularMarketPrice"]
        change = data["regularMarketChangePercent"]

        trend = "🟢 Haussier" if change > 1 else "🔴 Baissier" if change < -1 else "🟡 Stable"

        await update.message.reply_text(
            f"📈 NASDAQ\n\nPrix : {price}\nVariation : {change:.2f}%\n\n🎯 {trend}"
        )

    except:
        await update.message.reply_text("❌ Erreur Nasdaq")

# =========================
# MACRO
# =========================
async def macro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        gold = requests.get(f"https://financialmodelingprep.com/api/v3/quote/GCUSD?apikey={FMP_API}").json()
        brent = requests.get(f"https://financialmodelingprep.com/api/v3/quote/BZUSD?apikey={FMP_API}").json()

        gold_price = gold[0]["price"] if gold else 0
        brent_price = brent[0]["price"] if brent else 0

        gold_state = "🟡 Peur marché" if gold_price > 2000 else "🟢 Confiance"
        brent_state = "🔥 Inflation" if brent_price > 85 else "❄️ Inflation faible"

        await update.message.reply_text(
            f"🌍 MACRO\n\n🟡 Or : {gold_price}$ → {gold_state}\n"
            f"🛢️ Brent : {brent_price}$ → {brent_state}"
        )

    except:
        await update.message.reply_text("❌ Erreur macro")

# =========================
# NEWS + IMPACT
# =========================
def analyser_impact_news(t):
    t = t.lower()

    if "oil" in t or "ormuz" in t:
        return "🛢️ Impact : pétrole (Brent)"
    if "inflation" in t:
        return "📉 Impact : marchés sous pression"
    if "crypto" in t or "bitcoin" in t:
        return "₿ Impact : crypto"
    if "tech" in t or "nasdaq" in t:
        return "📈 Impact : tech"
    if "war" in t:
        return "⚠️ Impact : fuite vers l’or"

    return "⚪ Impact neutre"

def get_news_fr():
    url = f"https://newsapi.org/v2/top-headlines?category=business&language=en&apiKey={NEWS_API}"
    r = requests.get(url)
    data = r.json()

    articles = data.get("articles", [])[:3]

    result = []
    for a in articles:
        title = a.get("title", "")
        impact = analyser_impact_news(title)
        result.append(f"📰 {title}\n➡️ {impact}")

    return result

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        news_list = get_news_fr()

        msg = "📰 NEWS\n\n"
        for n in news_list:
            msg += f"{n}\n\n"

        await update.message.reply_text(msg)

    except:
        await update.message.reply_text("❌ Erreur news")

# =========================
# DECISION (IA)
# =========================
async def decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        score = 50
        msg = "🧠 DÉCISION MARCHÉ\n\n"

        btc = requests.get("https://api.coingecko.com/api/v3/coins/bitcoin").json()
        btc_change = btc["market_data"]["price_change_percentage_24h"]
        btc_volume = btc["market_data"]["total_volume"]["usd"]

        nasdaq = requests.get("https://query1.finance.yahoo.com/v7/finance/quote?symbols=^IXIC").json()
        n_change = nasdaq["quoteResponse"]["result"][0]["regularMarketChangePercent"]

        if btc_change > 1: score += 15
        elif btc_change < -1: score -= 15

        if n_change > 0.5: score += 15
        elif n_change < -0.5: score -= 15

        manipulation = "🐋 Mouvement suspect" if abs(btc_change) > 5 and btc_volume > 30_000_000_000 else "✅ Stable"

        if score >= 75:
            decision = "🟢 BUY FORT"
        elif score >= 60:
            decision = "🟢 BUY"
        elif score <= 30:
            decision = "🔴 SELL FORT"
        elif score <= 40:
            decision = "🔴 SELL"
        else:
            decision = "🟡 ATTENTE"

        timing = "🎯 Bon moment" if score > 65 and btc_change > 1 else "⏳ Attente"

        msg += f"📊 Score : {score}/100\n🎯 {decision}\n{manipulation}\n⏱ {timing}"

        await update.message.reply_text(msg)

    except:
        await update.message.reply_text("❌ Erreur décision")

# =========================
# ALERTES AUTO
# =========================
async def alertes(context: ContextTypes.DEFAULT_TYPE):
    try:
        msg = "🚨 ALERTES\n\n"

        btc = requests.get("https://api.coingecko.com/api/v3/coins/bitcoin").json()
        change = btc["market_data"]["price_change_percentage_24h"]

        if abs(change) > 3:
            msg += f"₿ BTC mouvement : {change:.2f}%\n\n"

        if msg != "🚨 ALERTES\n\n":
            await context.bot.send_message(chat_id=CHAT_ID, text=msg)

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

    app.job_queue.run_repeating(alertes, interval=900, first=10)

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
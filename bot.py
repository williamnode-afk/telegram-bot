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
        "Commandes disponibles :\n"
        "/btc\n/nasdaq\n/macro\n/news\n/decision"
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

    except Exception as e:
        print(e)
        await update.message.reply_text("❌ Données BTC indisponibles")

# =========================
# NASDAQ
# =========================
async def nasdaq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        r = requests.get("https://query1.finance.yahoo.com/v7/finance/quote?symbols=^IXIC").json()
        result = r.get("quoteResponse", {}).get("result", [])

        if not result:
            raise Exception("Pas de data Nasdaq")

        data = result[0]
        price = data.get("regularMarketPrice", 0)
        change = data.get("regularMarketChangePercent", 0)

        trend = "🟢 Haussier" if change > 1 else "🔴 Baissier" if change < -1 else "🟡 Stable"

        await update.message.reply_text(
            f"📈 NASDAQ\n\nPrix : {price}\nVariation : {change:.2f}%\n\n{trend}"
        )

    except Exception as e:
        print(e)
        await update.message.reply_text("❌ Données Nasdaq indisponibles")

# =========================
# MACRO
# =========================
async def macro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        gold = requests.get(f"https://financialmodelingprep.com/api/v3/quote/GCUSD?apikey={FMP_API}").json()
        brent = requests.get(f"https://financialmodelingprep.com/api/v3/quote/BZUSD?apikey={FMP_API}").json()

        if not gold or not brent:
            raise Exception("API vide")

        gold_price = gold[0].get("price", 0)
        brent_price = brent[0].get("price", 0)

        gold_state = "🟡 Peur marché" if gold_price > 2000 else "🟢 Confiance"
        brent_state = "🔥 Inflation" if brent_price > 85 else "❄️ Inflation faible"

        await update.message.reply_text(
            f"🌍 MACRO\n\n🟡 Or : {gold_price}$ → {gold_state}\n🛢️ Brent : {brent_price}$ → {brent_state}"
        )

    except Exception as e:
        print(e)
        await update.message.reply_text("❌ Données macro indisponibles")

# =========================
# NEWS
# =========================
def traduire(t):
    t = t.replace("oil", "pétrole")
    t = t.replace("war", "guerre")
    t = t.replace("market", "marché")
    return t

def analyser_impact_news(t):
    t = t.lower()

    if "pétrole" in t:
        return "🛢️ Impact : pétrole"
    if "inflation" in t:
        return "📉 Impact : marchés baissiers"
    if "bitcoin" in t:
        return "₿ Impact : crypto"
    if "tech" in t:
        return "📈 Impact : Nasdaq"
    if "guerre" in t:
        return "⚠️ Impact : fuite vers l’or"

    return "⚪ Impact neutre"

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        url = f"https://newsapi.org/v2/top-headlines?category=business&language=en&apiKey={NEWS_API}"
        data = requests.get(url).json()

        articles = data.get("articles", [])[:3]

        msg = "📰 ACTUALITÉS\n\n"

        for a in articles:
            title = traduire(a.get("title", ""))
            impact = analyser_impact_news(title)

            msg += f"{title}\n➡️ {impact}\n\n"

        await update.message.reply_text(msg)

    except Exception as e:
        print(e)
        await update.message.reply_text("❌ Erreur news")

# =========================
# DECISION
# =========================
async def decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        score = 50

        btc = requests.get("https://api.coingecko.com/api/v3/coins/bitcoin").json()
        btc_change = btc["market_data"]["price_change_percentage_24h"]

        try:
            nasdaq = requests.get("https://query1.finance.yahoo.com/v7/finance/quote?symbols=^IXIC").json()
            n_change = nasdaq["quoteResponse"]["result"][0]["regularMarketChangePercent"]
        except:
            n_change = 0

        if btc_change > 1:
            score += 15
        elif btc_change < -1:
            score -= 15

        if n_change > 0.5:
            score += 10
        elif n_change < -0.5:
            score -= 10

        if score >= 70:
            signal = "🟢 ACHAT"
        elif score <= 30:
            signal = "🔴 VENTE"
        else:
            signal = "🟡 ATTENTE"

        timing = "🎯 Bon timing" if score > 65 else "⏳ Attendre"

        await update.message.reply_text(
            f"🧠 DÉCISION\n\nScore : {score}/100\nSignal : {signal}\n{timing}"
        )

    except Exception as e:
        print(e)
        await update.message.reply_text("❌ Erreur décision")

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

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
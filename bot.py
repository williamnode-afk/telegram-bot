import requests
import time
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("TOKEN")
NEWS_API = os.getenv("NEWSAPI_KEY")
CHAT_ID = os.getenv("CHAT_ID")

# ================= SAFE REQUEST + CACHE =================
CACHE = {}

def safe_request(url, key):
    try:
        if key in CACHE and time.time() - CACHE[key]["time"] < 60:
            return CACHE[key]["data"]

        r = requests.get(url, timeout=5)
        data = r.json()

        CACHE[key] = {"data": data, "time": time.time()}
        return data

    except Exception as e:
        print("API ERROR:", e)
        return CACHE.get(key, {}).get("data", None)

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 BOT TRADING HEDGE FUND\n\n"
        "/btc\n/nasdaq\n/macro\n/news\n/decision\n/central"
    )

# ================= BTC =================
async def btc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = safe_request("https://api.coingecko.com/api/v3/coins/bitcoin", "btc")

    if not data:
        await update.message.reply_text("⚠️ BTC indisponible")
        return

    try:
        price = data["market_data"]["current_price"]["usd"]
        change = data["market_data"]["price_change_percentage_24h"]
        volume = data["market_data"]["total_volume"]["usd"]

        manipulation = abs(change) > 5 and volume > 30_000_000_000

        await update.message.reply_text(
            f"₿ BTC\n\nPrix : {price}$\nVariation : {change:.2f}%\n"
            f"🐋 Manipulation : {'Oui' if manipulation else 'Non'}"
        )
    except:
        await update.message.reply_text("⚠️ Erreur BTC")

# ================= NASDAQ =================
async def nasdaq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = safe_request("https://query1.finance.yahoo.com/v7/finance/quote?symbols=^IXIC", "nasdaq")

    if not data:
        await update.message.reply_text("⚠️ Nasdaq indisponible")
        return

    try:
        result = data.get("quoteResponse", {}).get("result", [])
        if not result:
            raise Exception()

        d = result[0]
        price = d.get("regularMarketPrice", 0)
        change = d.get("regularMarketChangePercent", 0)

        trend = "🟢 Haussier" if change > 1 else "🔴 Baissier" if change < -1 else "🟡 Stable"

        await update.message.reply_text(
            f"📈 NASDAQ\n\nPrix : {price}\nVariation : {change:.2f}%\n{trend}"
        )
    except:
        await update.message.reply_text("⚠️ Erreur Nasdaq")

# ================= MACRO =================
async def macro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    gold = safe_request("https://query1.finance.yahoo.com/v7/finance/quote?symbols=GC=F", "gold")
    brent = safe_request("https://query1.finance.yahoo.com/v7/finance/quote?symbols=BZ=F", "brent")

    if not gold or not brent:
        await update.message.reply_text("⚠️ Macro indisponible")
        return

    try:
        g = gold.get("quoteResponse", {}).get("result", [{}])[0]
        b = brent.get("quoteResponse", {}).get("result", [{}])[0]

        gold_change = g.get("regularMarketChangePercent", 0)
        brent_price = b.get("regularMarketPrice", 0)

        score = (-1 if gold_change > 0 else 1) + (-1 if brent_price > 85 else 1)
        direction = "🟢 BULLISH" if score >= 2 else "🔴 BEARISH" if score <= -2 else "🟡 NEUTRE"

        await update.message.reply_text(
            f"🌍 MACRO\n\nOr Δ : {gold_change:.2f}%\nBrent : {brent_price}$\n\nDirection : {direction}"
        )
    except:
        await update.message.reply_text("⚠️ Erreur macro")

# ================= NEWS =================
async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = f"https://newsapi.org/v2/top-headlines?category=business&language=en&pageSize=3&apiKey={NEWS_API}"
    data = safe_request(url, "news")

    if not data:
        await update.message.reply_text("⚠️ News indisponibles")
        return

    try:
        msg = "📰 NEWS\n\n"
        for a in data.get("articles", [])[:3]:
            msg += f"{a.get('title','...')}\n\n"
        await update.message.reply_text(msg)
    except:
        await update.message.reply_text("⚠️ Erreur news")

# ================= DECISION =================
async def decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        score = 50

        btc = safe_request("https://api.coingecko.com/api/v3/coins/bitcoin", "btc")
        nasdaq = safe_request("https://query1.finance.yahoo.com/v7/finance/quote?symbols=^IXIC", "nasdaq")

        btc_change = btc.get("market_data", {}).get("price_change_percentage_24h", 0) if btc else 0
        n_res = nasdaq.get("quoteResponse", {}).get("result", []) if nasdaq else []
        n_change = n_res[0].get("regularMarketChangePercent", 0) if n_res else 0

        score += 15 if btc_change > 1 else -15 if btc_change < -1 else 0
        score += 10 if n_change > 0.5 else -10 if n_change < -0.5 else 0

        signal = "🟢 ACHAT" if score >= 70 else "🔴 VENTE" if score <= 30 else "🟡 ATTENTE"

        await update.message.reply_text(f"🧠 DÉCISION\n\nScore : {score}/100\nSignal : {signal}")
    except:
        await update.message.reply_text("⚠️ Erreur décision")

# ================= BOT CENTRAL HEDGE FUND =================
async def central(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        score = 50

        btc = safe_request("https://api.coingecko.com/api/v3/coins/bitcoin", "btc")
        btc_change = btc.get("market_data", {}).get("price_change_percentage_24h", 0) if btc else 0
        volume = btc.get("market_data", {}).get("total_volume", {}).get("usd", 0) if btc else 0

        nasdaq = safe_request("https://query1.finance.yahoo.com/v7/finance/quote?symbols=^IXIC", "nasdaq")
        n_res = nasdaq.get("quoteResponse", {}).get("result", []) if nasdaq else []
        n_change = n_res[0].get("regularMarketChangePercent", 0) if n_res else 0

        gold = safe_request("https://query1.finance.yahoo.com/v7/finance/quote?symbols=GC=F", "gold")
        brent = safe_request("https://query1.finance.yahoo.com/v7/finance/quote?symbols=BZ=F", "brent")

        g = gold.get("quoteResponse", {}).get("result", [{}])[0] if gold else {}
        b = brent.get("quoteResponse", {}).get("result", [{}])[0] if brent else {}

        gold_change = g.get("regularMarketChangePercent", 0)
        brent_price = b.get("regularMarketPrice", 0)

        score += 20 if btc_change > 2 else -20 if btc_change < -2 else 0
        score += 15 if n_change > 1 else -15 if n_change < -1 else 0
        score += -10 if gold_change > 0 else 10
        score += -5 if brent_price > 85 else 5

        manipulation = abs(btc_change) > 5 and volume > 30_000_000_000
        divergence = (btc_change > 0 and n_change < 0) or (btc_change < 0 and n_change > 0)

        if manipulation or divergence:
            signal = "⛔ PAS DE TRADE"
            timing = "⚠️ Marché instable"
        else:
            if score >= 80:
                signal = "🟢 BUY FORT"
            elif score >= 65:
                signal = "🟢 BUY"
            elif score <= 20:
                signal = "🔴 SELL FORT"
            elif score <= 45:
                signal = "🔴 SELL"
            else:
                signal = "🟡 ATTENTE"
            timing = "🎯 Entrée possible"

        await update.message.reply_text(
            f"🧠 BOT CENTRAL\n\nScore : {score}/100\nSignal : {signal}\n{timing}"
        )
    except:
        await update.message.reply_text("⚠️ Erreur central")

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("btc", btc))
    app.add_handler(CommandHandler("nasdaq", nasdaq))
    app.add_handler(CommandHandler("macro", macro))
    app.add_handler(CommandHandler("news", news))
    app.add_handler(CommandHandler("decision", decision))
    app.add_handler(CommandHandler("central", central))

    app.run_polling()

if __name__ == "__main__":
    main()
import os
import requests
import asyncio
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ================= CONFIG =================
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
FMP_API = os.getenv("FMP_API")

last_price = None

# ================= LOGS =================
logging.basicConfig(level=logging.INFO)

# ================= SAFE REQUEST =================
def safe_get(url):
    try:
        r = requests.get(url, timeout=5)
        return r.json()
    except Exception as e:
        logging.error(f"API ERROR: {e}")
        return None

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 BOT TRADING ACTIF")

# ================= BTC =================
async def btc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = safe_get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd")

    if not data:
        await update.message.reply_text("❌ BTC indisponible")
        return

    price = data.get("bitcoin", {}).get("usd", 0)

    await update.message.reply_text(
        f"💰 BTC\n\nPrix : {price}$\n\n📊 Analyse : Stable"
    )

# ================= NASDAQ =================
async def nasdaq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = safe_get("https://query1.finance.yahoo.com/v7/finance/quote?symbols=^IXIC")

    if not data:
        await update.message.reply_text("⚠️ Nasdaq indisponible")
        return

    try:
        result = data.get("quoteResponse", {}).get("result", [])
        d = result[0]

        price = d.get("regularMarketPrice", 0)
        change = d.get("regularMarketChangePercent", 0)

        sens = "📈 Hausse" if change > 0 else "📉 Baisse"

        await update.message.reply_text(
            f"📊 NASDAQ\n\nPrix : {price}\nVariation : {round(change,2)}%\n\n{sens}"
        )
    except:
        await update.message.reply_text("⚠️ Erreur Nasdaq")

# ================= MACRO =================
async def macro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        gold_data = safe_get(f"https://financialmodelingprep.com/api/v3/quote/XAUUSD?apikey={FMP_API}")
        oil_data = safe_get(f"https://financialmodelingprep.com/api/v3/quote/CLUSD?apikey={FMP_API}")
        dxy_data = safe_get("https://query1.finance.yahoo.com/v7/finance/quote?symbols=DX-Y.NYB")

        if not gold_data or not oil_data or not dxy_data:
            raise Exception()

        gold = gold_data[0]["price"]
        oil = oil_data[0]["price"]
        dxy = dxy_data["quoteResponse"]["result"][0]["regularMarketPrice"]

        await update.message.reply_text(
            f"🌍 MACRO\n\n🟡 Or : {gold}\n🛢 Brent : {oil}\n💵 Dollar : {dxy}"
        )

    except:
        await update.message.reply_text("⚠️ Macro indisponible")

# ================= NEWS =================
async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📰 News actives (OK)")

# ================= DECISION =================
async def decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🧠 DÉCISION\n\nScore : 50/100\nSignal : ⚠️ ATTENTE"
    )

# ================= ALERTES AUTO BTC =================
async def auto_alerts(app):
    global last_price

    while True:
        try:
            data = safe_get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd")

            if not data:
                await asyncio.sleep(60)
                continue

            price = data["bitcoin"]["usd"]

            if last_price is not None:
                diff = ((price - last_price) / last_price) * 100

                if diff > 1:
                    await app.bot.send_message(
                        chat_id=CHAT_ID,
                        text=f"🚀 BTC PUMP +{round(diff,2)}%"
                    )

                elif diff < -1:
                    await app.bot.send_message(
                        chat_id=CHAT_ID,
                        text=f"📉 BTC DROP {round(diff,2)}%"
                    )

                if abs(diff) > 2:
                    await app.bot.send_message(
                        chat_id=CHAT_ID,
                        text="🐋 MOUVEMENT SUSPECT (manipulation possible)"
                    )

            last_price = price

        except Exception as e:
            logging.error(f"ALERT ERROR: {e}")

        await asyncio.sleep(60)

# ================= MAIN =================
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # reset webhook (anti conflit)
    await app.bot.delete_webhook(drop_pending_updates=True)

    # commandes
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("btc", btc))
    app.add_handler(CommandHandler("nasdaq", nasdaq))
    app.add_handler(CommandHandler("macro", macro))
    app.add_handler(CommandHandler("news", news))
    app.add_handler(CommandHandler("decision", decision))

    # alertes auto
    asyncio.create_task(auto_alerts(app))

    logging.info("✅ BOT LANCÉ")
    await app.run_polling()

# ================= START =================
if __name__ == "__main__":
    asyncio.run(main())
import os
import logging
import httpx
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Logs (important pour Render)
logging.basicConfig(level=logging.INFO)

# Récupération du token
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise ValueError("TOKEN manquant")

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 Bot trading ELITE actif !")

# /btc
async def btc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            data = response.json()

        price = data["bitcoin"]["usd"]

        await update.message.reply_text(f"💰 BTC = {price}$")

    except Exception as e:
        await update.message.reply_text("❌ Erreur récupération prix BTC")
        print(e)

# MAIN
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("btc", btc))

    print("Bot lancé 🚀")

    await app.run_polling()

# Lancement (IMPORTANT)
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
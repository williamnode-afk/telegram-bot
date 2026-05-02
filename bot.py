import requests
import asyncio
import os

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# 🔐 Variables d'environnement (Render)
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")  # optionnel

if not TOKEN:
    raise ValueError("TOKEN manquant")

# ------------------------
# COMMANDES
# ------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 Bot actif et prêt !")

async def btc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
    data = requests.get(url).json()
    price = data["bitcoin"]["usd"]

    await update.message.reply_text(f"💰 BTC = {price}$")

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📰 News du marché (à venir)")

async def macro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 Macro économie (à venir)")

# ------------------------
# AUTO ALERT
# ------------------------

async def auto_alert(app):
    while True:
        try:
            if CHAT_ID:
                await app.bot.send_message(
                    chat_id=CHAT_ID,
                    text="🚨 ALERTE MARCHE : surveillance active"
                )
        except Exception as e:
            print("Erreur auto alert :", e)

        await asyncio.sleep(3600)  # toutes les 1h

# ------------------------
# MAIN
# ------------------------

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # commandes
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("btc", btc))
    app.add_handler(CommandHandler("news", news))
    app.add_handler(CommandHandler("macro", macro))

    # tâche automatique
    asyncio.create_task(auto_alert(app))

    print("✅ Bot en ligne")

    await app.run_polling()

# lancement
if __name__ == "__main__":
    asyncio.run(main())

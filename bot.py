import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("token")
CHAT_ID = int(os.getenv("chat_id"))

# ===== COMMANDES =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 Bot actif et prêt !")

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📰 News marché (bientôt connecté API)")

async def btc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💰 BTC : 67 000$ (exemple)")

async def macro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📉 Macro : données en attente API")

# ===== BOT =====

async def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("news", news))
    app.add_handler(CommandHandler("btc", btc))
    app.add_handler(CommandHandler("macro", macro))

    print("Bot en ligne...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())

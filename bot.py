import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("TOKEN")

# ===== COMMANDES =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 Bot actif et prêt !")
    print("STAR COMMAND RECEIVED")

async def btc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💰 BTC : 67 000$ (exemple)")

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📰 News marché (à connecter plus tard)")

async def macro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🌍 Macro data (à venir)")

# ===== MAIN =====


async def main():
    print("BOT STARTED")
    print("TOKEN =", TOKEN)
    app = ApplicationBuilder().token(TOKEN).build()

    # AJOUT DES COMMANDES (IMPORTANT)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("btc", btc))
    app.add_handler(CommandHandler("news", news))
    app.add_handler(CommandHandler("macro", macro))

    print("BOT RUNNING")
   
    await app.run_polling(drop_pending_updates=True)

# ===== LANCEMENT =====

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
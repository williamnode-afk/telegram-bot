import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# 🔑 Variables d'environnement
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TOKEN:
    raise ValueError("TOKEN manquant")

# ---- COMMANDES ----

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot actif et prêt !")

async def btc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💰 BTC : 67 000$ (exemple)")

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📰 News du marché (à connecter plus tard)")

async def macro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🌍 Macro économie (à venir)")

# ---- AUTO MESSAGE ----

async def auto_alert(app):
    while True:
        try:
            await app.bot.send_message(
                chat_id=CHAT_ID,
                text="🚨 ALERTE MARCHÉ : surveillance active"
            )
        except Exception as e:
            print(f"Erreur envoi message : {e}")

        await asyncio.sleep(3600)  # toutes les 1h

# ---- MAIN ----

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("btc", btc))
    app.add_handler(CommandHandler("news", news))
    app.add_handler(CommandHandler("macro", macro))

    print("Bot en ligne 🚀")

    # lancer la tâche après démarrage
    async def post_init(app):
        asyncio.create_task(auto_alert(app))

    app.post_init = post_init

    await app.run_polling()

# ---- RUN ----

if __name__ == "__main__":
    asyncio.run(main())

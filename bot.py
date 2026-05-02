from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "8705712461:AAFATHhFqzyIX2APIGAKGOxn_xuuFZaYusc"

# Commande /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Commande /start reçue")
    await update.message.reply_text("🔥 Bot actif et prêt !")

# Commande /news
async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Commande /news reçue")
    await update.message.reply_text("📰 News du marché (à connecter plus tard)")

# Commande /btc
async def btc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Commande /btc reçue")
    await update.message.reply_text("💰 BTC : 67 000$ (exemple)")

# Création app
app = ApplicationBuilder().token(TOKEN).build()

# Ajout des commandes
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("news", news))
app.add_handler(CommandHandler("btc", btc))

print("Bot en écoute...")
app.run_polling()
import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Variables d'environnement
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TOKEN:
    raise ValueError("TOKEN manquant")

# ========================
# COMMANDES
# ========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot actif et prêt !")

async def btc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💰 BTC : 67 000$ (exemple)")

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📰 News du marché (à connecter plus tard)")

async def macro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 Macro économie (à venir)")

# ========================
# AUTO MESSAGE
# ========================

async def auto_alert(app):
    while True:
        try:
            await app.bot.send_message(
                chat_id=CHAT_ID,
                text="🚨 ALERTE MARCHE : surveillance active"
            )
        except Exception as e:
            print("Erreur envoi message:", e)

        await asyncio.sleep(3600)  # 1 heure

# ========================
# MAIN
# ========================

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # commandes
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("btc", btc))
    app.add_handler(CommandHandler("news", news))
    app.add_handler(CommandHandler("macro", macro))

    # lancer tâche auto
    asyncio.get_event_loop().create_task(auto_alert(app))

    print("Bot en ligne 🚀")

    app.run_polling()


if __name__ == "__main__":
    main()

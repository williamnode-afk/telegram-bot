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
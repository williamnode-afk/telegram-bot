import os
import requests
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# =========================
# CONFIG
# =========================
TOKEN = os.getenv("TOKEN")

# =========================
# LOGGING
# =========================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# =========================
# SAFE FETCH
# =========================
def fetch(url):
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            return r.json()
        return None
    except:
        return None

# =========================
# BTC PRICE
# =========================
def get_btc():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
    data = fetch(url)

    if not data or "bitcoin" not in data:
        return None

    return data["bitcoin"]["usd"]

# =========================
# COMMANDS
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot actif ✅")

async def btc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    price = get_btc()

    if price is None:
        await update.message.reply_text("Erreur récupération BTC ❌")
        return

    await update.message.reply_text(f"BTC : {price}$")

# =========================
# ERROR HANDLER
# =========================
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error(msg="Exception:", exc_info=context.error)

# =========================
# MAIN
# =========================
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("btc", btc))

    app.add_error_handler(error_handler)

    print("BOT LANCÉ ✅")

    # ⚠️ IMPORTANT: UNE SEULE INSTANCE
    app.run_polling()
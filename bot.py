import os
import time
import requests
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("TOKEN")
CRYPTO_API = os.getenv("CRYPTO_API")
FMP_API = os.getenv("FMP_API")

# =========================
# FIX TELEGRAM
# =========================
def clear_webhook():
    try:
        requests.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook")
    except:
        pass

# =========================
# DATA
# =========================
history = {
    "BTC": [],
    "NASDAQ": [],
    "GOLD": [],
    "BRENT": []
}

# =========================
# FETCH PRICES
# =========================
def get_price(symbol):
    try:
        url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}"
        return requests.get(url).json()["quoteResponse"]["result"][0]["regularMarketPrice"]
    except:
        return None

def get_btc():
    try:
        return requests.get(
            "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        ).json()["bitcoin"]["usd"]
    except:
        return None

# =========================
# INDICATORS
# =========================
def rsi(prices):
    if len(prices) < 10:
        return None
    gains, losses = [], []
    for i in range(1, len(prices)):
        diff = prices[i] - prices[i-1]
        if diff > 0:
            gains.append(diff)
        else:
            losses.append(abs(diff))
    avg_gain = sum(gains)/len(gains) if gains else 0.01
    avg_loss = sum(losses)/len(losses) if losses else 0.01
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# =========================
# SCORE
# =========================
def score(prices):
    s = 50
    if prices[-1] > prices[0]:
        s += 15
    if prices[-1] >= max(prices[-10:]):
        s += 15
    if prices[-1] <= min(prices[-10:]):
        s -= 15

    r = rsi(prices)
    if r:
        if r < 30:
            s += 10
        elif r > 70:
            s -= 10

    return max(0, min(100, s))

def signal(score):
    if score >= 70:
        return "🟢 BUY"
    elif score <= 30:
        return "🔴 SELL"
    return "⚪ WAIT"

# =========================
# MARKET CONTEXT
# =========================
def market_context():
    if len(history["BTC"]) < 10:
        return "UNKNOWN"

    btc = history["BTC"][-1] - history["BTC"][0]
    nasdaq = history["NASDAQ"][-1] - history["NASDAQ"][0]

    if btc > 0 and nasdaq > 0:
        return "🟢 RISK-ON"
    elif btc < 0 and nasdaq < 0:
        return "🔴 RISK-OFF"
    return "⚪ MIXED"

# =========================
# NEWS
# =========================
def get_news():
    try:
        url = f"https://financialmodelingprep.com/api/v3/stock_news?limit=3&apikey={FMP_API}"
        data = requests.get(url).json()

        news = []
        for n in data:
            news.append(f"📰 {n['title']}")

        return "\n".join(news)
    except:
        return "❌ Erreur news"

# =========================
# COMMANDES
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 BOT NEWS PRO ACTIF")

    chat_id = update.effective_chat.id
    context.job_queue.run_repeating(scan, interval=60, first=5, chat_id=chat_id)

async def btc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    price = get_btc()
    await update.message.reply_text(f"₿ BTC: {price}$")

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    n = get_news()
    await update.message.reply_text(n)

async def macro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ctx = market_context()
    await update.message.reply_text(f"🌍 {ctx}")

# =========================
# SCAN AUTO
# =========================
async def scan(context: ContextTypes.DEFAULT_TYPE):
    btc = get_btc()
    nasdaq = get_price("^IXIC")
    gold = get_price("GC=F")
    brent = get_price("BZ=F")

    data = {
        "BTC": btc,
        "NASDAQ": nasdaq,
        "GOLD": gold,
        "BRENT": brent
    }

    for k, v in data.items():
        if v:
            history[k].append(v)
            if len(history[k]) > 50:
                history[k].pop(0)

    for asset in history:
        if len(history[asset]) < 10:
            continue

        s = score(history[asset])
        sig = signal(s)

        if sig != "⚪ WAIT":
            await context.bot.send_message(
                chat_id=context.job.chat_id,
                text=f"🚨 {asset}\n{sig}\nScore: {s}"
            )

# =========================
# WEB SERVER (Render)
# =========================
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot actif")

def run_web():
    HTTPServer(("0.0.0.0", 8000), Handler).serve_forever()

# =========================
# MAIN
# =========================
def main():
    clear_webhook()
    time.sleep(2)

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("btc", btc))
    app.add_handler(CommandHandler("news", news))
    app.add_handler(CommandHandler("macro", macro))

    threading.Thread(target=run_web, daemon=True).start()

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
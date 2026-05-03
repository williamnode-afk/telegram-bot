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
# TELEGRAM FIX
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

last_signal = {}
cooldown = {}

# =========================
# FETCH DATA
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
        (gains if diff > 0 else losses).append(abs(diff))
    avg_gain = sum(gains)/len(gains) if gains else 0.01
    avg_loss = sum(losses)/len(losses) if losses else 0.01
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def spike(prices):
    if len(prices) < 5:
        return False
    return abs((prices[-1]-prices[-2])/prices[-2]*100) > 0.8

def volatility(prices):
    if len(prices) < 10:
        return 0
    returns = [(prices[i]-prices[i-1]) for i in range(1, len(prices))]
    avg = sum(returns)/len(returns)
    var = sum((r-avg)**2 for r in returns)/len(returns)
    return var**0.5

# =========================
# STRATEGIES
# =========================
def strat_trend(p):
    return 1 if p[-1] > p[0] else -1

def strat_breakout(p):
    return 1 if p[-1] >= max(p[-10:]) else (-1 if p[-1] <= min(p[-10:]) else 0)

def strat_mean(p):
    r = rsi(p)
    if not r: return 0
    if r < 30: return 1
    if r > 70: return -1
    return 0

# =========================
# SCORE
# =========================
def adaptive_score(p):
    score = 50
    score += strat_trend(p)*15
    score += strat_breakout(p)*15
    score += strat_mean(p)*10
    if spike(p): score += 5
    if volatility(p) > 5: score += 5
    return max(0, min(100, score))

def final_signal(score):
    if score >= 80: return "🟢 STRONG BUY"
    if score >= 65: return "🟢 BUY"
    if score <= 20: return "🔴 STRONG SELL"
    if score <= 35: return "🔴 SELL"
    return "⚪ WAIT"

# =========================
# MARKET CONTEXT
# =========================
def market_context():
    if len(history["BTC"]) < 10:
        return "UNKNOWN"
    btc = history["BTC"][-1] - history["BTC"][0]
    nasdaq = history["NASDAQ"][-1] - history["NASDAQ"][0]
    gold = history["GOLD"][-1] - history["GOLD"][0]
    if btc > 0 and nasdaq > 0: return "🟢 RISK-ON"
    if btc < 0 and nasdaq < 0 and gold > 0: return "🔴 RISK-OFF"
    return "⚪ MIXED"

# =========================
# TIMING
# =========================
def precise_timing(p):
    if len(p) < 10: return "WAIT"
    high = max(p[-6:-1])
    if p[-1] > high: return "🎯 ENTRY"
    return "WAIT"

# =========================
# MANIPULATION
# =========================
def manipulation(p):
    if len(p) < 5: return None
    if abs((p[-1]-p[-2])/p[-2]*100) > 1.2:
        return "🐋 Possible manipulation"
    return None

# =========================
# NEWS
# =========================
def get_news():
    try:
        url = f"https://cryptopanic.com/api/v1/posts/?auth_token={CRYPTO_API}&public=true"
        data = requests.get(url).json()
        return "\n".join([n["title"] for n in data["results"][:3]])
    except:
        return "No news"

# =========================
# SCAN
# =========================
async def scan(context: ContextTypes.DEFAULT_TYPE):
    btc = get_btc()
    nasdaq = get_price("^IXIC")
    gold = get_price("GC=F")
    brent = get_price("BZ=F")

    data = {"BTC": btc, "NASDAQ": nasdaq, "GOLD": gold, "BRENT": brent}

    for k, v in data.items():
        if v:
            history[k].append(v)
            if len(history[k]) > 50:
                history[k].pop(0)

    for asset in history:
        if len(history[asset]) < 10:
            continue

        score = adaptive_score(history[asset])
        signal = final_signal(score)

        if signal != "⚪ WAIT":
            await context.bot.send_message(
                chat_id=context.job.chat_id,
                text=f"🚨 {asset}\n{signal}\nScore: {score}"
            )

# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 BOT NEWS PRO ACTIF")

    chat_id = update.effective_chat.id
    context.job_queue.run_repeating(scan, interval=60, first=5, chat_id=chat_id)

# =========================
# WEB DASHBOARD
# =========================
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write("Bot actif".encode())

def start_web():
    HTTPServer(("0.0.0.0", 8000), Handler).serve_forever()

# =========================
# MAIN
# =========================
def main():
    clear_webhook()
    time.sleep(2)

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    threading.Thread(target=start_web, daemon=True).start()

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
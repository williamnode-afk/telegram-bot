import os
import time
import requests
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("TOKEN")
NEWS_API = os.getenv("NEWSAPI_KEY")

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

last_news = []

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

# =========================
# SCORE
# =========================
def score(prices):
    s = 50
    if prices[-1] > prices[0]: s += 15
    if prices[-1] >= max(prices[-10:]): s += 15
    if prices[-1] <= min(prices[-10:]): s -= 15

    r = rsi(prices)
    if r:
        if r < 30: s += 10
        elif r > 70: s -= 10

    return max(0, min(100, s))

def signal(s):
    if s >= 70: return "🟢 BUY"
    elif s <= 30: return "🔴 SELL"
    return "⚪ WAIT"

# =========================
# TIMING
# =========================
def precise_entry(p):
    if len(p) < 12:
        return "WAIT"

    high = max(p[-6:-1])
    low = min(p[-6:-1])

    p0, p1, p2 = p[-1], p[-2], p[-3]

    if p1 <= high and p0 > high:
        return "BREAKOUT"
    if p0 < high and p1 > high:
        return "PULLBACK"
    if p1 < high and p0 > p1 and p0 > p2:
        return "🎯 ENTRY"
    if p1 >= low and p0 < low:
        return "BREAKDOWN"

    return "WAIT"

# =========================
# MANIPULATION
# =========================
def detect_manipulation(p):
    if len(p) < 5:
        return None

    move = (p[-1] - p[-2]) / p[-2] * 100
    prev = (p[-2] - p[-3]) / p[-3] * 100

    if abs(prev) > 1.2 and abs(move) < 0.2:
        return "⚠️ Rejet rapide (piège)"
    if abs(move) > 1.5:
        return "🐋 Spike suspect"

    return None

# =========================
# NEWS ANALYSIS
# =========================
def analyze_news(text):
    text = text.lower()

    bullish = ["growth", "surge", "strong", "positive", "beat"]
    bearish = ["inflation", "war", "crash", "recession", "rate hike"]

    score = 0
    for w in bullish:
        if w in text:
            score += 1
    for w in bearish:
        if w in text:
            score -= 1

    confidence = min(abs(score) * 50, 100)

    if score > 0:
        return "🟢 BULLISH", "BUY 📈", confidence
    elif score < 0:
        return "🔴 BEARISH", "SELL 📉", confidence
    return "⚪ NEUTRE", "WAIT", confidence

# =========================
# GET NEWS
# =========================
def get_news():
    url = f"https://newsapi.org/v2/top-headlines?category=business&language=en&apiKey={NEWS_API}"
    r = requests.get(url)
    data = r.json()
    articles = data.get("articles", [])

    results = []

    for a in articles[:5]:
        title = a.get("title", "")

        if title in last_news:
            continue

        impact, sig, conf = analyze_news(title)

        if conf >= 50:
            results.append((title, impact, sig, conf))
            last_news.append(title)

    return results

# =========================
# COMMANDS
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 BOT TRADING NEWS ACTIF")

    chat_id = update.effective_chat.id
    context.job_queue.run_repeating(scan, interval=60, first=5, chat_id=chat_id)
    context.job_queue.run_repeating(alerts, interval=900, first=10)

async def btc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"₿ BTC: {get_btc()}$")

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    news = get_news()
    if not news:
        await update.message.reply_text("Aucune news importante")
        return

    text = "🚨 NEWS IMPACT\n\n"
    for t, imp, sig, conf in news:
        text += f"{t}\n{imp} | {sig} | {conf}%\n\n"

    await update.message.reply_text(text)

# =========================
# ALERTS AUTO
# =========================
async def alerts(context):
    news = get_news()
    if not news:
        return

    text = "🚨 ALERT NEWS 🔥\n\n"
    for t, imp, sig, conf in news:
        text += f"{t}\n{imp} | {sig} | {conf}%\n\n"

    await context.bot.send_message(chat_id=os.getenv("CHAT_ID"), text=text)

# =========================
# SCAN
# =========================
async def scan(context):
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

    if len(history["BTC"]) > 10:
        s = score(history["BTC"])
        sig = signal(s)
        timing = precise_entry(history["BTC"])
        manip = detect_manipulation(history["BTC"])

        if manip:
            await context.bot.send_message(chat_id=context.job.chat_id, text=manip)

        if sig != "⚪ WAIT" and timing == "🎯 ENTRY" and not manip:
            await context.bot.send_message(
                chat_id=context.job.chat_id,
                text=f"🔥 ENTRY BTC\n{sig}\nScore: {s}\nTiming: {timing}"
            )

# =========================
# WEB SERVER
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

    threading.Thread(target=run_web, daemon=True).start()

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
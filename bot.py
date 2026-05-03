import os
import requests
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("TOKEN")

# =========================
# DATA STORAGE
# =========================
history = {
    "BTC": [],
    "NASDAQ": [],
    "GOLD": [],
    "BRENT": []
}

params = {
    "rsi_buy": 30,
    "rsi_sell": 70
}

active_trade = None

# =========================
# DATA FETCH
# =========================
def get_price(symbol):
    url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}"
    data = requests.get(url).json()
    return data["quoteResponse"]["result"][0]["regularMarketPrice"]

def get_btc():
    return requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd").json()["bitcoin"]["usd"]

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

def spike(prices):
    if len(prices) < 5:
        return False
    change = abs((prices[-1] - prices[-2]) / prices[-2]) * 100
    return change > 0.8

def market_mode(prices):
    if len(prices) < 10:
        return "UNKNOWN"
    return "TREND" if (max(prices) - min(prices)) > prices[-1] * 0.02 else "RANGE"

# =========================
# STRATEGIES
# =========================
def strat_trend(prices):
    if len(prices) < 10:
        return 0
    change = (prices[-1] - prices[0]) / prices[0] * 100
    return 1 if change > 1 else (-1 if change < -1 else 0)

def strat_mean(prices):
    r = rsi(prices)
    if not r:
        return 0
    if r < params["rsi_buy"]:
        return 1
    elif r > params["rsi_sell"]:
        return -1
    return 0

def strat_breakout(prices):
    if len(prices) < 10:
        return 0
    if prices[-1] >= max(prices[-10:]):
        return 1
    elif prices[-1] <= min(prices[-10:]):
        return -1
    return 0

# =========================
# SCORE
# =========================
def adaptive_score(prices):
    score = 50
    score += strat_trend(prices) * 15
    score += strat_mean(prices) * 10
    score += strat_breakout(prices) * 15
    if spike(prices):
        score += 5
    return max(0, min(100, score))

def final_signal(score):
    if score >= 70:
        return "🟢 BUY"
    elif score <= 30:
        return "🔴 SELL"
    return "⚪ WAIT"

# =========================
# ORDER FLOW
# =========================
def order_flow():
    try:
        url = "https://api.binance.com/api/v3/depth?symbol=BTCUSDT&limit=50"
        data = requests.get(url).json()
        bids = sum(float(b[1]) for b in data["bids"])
        asks = sum(float(a[1]) for a in data["asks"])
        if bids > asks:
            return "🟢 Buyers"
        else:
            return "🔴 Sellers"
    except:
        return "N/A"

# =========================
# DASHBOARD
# =========================
def dashboard():
    scores = {k: adaptive_score(v) for k, v in history.items() if len(v) > 10}

    msg = "📊 DASHBOARD\n\n"
    for k, v in scores.items():
        msg += f"{k}: {v}/100 → {final_signal(v)}\n"

    msg += f"\nOrderFlow: {order_flow()}"
    return msg

# =========================
# TRADE LOG
# =========================
def log_trade(trade):
    try:
        with open("trades.json", "r") as f:
            data = json.load(f)
    except:
        data = []

    data.append(trade)

    with open("trades.json", "w") as f:
        json.dump(data, f)

# =========================
# ANALYSIS
# =========================
def analyze_trades():
    try:
        with open("trades.json", "r") as f:
            trades = json.load(f)
    except:
        return "Aucune donnée"

    wins = [t for t in trades if t.get("result") == "win"]
    losses = [t for t in trades if t.get("result") == "loss"]

    total = len(trades)
    winrate = (len(wins) / total * 100) if total else 0

    return f"Trades: {total}\nWinrate: {winrate:.2f}%"

# =========================
# SCAN LOOP
# =========================
async def scan(context: ContextTypes.DEFAULT_TYPE):
    try:
        btc = get_btc()
        nasdaq = get_price("^IXIC")
        gold = get_price("GC=F")
        brent = get_price("BZ=F")

        data = {"BTC": btc, "NASDAQ": nasdaq, "GOLD": gold, "BRENT": brent}

        for k, v in data.items():
            history[k].append(v)
            if len(history[k]) > 50:
                history[k].pop(0)

        if len(history["BTC"]) > 10:
            score = adaptive_score(history["BTC"])
            signal = final_signal(score)

            if signal != "⚪ WAIT":
                await context.bot.send_message(
                    chat_id=context.job.chat_id,
                    text=f"{signal} BTC\nScore: {score}"
                )

        # dashboard
        await context.bot.send_message(
            chat_id=context.job.chat_id,
            text=dashboard()
        )

    except Exception as e:
        print("Erreur scan:", e)

# =========================
# COMMANDS
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 BOT TRADING ULTRA PRO ACTIF")

    chat_id = update.effective_chat.id
    context.job_queue.run_repeating(scan, interval=60, first=5, chat_id=chat_id)

async def stats_cmd(update, context):
    await update.message.reply_text(analyze_trades())

# =========================
# WEB DASHBOARD
# =========================
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(f"<h1>{dashboard()}</h1>".encode())

def start_web():
    server = HTTPServer(("0.0.0.0", 8000), Handler)
    server.serve_forever()

# =========================
# MAIN
# =========================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats_cmd))

    threading.Thread(target=start_web, daemon=True).start()

    print("BOT ULTRA PRO LANCÉ")
    app.run_polling()

if __name__ == "__main__":
    main()
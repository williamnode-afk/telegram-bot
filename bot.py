import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")  # optionnel

# =========================
# 📰 NEWS SOURCES
# =========================

def fetch_cryptopanic():
    try:
        url = "https://cryptopanic.com/api/v1/posts/?public=true"
        data = requests.get(url, timeout=5).json()["results"]
        return [{"title": n["title"], "url": n["url"]} for n in data]
    except:
        return []

def fetch_newsapi():
    if not NEWSAPI_KEY:
        return []

    try:
        url = f"https://newsapi.org/v2/everything?q=bitcoin OR crypto OR inflation OR fed&language=en&sortBy=publishedAt&apiKey={NEWSAPI_KEY}"
        data = requests.get(url, timeout=5).json()["articles"]
        return [{"title": n["title"], "url": n["url"]} for n in data]
    except:
        return []

# =========================
# 🧠 FILTRAGE
# =========================

KEYWORDS = [
    "bitcoin","btc","crypto","fed","inflation","interest",
    "etf","sec","regulation","market","rate","crash","bull"
]

def filter_news(news):
    unique = []
    seen = set()

    for n in news:
        title = n["title"].lower()

        if len(title) < 20:
            continue

        if not any(k in title for k in KEYWORDS):
            continue

        if title in seen:
            continue

        seen.add(title)
        unique.append(n)

    return unique[:10]

def get_news():
    news = fetch_cryptopanic() + fetch_newsapi()
    return filter_news(news)

# =========================
# 📈 SENTIMENT + IMPACT
# =========================

def analyze_sentiment(title):
    t = title.lower()

    bull = ["rise","surge","bull","growth","approval","adoption","pump"]
    bear = ["crash","drop","fall","ban","fear","lawsuit","dump"]

    score = sum(1 for w in bull if w in t) - sum(1 for w in bear if w in t)

    if score > 0:
        return "📈 Bullish", score
    elif score < 0:
        return "📉 Bearish", score
    return "⚖️ Neutral", 0

def impact_score(title):
    t = title.lower()
    important = ["fed","inflation","etf","sec","interest","bitcoin"]

    return sum(2 for w in important if w in t)

# =========================
# 📊 GLOBAL MARKET ANALYSIS
# =========================

def global_market_analysis(news):
    total = 0

    for n in news:
        _, s = analyze_sentiment(n["title"])
        impact = impact_score(n["title"])
        total += s * (impact + 1)

    if not news:
        return "NEUTRAL", 0

    avg = total / len(news)

    if avg > 1:
        return "📈 BULLISH", avg
    elif avg < -1:
        return "📉 BEARISH", avg
    return "⚖️ NEUTRAL", avg

def confidence(score):
    s = abs(score)

    if s > 3:
        return "🔥🔥🔥"
    elif s > 2:
        return "🔥🔥"
    elif s > 1:
        return "🔥"
    return "❄️"

# =========================
# 💰 BTC PRICE (corrélation simple)
# =========================

def btc_price():
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT").json()
        return float(r["price"])
    except:
        return 0

# =========================
# 🤖 COMMANDES
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 Bot News Elite actif")

async def news_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    news = get_news()

    msg = "📰 NEWS ANALYSÉES\n\n"

    for n in news[:5]:
        sentiment, score = analyze_sentiment(n["title"])
        impact = impact_score(n["title"])

        msg += (
            f"{n['title']}\n"
            f"{sentiment} | Impact: {impact}\n"
            f"{n['url']}\n\n"
        )

    await update.message.reply_text(msg)

async def market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    news = get_news()
    bias, score = global_market_analysis(news)
    conf = confidence(score)
    price = btc_price()

    msg = (
        "🧠 MARCHÉ GLOBAL\n\n"
        f"📊 Bias: {bias}\n"
        f"📈 Score: {round(score,2)}\n"
        f"🔥 Confiance: {conf}\n\n"
        f"💰 BTC: {price:.2f}$"
    )

    await update.message.reply_text(msg)

# =========================
# 🚨 ALERTES
# =========================

last_bias = None

async def smart_alerts(context: ContextTypes.DEFAULT_TYPE):
    global last_bias

    news = get_news()
    bias, score = global_market_analysis(news)

    if abs(score) > 2 and bias != last_bias:
        msg = (
            "🚨 ALERTE MARCHÉ 🚨\n\n"
            f"{bias}\n"
            f"Score: {round(score,2)}"
        )

        await context.bot.send_message(chat_id=CHAT_ID, text=msg)
        last_bias = bias

# =========================
# 🚀 MAIN
# =========================

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("news", news_cmd))
    app.add_handler(CommandHandler("market", market))

    app.job_queue.run_repeating(smart_alerts, interval=300, first=10)

    print("BOT NEWS ELITE 🚀")

    app.run_polling()

if __name__ == "__main__":
    main()
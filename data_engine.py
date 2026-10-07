import requests
import os
from datetime import datetime

TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

PAIRS = {
    "GOLD": {"symbol": "GC=F", "emoji": "🥇", "nama": "Gold (XAUUSD)"},
    "EURUSD": {"symbol": "EURUSD=X", "emoji": "💶", "nama": "EURUSD"},
    "BTC": {"symbol": "BTC-USD", "emoji": "₿", "nama": "Bitcoin"},
    "OIL": {"symbol": "CL=F", "emoji": "🛢️", "nama": "Crude Oil"},
    "SILVER": {"symbol": "SI=F", "emoji": "🥈", "nama": "Silver"},
    "SP500": {"symbol": "^GSPC", "emoji": "📈", "nama": "S&P 500"},
    "USDJPY": {"symbol": "JPY=X", "emoji": "💴", "nama": "USDJPY"},
    "GBPUSD": {"symbol": "GBPUSD=X", "emoji": "💷", "nama": "GBPUSD"}
}

def ambil_harga(symbol):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=5d"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        data = r.json()
        result = data["chart"]["result"][0]
        closes = result["indicators"]["quote"][0]["close"]
        closes = [c for c in closes if c is not None]
        if len(closes) >= 2:
            return {
                "harga": closes[-1],
                "sebelum": closes[-2],
                "chg": ((closes[-1] - closes[-2]) / closes[-2]) * 100
            }
    except Exception as e:
        print(f"Error {symbol}: {e}")
    return None

def ambil_ohlc(symbol, interval="1h", range_="1mo"):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval={interval}&range={range_}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        data = r.json()
        result = data["chart"]["result"][0]
        q = result["indicators"]["quote"][0]
        out = []
        for i in range(len(q["high"])):
            if q["high"][i] and q["low"][i] and q["close"][i] and q["open"][i]:
                out.append({
                    "open": q["open"][i],
                    "high": q["high"][i],
                    "low": q["low"][i],
                    "close": q["close"][i],
                    "volume": q["volume"][i] if q["volume"][i] else 0
                })
        return out
    except:
        return []

def hitung_statistik(data):
    """Hitung statistik dasar dari data OHLC"""
    if not data or len(data) < 5:
        return None
    
    closes = [d["close"] for d in data]
    highs = [d["high"] for d in data]
    lows = [d["low"] for d in data]
    volumes = [d["volume"] for d in data if d["volume"] > 0]
    
    # Volatilitas (ATR-like)
    ranges = [highs[i] - lows[i] for i in range(len(highs))]
    avg_range = sum(ranges) / len(ranges) if ranges else 0
    
    # Average volume
    avg_volume = sum(volumes) / len(volumes) if volumes else 0
    
    # Return (perubahan)
    returns = [(closes[i] - closes[i-1]) / closes[i-1] * 100 for i in range(1, len(closes))]
    avg_return = sum(returns) / len(returns) if returns else 0
    volatility = (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5 if returns else 0
    
    return {
        "avg_range": round(avg_range, 4),
        "avg_volume": round(avg_volume, 2),
        "avg_return": round(avg_return, 4),
        "volatility": round(volatility, 4),
        "high_24h": round(max(highs[-24:]), 4) if len(highs) >= 24 else round(max(highs), 4),
        "low_24h": round(min(lows[-24:]), 4) if len(lows) >= 24 else round(min(lows), 4)
    }

# ============ MAIN ============
print("=== QUANT ANALIS — FOUNDATION ===")
print(f"Waktu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

hasil = {}

for kode, info in PAIRS.items():
    print(f"Ambil data {kode}...")
    harga = ambil_harga(info["symbol"])
    ohlc = ambil_ohlc(info["symbol"], interval="1h", range_="1mo")
    statistik = hitung_statistik(ohlc) if ohlc else None
    
    hasil[kode] = {
        "nama": info["nama"],
        "emoji": info["emoji"],
        "harga": harga,
        "statistik": statistik,
        "total_candle": len(ohlc)
    }

# ============ SUSUN PESAN ============
tanggal = datetime.now().strftime("%d %B %Y — %H:%M WIB")
pesan = "📊 *QUANT ANALIS — FOUNDATION*\n"
pesan += f"📅 {tanggal}\n\n"
pesan += "━━━━━━━━━━━━━━━━━━\n\n"

for kode, h in hasil.items():
    pesan += f"{h['emoji']} *{h['nama']}*\n"
    if h["harga"]:
        pesan += f"💰 ${round(h['harga']['harga'], 2)} ({round(h['harga']['chg'], 2)}%)\n"
    if h["statistik"]:
        s = h["statistik"]
        pesan += f"📊 Range avg: {s['avg_range']}\n"
        pesan += f"📈 Volatility: {s['volatility']}%\n"
        pesan += f"📉 High 24h: {s['high_24h']}\n"
        pesan += f"📈 Low 24h: {s['low_24h']}\n"
    pesan += f"🕯️ Candle: {h['total_candle']}\n\n"

pesan += "━━━━━━━━━━━━━━━━━━\n"
pesan += "✅ *FASE 1: FOUNDATION — SELESAI*\n"
pesan += "🚀 _Next: Layer 1 — Macro Engine_"

# ============ KIRIM TELEGRAM ============
if TOKEN and CHAT_ID:
    url_tg = "https://api.telegram.org/bot" + TOKEN + "/sendMessage"
    r = requests.post(url_tg, data={
        "chat_id": CHAT_ID,
        "text": pesan,
        "parse_mode": "Markdown"
    })
    print("Terkirim!" if r.status_code == 200 else f"Gagal: {r.json()}")
else:
    print("TOKEN atau CHAT_ID kosong — skip kirim")
    print(pesan)

print()
print("Selesai!")

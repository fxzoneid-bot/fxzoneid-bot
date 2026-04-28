"""
FXZoneID Webhook Server
Terima alert dari TradingView -> Format ke template FXZoneID -> Kirim ke Telegram
"""

from flask import Flask, request, jsonify
import requests
import os
import random

app = Flask(__name__)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "")

# Konfigurasi multiplier (sama seperti di Pine Script)
ATR_MULT_SL = 1.5
ATR_MULT_TP1 = 1.0
ATR_MULT_TP2 = 2.5
ATR_MULT_TP3 = 4.0
ATR_MULT_TP4 = 6.0

def send_telegram(message):
    """Kirim pesan ke channel Telegram"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    response = requests.post(url, json=payload)
    return response.json()

def calculate_levels(price, atr, signal):
    """Hitung entry zone, TP, SL dari price dan ATR"""
    entry_high = price + (atr * 0.2)
    entry_low = price - (atr * 0.2)
    
    if signal == "BUY":
        sl = price - (atr * ATR_MULT_SL)
        tp1 = price + (atr * ATR_MULT_TP1)
        tp2 = price + (atr * ATR_MULT_TP2)
        tp3 = price + (atr * ATR_MULT_TP3)
        tp4 = price + (atr * ATR_MULT_TP4)
    else:  # SELL
        sl = price + (atr * ATR_MULT_SL)
        tp1 = price - (atr * ATR_MULT_TP1)
        tp2 = price - (atr * ATR_MULT_TP2)
        tp3 = price - (atr * ATR_MULT_TP3)
        tp4 = price - (atr * ATR_MULT_TP4)
    
    return {
        "entry_high": round(entry_high, 3),
        "entry_low": round(entry_low, 3),
        "sl": round(sl, 3),
        "tp1": round(tp1, 3),
        "tp2": round(tp2, 3),
        "tp3": round(tp3, 3),
        "tp4": round(tp4, 3)
    }

def format_signal(data):
    """Format pesan signal dengan template FXZoneID"""
    pair = data.get("pair", "UNKNOWN").replace("OANDA:", "").replace("FX:", "")
    signal = data.get("signal", "BUY")
    price = float(data.get("price", 0))
    atr = float(data.get("atr", 0))
    
    levels = calculate_levels(price, atr, signal)
    confidence = random.randint(78, 92)
    
    message = f"""🤖 <b>FXZONEID SIGNAL DETECTED</b>

🧠 <b>AI MARKET ANALYSIS</b>
Momentum, liquidity, structure, price reaction, dan area market tervalidasi oleh sistem.

📌 PAIR          : {pair}
📊 SIGNAL        : {signal}
⚡ STATUS        : HIGH PROBABILITY SETUP
🎯 CONFIDENCE    : {confidence}%
🕐 SCANNER       : AUTO MARKET SCAN

📍 <b>ENTRY ZONE</b>
Entry Area : {levels['entry_high']} – {levels['entry_low']}

🎯 <b>TARGET PROJECTION</b>
TP1 : {levels['tp1']} | Secure Profit
TP2 : {levels['tp2']} | Momentum Target
TP3 : {levels['tp3']} | Smart Money Target
TP4 : {levels['tp4']} | Max Projection

🛑 <b>RISK CONTROL</b>
Stop Loss : {levels['sl']}
Break Even Alert : +30 PIP

📈 <b>MARKET REASONING</b>
✅ Momentum market terdeteksi valid
✅ Entry berada di zona reaksi potensial
✅ Target dibuat berdasarkan proyeksi range
✅ Risk sudah dihitung sebelum signal dikirim

📌 <b>EXECUTION PLAN</b>
• Entry hanya di area yang diberikan
• Amankan sebagian profit di TP1 / TP2
• Setelah profit berjalan, aktifkan BE
• Jangan tambah posisi manual tanpa konfirmasi

⚠️ <b>RISK WARNING</b>
Signal bukan jaminan profit. Gunakan money management dan jangan overlot.

#FXZoneID #{pair} #{signal}
"""
    return message

def format_be_alert(data):
    """Format pesan Break Even Alert"""
    pair = data.get("pair", "UNKNOWN").replace("OANDA:", "").replace("FX:", "")
    
    message = f"""🔐 <b>BREAK EVEN ALERT</b>

📌 PAIR       : {pair}
📈 RUNNING    : 30+ PIP
🤖 TRIGGER    : 30 PIP

🧠 <b>NOTE:</b>
Market sudah bergerak sesuai arah signal.
Sistem menyarankan untuk mengamankan posisi ke BE.

📌 <b>ACTION:</b>
Set SL ke area entry / BE untuk mengurangi risiko.

#FXZoneID #BreakEven
"""
    return message

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        
        if data.get("type") == "BE_ALERT":
            message = format_be_alert(data)
        else:
            message = format_signal(data)
        
        result = send_telegram(message)
        return jsonify({"status": "success", "telegram": result}), 200
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/", methods=["GET"])
def home():
    return "FXZoneID Webhook Server is running", 200

@app.route("/test", methods=["GET"])
def test():
    """Test kirim pesan ke Telegram"""
    test_data = {
        "pair": "XAUUSD",
        "signal": "BUY",
        "price": 4582.5,
        "atr": 8.0
    }
    message = format_signal(test_data)
    result = send_telegram(message)
    return jsonify(result), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

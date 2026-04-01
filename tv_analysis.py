import os
from dotenv import load_dotenv
from tvDatafeed import TvDatafeed, Interval
import pandas as pd
import numpy as np
import ssl
import certifi

# Fix SSL certificate issues for macOS
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

load_dotenv()

def calculate_rsi(df, period=14):
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 * rs + 1))

def calculate_macd(df):
    exp12 = df['close'].ewm(span=12, adjust=False).mean()
    exp26 = df['close'].ewm(span=26, adjust=False).mean()
    macd = exp12 - exp26
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal

def get_tv_analysis(symbol='GLD', exchange='AMEX', interval='1d'):
    username = os.getenv("TRADINGVIEW_USERNAME")
    password = os.getenv("TRADINGVIEW_PASSWORD")

    if not username or not password:
        return "TradingView credentials missing in .env."

    try:
        # Initialize TvDatafeed
        tv = TvDatafeed(username, password)
        # Fetch 100 candles to ensure enough data for indicators
        n_bars = 100
        
        # Mapping string intervals to TvDatafeed intervals
        tv_interval = Interval.in_daily
        if interval == '1h':
            tv_interval = Interval.in_1_hour
            
        df = tv.get_hist(symbol=symbol, exchange=exchange, interval=tv_interval, n_bars=n_bars)
        
        if df is None or df.empty:
            return f"Failed to fetch data for {symbol} from TradingView."

        # Calculate indicators
        df['rsi'] = calculate_rsi(df)
        df['macd'], df['macd_signal'] = calculate_macd(df)
        df['sma50'] = df['close'].rolling(window=50).mean()
        df['sma200'] = df['close'].rolling(window=200 if len(df) >= 200 else len(df)).mean()

        last = df.iloc[-1]
        prev = df.iloc[-2]

        rsi_val = last['rsi']
        macd_val = last['macd']
        macd_sig = last['macd_signal']
        price = last['close']
        sma50 = last['sma50']
        sma200 = last['sma200']

        # Determine bias
        tech_bias = "NEUTRAL"
        if rsi_val > 60 and macd_val > macd_sig:
            tech_bias = "BULLISH"
        elif rsi_val < 40 and macd_val < macd_sig:
            tech_bias = "BEARISH"

        trend = "UPTREND" if price > sma50 else "DOWNTREND"
        
        summary = f"""
GLD TECHNICAL ANALYSIS (TradingView):
- Price: ${price:.2f}
- RSI(14): {rsi_val:.1f} ({'Overbought' if rsi_val > 70 else 'Oversold' if rsi_val < 30 else 'Neutral'})
- MACD: {macd_val:.2f} | Signal: {macd_sig:.2f} ({'Bullish Cross' if macd_val > macd_sig else 'Bearish Cross'})
- 50 SMA: ${sma50:.2f} | 200 SMA: ${sma200:.2f}
- Trend: {trend}
- Technical Bias: {tech_bias}
"""
        return summary
    except Exception as e:
        return f"TradingView Analysis Error: {str(e)}"

if __name__ == "__main__":
    print(get_tv_analysis())

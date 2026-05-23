import datetime
import json
import numpy as np
import pandas as pd
import yfinance as yf

# ==============================================================================
# 1. 定義監控的台股 AI 概念股池 (包含散熱、光通訊、高速傳輸、PCB、伺服器大廠)
# ==============================================================================
AI_WATCHLIST = [
    "6526.TW",
    "4958.TW",
    "3363.TW",
    "3017.TW",
    "2382.TW",
    "2330.TW",
    "3163.TW",
    "8021.TW",
    "3167.TW",
    "2308.TW",
    "6669.TW",
    "2454.TW",
    "3231.TW",
    "2356.TW",
]

print("🚀 量化選股模型啟動：開始分析台股 AI 供應鏈數據...")


# ==============================================================================
# 2. 量化篩選演算法 (技術指標計算)
# ==============================================================================
def screen_breakout_stocks(ticker_list):
    selected_stocks = []

    for ticker in ticker_list:
        try:
            # 抓取最近 120 天的日 K 線數據
            stock = yf.Ticker(ticker)
            df = stock.history(period="120d")
            if len(df) < 60:
                continue

            # 計算均線 (5MA, 10MA, 20MA)
            df["5MA"] = df["Close"].rolling(window=5).mean()
            df["10MA"] = df["Close"].rolling(window=10).mean()
            df["20MA"] = df["Close"].rolling(window=20).mean()
            df["5日均量"] = df["Volume"].rolling(window=5).mean()

            # 取得最新一筆與前一筆數據
            today = df.iloc[-1]
            yesterday = df.iloc[-2]

            close_p = today["Close"]
            volume = today["Volume"]
            ma5, ma10, ma20 = today["5MA"], today["10MA"], today["20MA"]

            # ---- 量化條件 1: 均線糾結度 (5, 10, 20MA 彼此距離在 3% 以內) ----
            ma_list = [ma5, ma10, ma20]
            ma_dispersion = (max(ma_list) - min(ma_list)) / min(ma_list)
            is_tangent = ma_dispersion <= 0.035

            # ---- 量化條件 2: 剛要噴發 (今日收盤突破均線糾結，且創近10日新高) ----
            is_breakout = (close_p > max(ma_list)) and (
                close_p >= df["Close"].iloc[-10:].max()
            )

            # ---- 量化條件 3: 成交量爆發 (今日量大於5日均量的 1.5 倍) ----
            is_volume_up = volume > (df["5日均量"].iloc[-2] * 1.5)

            # 如果符合剛突破、量放大，或近期強勢多頭排列
            if (is_tangent and is_breakout) or (
                is_breakout and is_volume_up
            ):  # 剛突破或量滾量
                # 量化計算建議買進區間 (第一根突破棒的中軸至箱頂)
                buy_min = round(min(today["Open"], close_p) * 0.99, 1)
                buy_max = round(close_p * 1.005, 1)
                # 防守位設定為 20MA 或此棒最低價
                support_line = round(min(today["Low"], ma20), 1)

                # 格式化 Highcharts 所需的 K 線 JSON 數據格式 [[時間戳, O, H, L, C], ...]
                chart_data = []
                for index, row in df.tail(40).iterrows():
                    timestamp = int(index.timestamp() * 1000)
                    chart_data.append(
                        [
                            timestamp,
                            round(row["Open"], 2),
                            round(row["High"], 2),
                            round(row["Low"], 2),
                            round(row["Close"], 2),
                        ]
                    )

                # 抓取股票中文名稱（防錯處理）
                info = stock.info
                name = (
                    info.get("longName")
                    if info.get("longName")
                    else ticker.split(".")[0]
                )

                selected_stocks.append(
                    {
                        "ticker": ticker.split(".")[0],
                        "name": name,
                        "current_price": round(close_p, 1),
                        "buy_min": buy_min,
                        "buy_max": buy_max,
                        "support": support_line,
                        "data": chart_data,
                        "signal_idx": len(chart_data) - 1,
                    }
                )
        except Exception as e:
            print(f"⚠️ 處理 {ticker} 時發生錯誤: {e}")

    return selected_stocks


# 執行篩選
filtered_list = screen_breakout_stocks(AI_WATCHLIST)
print(f"✅ 篩選完成！共找到 {len(filtered_list)} 檔剛要噴發的 AI 潛力股。")

# ==============================================================================
# 3. 自動渲染生成前台網頁網頁 (HTML)
# ==============================================================================
html_template = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>AI 剛噴發飆股每日監控系統</title>
    <script src="https://highcharts.com"></script>
    <style>
        body { background-color: #0f172a; color: #f8fafc; font-family: sans-serif; padding: 20px; }
        .container { max-width: 1100px; margin: 0 auto; }
        header { text-align: center; margin-bottom: 30px; border-bottom: 2px solid #1e293b; padding-bottom: 15px; }
        .update-time { color: #10b981; font-weight: bold; }
        .card { background-color: #1e293b; border-radius: 12px; padding: 20px; margin-bottom: 25px; }
        .stock-header { display: flex; justify-content: space-between; font-size: 1.3rem; font-weight: bold; margin-bottom: 10px; border-bottom: 1px solid #334155; padding-bottom: 8px;}
        .strategy-box { background-color: #0f172a; border-left: 4px solid #f59e0b; padding: 12px; margin-bottom: 15px; font-size: 0.9rem; border-radius: 4px; }
        .chart-container { height: 400px; width: 100%; }
    </style>
</head>
<body>
<div class="container">
    <header>
        <h1>🚀 AI 基礎建設：剛起漲飆股自動監控網頁</h1>
        <p>系統更新時間：<span class="update-time">UPDATE_TIME_PLACEHOLDER</span></p>
    </header>
    
    <!-- STOCKS_HOLDER -->
</div>

<script>
    const stockData = STOCKS_DATA_PLACEHOLDER;

    window.onload = function() {
        stockData.forEach(stock => {
            Highcharts.stockChart('chart-' + stock.ticker, {
                rangeSelector: { enabled: false }, navigator: { enabled: false }, scrollbar: { enabled: false },
                chart: { backgroundColor: '#1e293b' },
                title: { text: null },
                xAxis: { gridLineWidth: 1, gridLineColor: '#334155', labels: { style: { color: '#94a3b8' } } },
                yAxis: {
                    gridLineColor: '#334155', labels: { style: { color: '#94a3b8' } },
                    plotBands: [{
                        from: stock.buy_min, to: stock.buy_max, color: 'rgba(234, 179, 8, 0.15)',
                        label: { text: '🎯 建議買進區間', style: { color: '#f59e0b', fontWeight: 'bold' } }
                    }],
                    plotLines: [{
                        value: stock.support, color: '#38bdf8', width: 2, dashStyle: 'dash',
                        label: { text: '🛡️ 防守止損線: ' + stock.support, style: { color: '#38bdf8' }, align: 'right' }
                    }]
                },
                plotOptions: { candlestick: { color: '#ef4444', upColor: '#22c55e', lineColor: '#ef4444', upLineColor: '#22c55e' } },
                series: [{ type: 'candlestick', name: stock.name, data: stock.data, id: 'main' },
                {
                    type: 'flags', data: [{ x: stock.data[stock.signal_idx][0], title: '🚀噴發', text: '量化模型首日起漲點' }],
                    onSeries: 'main', shape: 'squarepin', width: 45, style: { color: '#fff', backgroundColor: '#e11d48' }
                }]
            });
        });
    };
</script>
</body>
</html>
"""

# 生成每檔股票的 HTML 結構
cards_html = ""
for s in filtered_list:
    cards_html += f"""
    <div class="card">
        <div class="stock-header">
            <div>{s['name']} ({s['ticker']}) <span style="font-size:1rem; color:#94a3b8;">當日收盤：{s['current_price']} 元</span></div>
            <div style="color: #f59e0b; font-size:1rem;">⚠️ 技術面：均線初次放量突圍</div>
        </div>
        <div class="strategy-box">
            🎯 <b>建議買進區間：</b> <span style="color:#fbbf24; font-weight:bold;">{s['buy_min']} - {s['buy_max']} 元</span> (突破上沿或拉回建立核心倉)<br>
            🛡️ <b>移動防守價位：</b> <span style="color:#38bdf8; font-weight:bold;">{s['support']} 元</span> (實體 K 棒跌破此防線則假突破停損)
        </div>
        <div id="chart-{s['ticker']}" class="chart-container"></div>
    </div>
    """

# 替換範本標籤
now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
html_output = html_template.replace("UPDATE_TIME_PLACEHOLDER", now_str)
html_output = html_output.replace("<!-- STOCKS_HOLDER -->", cards_html)
html_output = html_output.replace(
    "STOCKS_DATA_PLACEHOLDER", json.dumps(filtered_list)
)

# 寫出網頁檔案
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_output)

print("🎉 網頁更新完畢！請打開當前資料夾下的 index.html 查看最新日線圖與點位。")

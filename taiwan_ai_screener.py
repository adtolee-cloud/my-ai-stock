import datetime
import json
import numpy as np
import pandas as pd
import yfinance as yf

# ==============================================================================
# 1. 填寫您的 GitHub 帳號資訊 (用來建立網頁上的手動更新按鈕連結)
# ==============================================================================
# ⚠️ 請把引號內的文字改成您在 GitHub 註冊的真實帳號名稱（使用者名稱）
GITHUB_USERNAME = "adtolee-cloud"
REPO_NAME = "my-ai-stock"

# ==============================================================================
# 2. 定義監控的台股 AI 概念股池 (包含散熱、光通訊、高速傳輸、PCB、伺服器大廠)
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
# 3. 量化篩選演算法 (技術指標計算)
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

            # 取得最新一筆數據
            today = df.iloc[-1]
            close_p = today["Close"]
            volume = today["Volume"]
            ma5, ma10, ma20 = today["5MA"], today["10MA"], today["20MA"]

            # ---- 量化條件 1: 均線糾結度 (5, 10, 20MA 彼此距離在 3.5% 以內) ----
            ma_list = [ma5, ma10, ma20]
            ma_dispersion = (max(ma_list) - min(ma_list)) / min(ma_list)
            is_tangent = ma_dispersion <= 0.035

            # ---- 量化條件 2: 剛要噴發 (今日收盤突破均線糾結，且創近10日新高) ----
            is_breakout = (close_p > max(ma_list)) and (
                close_p >= df["Close"].iloc[-10:].max()
            )

            # ---- 量化條件 3: 成交量爆發 (今日量大於5日均量的 1.5 倍) ----
            is_volume_up = volume > (df["5日均量"].iloc[-2] * 1.5)

            # 篩選核心邏輯：剛突破均線糾結，或者帶量突破創高
            if (is_tangent and is_breakout) or (is_breakout and is_volume_up):
                # 量化計算建議買進區間 (第一根突破棒的中軸至收盤價)
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

                # 抓取股票代號 (去除.TW)
                clean_ticker = ticker.split(".")[0]

                selected_stocks.append(
                    {
                        "ticker": clean_ticker,
                        "name": f"台股 {clean_ticker}",
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
# 4. 自動網頁範本 (HTML) 內嵌互動 K 線與自動更新按鈕
# ==============================================================================
html_template = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI 剛噴發飆股每日監控系統</title>
    <!-- 引入高階圖表庫 -->
    <script src="https://highcharts.com"></script>
    <style>
        body { background-color: #0f172a; color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, sans-serif; padding: 20px; margin: 0; }
        .container { max-width: 1100px; margin: 0 auto; }
        header { text-align: center; margin-bottom: 30px; border-bottom: 2px solid #1e293b; padding-bottom: 20px; }
        h1 { color: #38bdf8; margin-bottom: 5px; }
        .update-time { color: #10b981; font-weight: bold; }
        .card { background-color: #1e293b; border-radius: 12px; padding: 20px; margin-bottom: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .stock-header { display: flex; justify-content: space-between; align-items: center; font-size: 1.3rem; font-weight: bold; margin-bottom: 10px; border-bottom: 1px solid #334155; padding-bottom: 8px;}
        .strategy-box { background-color: #0f172a; border-left: 4px solid #f59e0b; padding: 12px; margin-bottom: 15px; font-size: 0.9rem; border-radius: 0 4px 4px 0; line-height: 1.5; }
        .chart-container { height: 400px; width: 100%; }
        .update-btn { background-color: #10b981; color: white; border: none; padding: 12px 24px; font-size: 1rem; border-radius: 6px; cursor: pointer; font-weight: bold; box-shadow: 0 4px 6px rgba(0,0,0,0.1); transition: background 0.2s; }
        .update-btn:hover { background-color: #059669; }
    </style>
</head>
<body>
<div class="container">
    <header>
        <h1>🚀 AI 基礎建設：剛起漲飆股自動監控網頁</h1>
        <p style="color:#94a3b8;">策略：均線極度糾結後首日帶量突破 ｜ 移動停損防守</p>
        <p>系統最後更新時間：<span class="update-time">UPDATE_TIME_PLACEHOLDER</span></p>
        
        <!-- 手動更新按鈕區區塊 -->
        <div style="margin: 20px 0;">
            <button id="update-btn" class="update-btn" onclick="triggerManualUpdate()">
                🔄 點我立刻手動更新數據
            </button>
            <p id="status-msg" style="color: #fbbf24; font-size: 0.9rem; margin-top: 10px; display: none;"></p>
        </div>
    </header>
    
    <!-- STOCKS_HOLDER -->
</div>

<script>
    function triggerManualUpdate() {
        const btn = document.getElementById('update-btn');
        const msg = document.getElementById('status-msg');
        
        btn.disabled = true;
        btn.style.backgroundColor = '#64748b';
        btn.innerText = '⏳ 正在跳轉至雲端控制室...';
        msg.style.display = 'block';
        msg.innerText = '正在為您開啟 GitHub 後台控制室。請在彈出的視窗中，點擊右側的 "Run workflow" 綠色按鈕，雲端機器人就會立刻開始更新！';

        // 讀取 Python 自動填入的帳號變數
        const username = "GITHUB_USERNAME_PLACEHOLDER";
        const repo = "REPO_NAME_PLACEHOLDER";
        
        // 延遲開啟後台網頁
        setTimeout(() => {
            window.open(`https://github.com{username}/${repo}/actions/workflows/auto_run.yml`, '_blank');
            btn.disabled = false;
            btn.style.backgroundColor = '#10b981';
            btn.innerText = '🔄 點我立刻手動更新數據';
        }, 1500);
    }

    // 接收來自 Python 篩選完的最新股票清單 JSON
    const stockData = STOCKS_DATA_PLACEHOLDER;

    window.onload = function() {
        if(stockData.length === 0) {
            document.querySelector('.container').innerHTML += '<p style="text-align:center; color:#94a3b8; font-size:1.2rem; margin-top:50px;">今日暫無完全符合「剛要噴發」條件的個股，請隨時點選上方按鈕手動更新檢測。</p>';
            return;
        }

        stockData.forEach(stock => {
            Highcharts.stockChart('chart-' + stock.ticker, {
                rangeSelector: { enabled: false }, navigator: { enabled: false }, scrollbar: { enabled: false },
                chart: { backgroundColor: '#1e293b', plotBorderWidth: 0 },
                title: { text: null },
                xAxis: { gridLineWidth: 1, gridLineColor: '#334155', labels: { style: { color: '#94a3b8' } } },
                yAxis: {
                    gridLineColor: '#334155', labels: { style: { color: '#94a3b8' } },
                    plotBands: [{
                        from: stock.buy_min, to: stock.buy_max, color: 'rgba(234, 179, 8, 0.15)',
                        label: { text: '🎯 建議買進區間 ('+stock.buy_min+'-'+stock.buy_max+')', style: { color: '#f59e0b', fontWeight: 'bold' }, align: 'left', x: 10 }
                    }],
                    plotLines: [{
                        value: stock.support, color: '#38bdf8', width: 2, dashStyle: 'dash',
                        label: { text: '🛡️ 防守止損線: ' + stock.support, style: { color: '#38bdf8' }, align: 'right', y: -5 }
                    }]
                },
                plotOptions: { candlestick: { color: '#ef4444', upColor: '#22c55e', lineColor: '#ef4444', upLineColor: '#22c55e' } },
                series: [{ type: 'candlestick', name: stock.name, data: stock.data, id: 'main' },
                {
                    type: 'flags', data: [{ x: stock.data[stock.signal_idx][0], title: '🚀起漲', text: '量化模型首日放量突破點' }],
                    onSeries: 'main', shape: 'squarepin', width: 45, style: { color: '#fff', backgroundColor: '#e11d48', borderColor: '#e11d48' }
                }],
                credits: { enabled: false }
            });
        });
    };
</script>
</body>
</html>
"""

# 4. 生成每檔符合條件個股的 HTML 卡片元件
cards_html = ""
for s in filtered_list:
    cards_html += f"""
    <div class="card">
        <div class="stock-header">

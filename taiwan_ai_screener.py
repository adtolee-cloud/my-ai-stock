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

        const username = "GITHUB_USERNAME_PLACEHOLDER";
        const repo = "REPO_NAME_PLACEHOLDER";
        
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
        // 【修正防錯】如果沒有股票符合條件，安全顯示提示字眼
        if(!stockData || stockData.length === 0) {
            document.querySelector('.container').innerHTML += '<div style="text-align:center; color:#94a3b8; font-size:1.2rem; margin-top:50px; padding:30px; background:#1e293b; border-radius:12px;">📊 今日暫無完全符合「均線糾結後剛放量噴發」條件的個股。<br><span style="font-size:0.9rem; color:#64748b;">原因：可能正逢大盤震盪盤整，或主力資金正在洗盤。請於下一個交易日盤後再次點選上方按鈕手動更新。</span></div>';
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
                    type: 'flags', data: [{ x: stock.data[stock.signal_idx], title: '🚀起漲', text: '量化模型首日放量突破點' }],
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
            <div>{s['name']} ({s['ticker']}) <span style="font-size:1rem; color:#94a3b8; font-weight:normal;">最新收盤：{s['current_price']} 元</span></div>
            <div style="color: #22c55e; font-size:0.9rem; background:rgba(34,197,94,0.1); padding:4px 12px; border-radius:20px;">✓ 均線初次放量突圍</div>
        </div>
        <div class="strategy-box">
            🎯 <b>建議買進區間：</b> <span style="color:#fbbf24; font-weight:bold;">{s['buy_min']} - {s['buy_max']} 元</span> (突破棒合理震盪區，拉回分批布局)<br>
            🛡️ <b>移動防守價位：</b> <span style="color:#38bdf8; font-weight:bold;">{s['support']} 元</span> (實體日K線收盤跌破此防線則假突破停損)
        </div>
        <div id="chart-{s['ticker']}" class="chart-container"></div>
    </div>
    """

# 5. 替換網頁範本中的變數標籤
now_str = (datetime.datetime.utcnow() + datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
html_output = html_template.replace("UPDATE_TIME_PLACEHOLDER", now_str)
html_output = html_output.replace("GITHUB_USERNAME_PLACEHOLDER", GITHUB_USERNAME)
html_output = html_output.replace("REPO_NAME_PLACEHOLDER", REPO_NAME)
html_output = html_output.replace("<!-- STOCKS_HOLDER -->", cards_html)
html_output = html_output.replace("STOCKS_DATA_PLACEHOLDER", json.dumps(filtered_list))

# 6. 寫出網頁檔案
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_output)

print(f"🎉 網頁更新完畢！")

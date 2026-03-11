/**
 * Stock Trading Signals - Frontend App
 * TradingView Lightweight Charts + Real-time WebSocket updates
 */

const API_BASE = window.location.origin;
const WS_BASE = `ws://${window.location.host}`;

// State
const state = {
    symbol: null,
    interval: "1m",
    period: "1d",
    ws: null,
    candleSeries: null,
    sma20Series: null,
    sma50Series: null,
    ema9Series: null,
    bbUpperSeries: null,
    bbMidSeries: null,
    bbLowerSeries: null,
    rsiSeries: null,
    macdSeries: null,
    macdSignalSeries: null,
    macdHistSeries: null,
    mainChart: null,
    rsiChart: null,
    macdChart: null,
};

// ---- Chart Setup ----
function createMainChart() {
    const container = document.getElementById("candlestickChart");
    const height = container.parentElement.clientHeight - 28;
    const chart = LightweightCharts.createChart(container, {
        width: container.clientWidth,
        height: Math.max(height, 200),
        layout: {
            background: { color: "#0d1117" },
            textColor: "#8b949e",
        },
        grid: {
            vertLines: { color: "#21262d" },
            horzLines: { color: "#21262d" },
        },
        crosshair: {
            mode: LightweightCharts.CrosshairMode.Normal,
        },
        rightPriceScale: {
            borderColor: "#30363d",
        },
        timeScale: {
            borderColor: "#30363d",
            timeVisible: true,
            secondsVisible: false,
        },
    });

    const candleSeries = chart.addCandlestickSeries({
        upColor: "#00e676",
        downColor: "#ff1744",
        borderDownColor: "#ff1744",
        borderUpColor: "#00e676",
        wickDownColor: "#ff1744",
        wickUpColor: "#00e676",
    });

    const sma20 = chart.addLineSeries({
        color: "#1f6feb",
        lineWidth: 1.5,
        priceLineVisible: false,
        lastValueVisible: false,
        title: "SMA20",
    });

    const sma50 = chart.addLineSeries({
        color: "#ff9100",
        lineWidth: 1.5,
        priceLineVisible: false,
        lastValueVisible: false,
        title: "SMA50",
    });

    const ema9 = chart.addLineSeries({
        color: "#ce93d8",
        lineWidth: 1,
        lineStyle: LightweightCharts.LineStyle.Dashed,
        priceLineVisible: false,
        lastValueVisible: false,
        title: "EMA9",
    });

    const bbUpper = chart.addLineSeries({
        color: "rgba(255,215,64,0.5)",
        lineWidth: 1,
        priceLineVisible: false,
        lastValueVisible: false,
        title: "BB+",
    });

    const bbMid = chart.addLineSeries({
        color: "rgba(255,215,64,0.3)",
        lineWidth: 1,
        lineStyle: LightweightCharts.LineStyle.Dotted,
        priceLineVisible: false,
        lastValueVisible: false,
        title: "BB Mid",
    });

    const bbLower = chart.addLineSeries({
        color: "rgba(255,215,64,0.5)",
        lineWidth: 1,
        priceLineVisible: false,
        lastValueVisible: false,
        title: "BB-",
    });

    state.mainChart = chart;
    state.candleSeries = candleSeries;
    state.sma20Series = sma20;
    state.sma50Series = sma50;
    state.ema9Series = ema9;
    state.bbUpperSeries = bbUpper;
    state.bbMidSeries = bbMid;
    state.bbLowerSeries = bbLower;

    // OHLC display on crosshair
    chart.subscribeCrosshairMove((param) => {
        if (!param || !param.time) return;
        const candle = param.seriesData.get(candleSeries);
        if (candle) updateOHLCDisplay(candle);
    });

    // Resize handler
    new ResizeObserver(() => {
        chart.applyOptions({
            width: container.clientWidth,
        });
    }).observe(container);

    return chart;
}

function createRSIChart() {
    const container = document.getElementById("rsiChartContainer");
    const chart = LightweightCharts.createChart(container, {
        width: container.clientWidth,
        height: 110,
        layout: {
            background: { color: "#0d1117" },
            textColor: "#8b949e",
        },
        grid: {
            vertLines: { color: "#21262d" },
            horzLines: { color: "#21262d" },
        },
        rightPriceScale: { borderColor: "#30363d" },
        timeScale: { borderColor: "#30363d", timeVisible: true },
    });

    // RSI bounds
    const rsiSeries = chart.addLineSeries({
        color: "#ce93d8",
        lineWidth: 2,
        priceLineVisible: false,
        lastValueVisible: true,
        title: "RSI",
    });

    // Overbought/Oversold lines
    const ob = chart.addLineSeries({ color: "rgba(255,23,68,0.4)", lineWidth: 1, lineStyle: 2, priceLineVisible: false, lastValueVisible: false });
    const os = chart.addLineSeries({ color: "rgba(0,230,118,0.4)", lineWidth: 1, lineStyle: 2, priceLineVisible: false, lastValueVisible: false });

    state.rsiChart = chart;
    state.rsiSeries = rsiSeries;
    state.rsiOB = ob;
    state.rsiOS = os;

    new ResizeObserver(() => {
        chart.applyOptions({ width: container.clientWidth });
    }).observe(container);

    return chart;
}

function createMACDChart() {
    const container = document.getElementById("macdChartContainer");
    const chart = LightweightCharts.createChart(container, {
        width: container.clientWidth,
        height: 110,
        layout: {
            background: { color: "#0d1117" },
            textColor: "#8b949e",
        },
        grid: {
            vertLines: { color: "#21262d" },
            horzLines: { color: "#21262d" },
        },
        rightPriceScale: { borderColor: "#30363d" },
        timeScale: { borderColor: "#30363d", timeVisible: true },
    });

    const macdLine = chart.addLineSeries({
        color: "#1f6feb",
        lineWidth: 1.5,
        priceLineVisible: false,
        lastValueVisible: true,
        title: "MACD",
    });

    const signalLine = chart.addLineSeries({
        color: "#ff9100",
        lineWidth: 1.5,
        priceLineVisible: false,
        lastValueVisible: true,
        title: "Signal",
    });

    const histSeries = chart.addHistogramSeries({
        priceLineVisible: false,
        lastValueVisible: false,
        title: "Hist",
    });

    state.macdChart = chart;
    state.macdSeries = macdLine;
    state.macdSignalSeries = signalLine;
    state.macdHistSeries = histSeries;

    new ResizeObserver(() => {
        chart.applyOptions({ width: container.clientWidth });
    }).observe(container);

    return chart;
}

// ---- Data Loading ----
async function loadChartData() {
    const symbol = document.getElementById("symbolInput").value.trim().toUpperCase();
    if (!symbol) return;

    state.symbol = symbol;
    state.interval = document.querySelector(".btn-interval.active").dataset.interval;
    state.period = document.getElementById("periodSelect").value;

    const indicators = getSelectedIndicators();

    document.getElementById("loadingOverlay").classList.remove("hidden");
    document.getElementById("loadingOverlay").querySelector("p").textContent = `${symbol} のデータを取得中...`;

    try {
        const url = `${API_BASE}/api/chart/${symbol}?interval=${state.interval}&period=${state.period}&indicators=${indicators}`;
        const res = await fetch(url);
        const data = await res.json();

        if (data.error) {
            alert(`エラー: ${data.error}`);
            document.getElementById("loadingOverlay").querySelector("p").textContent = "銘柄を選択してチャートを表示";
            return;
        }

        // Init charts if not already
        if (!state.mainChart) {
            createMainChart();
            createRSIChart();
            createMACDChart();
        }

        // Show sub-charts if indicators selected
        const showRSI = indicators.includes("rsi");
        const showMACD = indicators.includes("macd");
        document.getElementById("rsiChart").classList.toggle("hidden", !showRSI);
        document.getElementById("macdChartDiv").classList.toggle("hidden", !showMACD);

        renderChartData(data);
        updateHeaderPrice(symbol, data.current_price, data.price_change_pct);
        updateSignals(data.signals);

        document.getElementById("signalBanner").classList.remove("hidden");
        document.getElementById("signalCards").classList.remove("hidden");
        document.getElementById("loadingOverlay").classList.add("hidden");

        // Start WebSocket
        connectWebSocket(symbol);

    } catch (err) {
        console.error(err);
        document.getElementById("loadingOverlay").querySelector("p").textContent = "データ取得エラー";
    }
}

function renderChartData(data) {
    const candles = data.candles;

    // Parse time to timestamp
    const parseTime = (timeStr) => {
        if (typeof timeStr === "number") return timeStr;
        const d = new Date(timeStr);
        return Math.floor(d.getTime() / 1000);
    };

    const candleData = candles.map(c => ({
        time: parseTime(c.time),
        open: c.open,
        high: c.high,
        low: c.low,
        close: c.close,
    })).filter(c => !isNaN(c.time) && c.time > 0);

    if (candleData.length === 0) return;

    // Sort by time
    candleData.sort((a, b) => a.time - b.time);

    state.candleSeries.setData(candleData);

    // MA Lines
    const indicators = getSelectedIndicators();

    if (indicators.includes("sma20")) {
        const sma20Data = candles
            .filter(c => c.sma20 !== undefined)
            .map(c => ({ time: parseTime(c.time), value: c.sma20 }))
            .filter(c => !isNaN(c.time));
        state.sma20Series.setData(sma20Data);
    }

    if (indicators.includes("sma50")) {
        const sma50Data = candles
            .filter(c => c.sma50 !== undefined)
            .map(c => ({ time: parseTime(c.time), value: c.sma50 }))
            .filter(c => !isNaN(c.time));
        state.sma50Series.setData(sma50Data);
    }

    if (indicators.includes("ema9")) {
        const ema9Data = candles
            .filter(c => c.ema9 !== undefined)
            .map(c => ({ time: parseTime(c.time), value: c.ema9 }))
            .filter(c => !isNaN(c.time));
        state.ema9Series.setData(ema9Data);
    }

    if (indicators.includes("bb")) {
        const bbU = candles.filter(c => c.bb_upper !== undefined).map(c => ({ time: parseTime(c.time), value: c.bb_upper })).filter(c => !isNaN(c.time));
        const bbM = candles.filter(c => c.bb_mid !== undefined).map(c => ({ time: parseTime(c.time), value: c.bb_mid })).filter(c => !isNaN(c.time));
        const bbL = candles.filter(c => c.bb_lower !== undefined).map(c => ({ time: parseTime(c.time), value: c.bb_lower })).filter(c => !isNaN(c.time));
        state.bbUpperSeries.setData(bbU);
        state.bbMidSeries.setData(bbM);
        state.bbLowerSeries.setData(bbL);
    }

    // RSI Chart
    if (indicators.includes("rsi")) {
        const rsiData = candles
            .filter(c => c.rsi !== undefined)
            .map(c => ({ time: parseTime(c.time), value: c.rsi }))
            .filter(c => !isNaN(c.time));
        state.rsiSeries.setData(rsiData);

        // OB/OS reference lines
        if (rsiData.length > 0) {
            const first = rsiData[0].time;
            const last = rsiData[rsiData.length - 1].time;
            state.rsiOB.setData([{ time: first, value: 70 }, { time: last, value: 70 }]);
            state.rsiOS.setData([{ time: first, value: 30 }, { time: last, value: 30 }]);
        }
    }

    // MACD Chart
    if (indicators.includes("macd")) {
        const macdData = candles.filter(c => c.macd !== undefined).map(c => ({ time: parseTime(c.time), value: c.macd })).filter(c => !isNaN(c.time));
        const signalData = candles.filter(c => c.macd_signal !== undefined).map(c => ({ time: parseTime(c.time), value: c.macd_signal })).filter(c => !isNaN(c.time));
        const histData = candles
            .filter(c => c.macd_hist !== undefined)
            .map(c => ({
                time: parseTime(c.time),
                value: c.macd_hist,
                color: c.macd_hist >= 0 ? "rgba(0,230,118,0.7)" : "rgba(255,23,68,0.7)"
            }))
            .filter(c => !isNaN(c.time));

        state.macdSeries.setData(macdData);
        state.macdSignalSeries.setData(signalData);
        state.macdHistSeries.setData(histData);
    }

    // Fit content
    state.mainChart.timeScale().fitContent();
}

// ---- WebSocket ----
function connectWebSocket(symbol) {
    if (state.ws) {
        state.ws.close();
    }

    const wsUrl = `${WS_BASE}/ws/${symbol}?interval=${state.interval}`;
    state.ws = new WebSocket(wsUrl);

    state.ws.onopen = () => {
        console.log(`WebSocket connected: ${symbol}`);
    };

    state.ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.type === "update") {
            handleRealtimeUpdate(msg);
        }
    };

    state.ws.onerror = (err) => {
        console.error("WebSocket error:", err);
    };

    state.ws.onclose = () => {
        console.log("WebSocket closed");
        // Reconnect after 5s
        setTimeout(() => {
            if (state.symbol === symbol) {
                connectWebSocket(symbol);
            }
        }, 5000);
    };
}

function handleRealtimeUpdate(msg) {
    updateHeaderPrice(msg.symbol, msg.price, msg.change_pct);
    updateSignals(msg.signals);

    if (msg.candle && state.candleSeries) {
        const parseTime = (t) => {
            if (typeof t === "number") return t;
            const d = new Date(t);
            return Math.floor(d.getTime() / 1000);
        };
        const candle = msg.candle;
        const time = parseTime(candle.time);
        if (!isNaN(time) && time > 0) {
            state.candleSeries.update({ time, open: candle.open, high: candle.high, low: candle.low, close: candle.close });

            if (candle.sma20 && state.sma20Series) state.sma20Series.update({ time, value: candle.sma20 });
            if (candle.sma50 && state.sma50Series) state.sma50Series.update({ time, value: candle.sma50 });
            if (candle.ema9 && state.ema9Series) state.ema9Series.update({ time, value: candle.ema9 });
            if (candle.bb_upper && state.bbUpperSeries) state.bbUpperSeries.update({ time, value: candle.bb_upper });
            if (candle.bb_mid && state.bbMidSeries) state.bbMidSeries.update({ time, value: candle.bb_mid });
            if (candle.bb_lower && state.bbLowerSeries) state.bbLowerSeries.update({ time, value: candle.bb_lower });
            if (candle.rsi && state.rsiSeries) state.rsiSeries.update({ time, value: candle.rsi });
            if (candle.macd && state.macdSeries) state.macdSeries.update({ time, value: candle.macd });
            if (candle.macd_signal && state.macdSignalSeries) state.macdSignalSeries.update({ time, value: candle.macd_signal });
            if (candle.macd_hist !== undefined && state.macdHistSeries) {
                state.macdHistSeries.update({
                    time,
                    value: candle.macd_hist,
                    color: candle.macd_hist >= 0 ? "rgba(0,230,118,0.7)" : "rgba(255,23,68,0.7)"
                });
            }
        }
    }

    // Auto trade log
    if (msg.auto_trade) {
        addTradeLog(msg.auto_trade);
        document.getElementById("tradeLog").classList.remove("hidden");
    }
}

// ---- Signal Display ----
function updateSignals(signals) {
    if (!signals || !signals.overall) return;

    const overall = signals.overall;
    const action = overall.action;
    const strength = overall.strength;
    const score = overall.score || 0;

    // Banner
    const actionEl = document.getElementById("signalAction");
    actionEl.textContent = action === "BUY" ? "買い ▲" : action === "SELL" ? "売り ▼" : "様子見";
    actionEl.className = `signal-action ${action}`;

    document.getElementById("signalStrength").textContent = `強度: ${strength}%`;
    document.getElementById("signalDesc").textContent = overall.desc || "";

    // Meter: score from -100 to +100, map to 0-100%
    const meterPct = Math.max(0, Math.min(100, (score + 100) / 2));
    document.getElementById("meterFill").style.left = `calc(${meterPct}% - 7px)`;

    // Signal cards
    const cardMap = {
        rsi: "rsi",
        macd: "macd",
        bb: "bb",
        ma: "ma",
        ema: "ema",
    };

    for (const [key, id] of Object.entries(cardMap)) {
        const sig = signals[key];
        if (!sig) continue;
        const card = document.getElementById(`card-${id}`);
        const actionEl2 = document.getElementById(`${id}-action`);
        const descEl = document.getElementById(`${id}-desc`);

        actionEl2.textContent = sig.action === "BUY" ? "買い ▲" : sig.action === "SELL" ? "売り ▼" : "様子見";
        actionEl2.className = `card-action ${sig.action}`;
        descEl.textContent = sig.desc || "";

        card.className = `signal-card ${sig.action.toLowerCase()}`;
    }

    // RSI indicator value display
    if (signals.rsi) {
        const rsiEl = document.getElementById("rsiValue");
        const rsiVal = signals.rsi.value;
        rsiEl.textContent = `${rsiVal}`;
        rsiEl.style.color = rsiVal <= 30 ? "#00e676" : rsiVal >= 70 ? "#ff1744" : "#ffd740";
    }

    // MACD indicator value display
    if (signals.macd) {
        const macdEl = document.getElementById("macdValue");
        macdEl.textContent = `${signals.macd.value} / ${signals.macd.signal_value}`;
        macdEl.style.color = signals.macd.color;
    }
}

function updateHeaderPrice(symbol, price, changePct) {
    document.getElementById("headerSymbol").textContent = symbol;
    document.getElementById("headerPriceVal").textContent = formatPrice(price);

    const changeEl = document.getElementById("headerChangePct");
    changeEl.textContent = `${changePct >= 0 ? "+" : ""}${changePct.toFixed(2)}%`;
    changeEl.className = `change-pct ${changePct >= 0 ? "positive" : "negative"}`;
}

function updateOHLCDisplay(candle) {
    document.getElementById("ohlcDisplay").innerHTML = `
        <span><span class="label">O</span><span class="ohlc-o">${formatPrice(candle.open)}</span></span>
        <span><span class="label">H</span><span class="ohlc-h">${formatPrice(candle.high)}</span></span>
        <span><span class="label">L</span><span class="ohlc-l">${formatPrice(candle.low)}</span></span>
        <span><span class="label">C</span><span class="ohlc-c">${formatPrice(candle.close)}</span></span>
    `;
}

// ---- Trade Log ----
function addTradeLog(trade) {
    const tbody = document.getElementById("tradeTableBody");
    const row = document.createElement("tr");
    row.className = trade.action === "BUY" ? "trade-buy" : "trade-sell";

    const time = new Date(trade.timestamp).toLocaleTimeString("ja-JP");
    const pnl = trade.pnl !== undefined
        ? `<span class="${trade.pnl >= 0 ? "pnl-positive" : "pnl-negative"}">${trade.pnl >= 0 ? "+" : ""}¥${trade.pnl.toLocaleString()} (${trade.pnl_pct >= 0 ? "+" : ""}${trade.pnl_pct}%)</span>`
        : "-";

    row.innerHTML = `
        <td>${time}</td>
        <td>${trade.action === "BUY" ? "買い ▲" : "売り ▼"}</td>
        <td>${formatPrice(trade.price)}</td>
        <td>${trade.quantity}株</td>
        <td>${pnl}</td>
        <td>${trade.reason || "-"}</td>
    `;

    tbody.insertBefore(row, tbody.firstChild);
}

// ---- Utils ----
function formatPrice(price) {
    if (price === undefined || price === null) return "-";
    if (price >= 1000) return price.toLocaleString("ja-JP", { minimumFractionDigits: 0, maximumFractionDigits: 0 });
    if (price >= 1) return price.toFixed(2);
    return price.toFixed(4);
}

function getSelectedIndicators() {
    const checked = document.querySelectorAll(".indicator-check input[type='checkbox']:checked");
    return Array.from(checked).map(el => el.dataset.indicator).join(",");
}

// ---- Event Listeners ----
document.getElementById("loadBtn").addEventListener("click", loadChartData);

document.getElementById("symbolInput").addEventListener("keydown", (e) => {
    if (e.key === "Enter") loadChartData();
});

// Symbol search
document.getElementById("symbolInput").addEventListener("input", async (e) => {
    const q = e.target.value.trim();
    const results = document.getElementById("searchResults");

    if (q.length < 1) {
        results.classList.add("hidden");
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/api/symbols/search?q=${encodeURIComponent(q)}`);
        const data = await res.json();

        if (data.length === 0) {
            results.classList.add("hidden");
            return;
        }

        results.innerHTML = data.map(s => `
            <div class="search-result-item" data-symbol="${s.symbol}">
                <span class="search-symbol">${s.symbol}</span>
                <span class="search-name">${s.name}</span>
            </div>
        `).join("");

        results.classList.remove("hidden");

        results.querySelectorAll(".search-result-item").forEach(item => {
            item.addEventListener("click", () => {
                document.getElementById("symbolInput").value = item.dataset.symbol;
                results.classList.add("hidden");
                loadChartData();
            });
        });
    } catch (err) {
        results.classList.add("hidden");
    }
});

// Hide search results on click outside
document.addEventListener("click", (e) => {
    if (!e.target.closest(".search-wrap")) {
        document.getElementById("searchResults").classList.add("hidden");
    }
});

// Interval buttons
document.getElementById("intervalGroup").querySelectorAll(".btn-interval").forEach(btn => {
    btn.addEventListener("click", () => {
        document.querySelectorAll(".btn-interval").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        state.interval = btn.dataset.interval;
        if (state.symbol) loadChartData();
    });
});

// Period select
document.getElementById("periodSelect").addEventListener("change", () => {
    if (state.symbol) loadChartData();
});

// Auto trade toggle
document.getElementById("autoTradeToggle").addEventListener("change", (e) => {
    document.getElementById("autoTradeConfig").classList.toggle("hidden", !e.target.checked);
    if (!e.target.checked && state.symbol) {
        // Disable auto trade
        fetch(`${API_BASE}/api/auto-trade/${state.symbol}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ enabled: false }),
        });
        document.getElementById("tradeLog").classList.add("hidden");
    }
});

// Range inputs display
["buyThreshold", "sellThreshold"].forEach(id => {
    document.getElementById(id).addEventListener("input", (e) => {
        document.getElementById(`${id}Val`).textContent = `${e.target.value}%`;
    });
});

// Apply auto trade config
document.getElementById("applyAutoTrade").addEventListener("click", async () => {
    if (!state.symbol) {
        alert("先に銘柄を選択してください");
        return;
    }

    const config = {
        enabled: true,
        strategy: document.getElementById("strategySelect").value,
        buy_threshold: parseInt(document.getElementById("buyThreshold").value),
        sell_threshold: parseInt(document.getElementById("sellThreshold").value),
        stop_loss_pct: parseFloat(document.getElementById("stopLoss").value),
        take_profit_pct: parseFloat(document.getElementById("takeProfit").value),
        max_position: parseInt(document.getElementById("maxPosition").value),
    };

    const res = await fetch(`${API_BASE}/api/auto-trade/${state.symbol}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
    });
    const data = await res.json();

    if (data.status === "configured") {
        document.getElementById("tradeLog").classList.remove("hidden");
        alert(`自動売買を有効化しました (${state.symbol})\n※シミュレーションモード`);
    }
});

// Indicator checkboxes reload chart
document.querySelectorAll(".indicator-check input[type='checkbox']").forEach(cb => {
    cb.addEventListener("change", () => {
        if (state.symbol) loadChartData();
    });
});

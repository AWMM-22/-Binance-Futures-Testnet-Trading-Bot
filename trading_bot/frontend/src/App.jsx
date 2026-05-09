import { useEffect, useMemo, useState } from "react";
import StatCard from "./components/StatCard.jsx";
import DataTable from "./components/DataTable.jsx";

const formatUsd = (value) => {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "-";
  }
  return `$${Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
};

const formatNumber = (value) => {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "-";
  }
  return Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 });
};

const formatPercent = (value) => {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "-";
  }
  const amount = Number(value);
  const sign = amount > 0 ? "+" : "";
  return `${sign}${amount.toFixed(2)}%`;
};

const formatTime = (value) => {
  if (!value) {
    return "-";
  }
  return new Date(Number(value)).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit"
  });
};

const formatDateTime = (value) => {
  if (!value) {
    return "-";
  }
  return new Date(Number(value)).toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  });
};

const App = () => {
  const apiBase = import.meta.env.VITE_API_BASE || "http://localhost:8000";
  const [health, setHealth] = useState(null);
  const [marketOverview, setMarketOverview] = useState([]);
  const [recentTrades, setRecentTrades] = useState([]);
  const [symbolInfo, setSymbolInfo] = useState(null);
  const [symbolLoading, setSymbolLoading] = useState(false);
  const [symbolError, setSymbolError] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const [form, setForm] = useState({
    symbol: "BTCUSDT",
    side: "BUY",
    type: "MARKET",
    quantity: "0.001",
    price: "",
    stopPrice: "",
    dryRun: false
  });
  const [orderResult, setOrderResult] = useState(null);

  const fetchJson = async (path) => {
    const response = await fetch(`${apiBase}${path}`);
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data.detail || "Request failed");
    }
    return response.json();
  };

  const lookupSymbol = async (symbol) => {
    const normalizedSymbol = symbol.trim().toUpperCase();
    if (!normalizedSymbol) {
      setSymbolInfo(null);
      setSymbolError("");
      return;
    }

    setSymbolLoading(true);
    setSymbolError("");
    try {
      const data = await fetchJson(`/market/symbol?symbol=${encodeURIComponent(normalizedSymbol)}`);
      setSymbolInfo(data);
    } catch (err) {
      setSymbolInfo(null);
      setSymbolError(err.message || "Symbol lookup failed");
    } finally {
      setSymbolLoading(false);
    }
  };

  const refresh = async () => {
    setLoading(true);
    setError("");
    try {
      const [healthData, overviewData, tradesData] = await Promise.all([
        fetchJson("/health"),
        fetchJson("/market/summary?limit=6"),
        fetchJson("/market/trades?symbol=BTCUSDT&limit=10")
      ]);
      setHealth(healthData);
      setMarketOverview(overviewData);
      setRecentTrades(tradesData);
    } catch (err) {
      setError(err.message || "Failed to load data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      lookupSymbol(form.symbol);
    }, 350);

    return () => window.clearTimeout(timer);
  }, [form.symbol]);

  const stats = useMemo(() => {
    const btc = marketOverview.find((item) => item.symbol === "BTCUSDT") || marketOverview[0];
    const lastPrice = btc ? Number(btc.lastPrice) : null;
    const changePercent = btc ? Number(btc.priceChangePercent) : null;
    const quoteVolume = btc ? Number(btc.quoteVolume) : null;
    const latency = health?.latency_ms ? `${health.latency_ms}ms` : "-";

    return [
      {
        label: "BTC Price",
        value: formatUsd(lastPrice),
        delta: "BTCUSDT",
        tone: changePercent >= 0 ? "up" : "down"
      },
      {
        label: "24h Change",
        value: formatPercent(changePercent),
        delta: "Testnet",
        tone: changePercent >= 0 ? "up" : "down"
      },
      {
        label: "24h Volume",
        value: formatNumber(quoteVolume),
        delta: "USDT",
        tone: "neutral"
      },
      {
        label: "Latency",
        value: latency,
        delta: "Live data",
        tone: "neutral"
      }
    ];
  }, [marketOverview, health]);

  const marketRows = marketOverview.map((item) => ({
    id: item.symbol,
    values: [
      item.symbol,
      formatUsd(item.lastPrice),
      formatPercent(item.priceChangePercent),
      formatNumber(item.quoteVolume)
    ]
  }));

  const tradeRows = recentTrades.map((item) => ({
    id: `${item.id}`,
    values: [
      `#${item.id}`,
      formatUsd(item.price),
      formatNumber(item.qty),
      item.isBuyerMaker ? "Sell" : "Buy",
      formatTime(item.time)
    ]
  }));

  const symbolStats = symbolInfo
    ? [
        { label: "Last Price", value: formatUsd(symbolInfo.lastPrice) },
        { label: "24h Change", value: formatPercent(symbolInfo.priceChangePercent) },
        { label: "24h High", value: formatUsd(symbolInfo.highPrice) },
        { label: "24h Low", value: formatUsd(symbolInfo.lowPrice) },
        { label: "Mark Price", value: formatUsd(symbolInfo.markPrice) },
        { label: "Funding Rate", value: formatPercent(symbolInfo.fundingRate) },
        { label: "Open Interest", value: formatNumber(symbolInfo.openInterest) },
        { label: "Next Funding", value: formatDateTime(symbolInfo.nextFundingTime) }
      ]
    : [];

  const onChange = (field) => (event) => {
    const value = event.target.type === "checkbox" ? event.target.checked : event.target.value;
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const submitOrder = async (event) => {
    event.preventDefault();
    setError("");
    setOrderResult(null);
    try {
      const payload = {
        symbol: form.symbol.trim().toUpperCase(),
        side: form.side,
        type: form.type,
        quantity: Number(form.quantity),
        price: form.price ? Number(form.price) : null,
        stopPrice: form.stopPrice ? Number(form.stopPrice) : null,
        dry_run: form.dryRun
      };
      const response = await fetch(`${apiBase}/orders`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.detail || "Order failed");
      }
      setOrderResult(data);
      await refresh();
    } catch (err) {
      setError(err.message || "Order failed");
    }
  };

  return (
    <div className="page">
      <div className="background-glow" />
      <header className="hero">
        <div>
          <p className="eyebrow">Binance Futures Market Data</p>
          <h1>
            Track live <span>Binance futures</span> market activity
          </h1>
          <p className="subtitle">
            Public market data pulled with the Binance library. No API key is
            required to view prices, tickers, and recent trades.
          </p>
          <div className="hero-actions">
            <button className="primary-button" type="button" onClick={refresh}>
              Refresh Data
            </button>
            <a className="secondary-button" href="/" onClick={(event) => event.preventDefault()}>
              Connected to API
            </a>
          </div>
          {error && <div className="error-banner">{error}</div>}
        </div>
        <aside className="hero-card">
          <h2>PUBLIC MARKET MODE</h2>
          <p>API: {apiBase}</p>
          <div className="hero-metrics">
            <div>
              <span>Status</span>
              <strong>{health ? "Online" : "Unknown"}</strong>
            </div>
            <div>
              <span>Latency</span>
              <strong>{health?.latency_ms ? `${health.latency_ms}ms` : "-"}</strong>
            </div>
            <div>
              <span>Updated</span>
              <strong>{loading ? "Loading" : "Now"}</strong>
            </div>
          </div>
        </aside>
      </header>

      <section className="stats-grid">
        {stats.map((stat) => (
          <StatCard key={stat.label} {...stat} />
        ))}
      </section>

      <section className="order-form">
        <div>
          <h2>Place Order</h2>
          <p>Trading requires Binance API credentials. Market data remains public.</p>
        </div>
        <div className="order-layout">
          <form onSubmit={submitOrder}>
            <label>
              Symbol
              <input value={form.symbol} onChange={onChange("symbol")} />
            </label>
            <label>
              Side
              <select value={form.side} onChange={onChange("side")}>
                <option value="BUY">BUY</option>
                <option value="SELL">SELL</option>
              </select>
            </label>
            <label>
              Type
              <select value={form.type} onChange={onChange("type")}>
                <option value="MARKET">MARKET</option>
                <option value="LIMIT">LIMIT</option>
                <option value="STOP_MARKET">STOP_MARKET</option>
              </select>
            </label>
            <label>
              Quantity
              <input value={form.quantity} onChange={onChange("quantity")} />
            </label>
            {form.type === "LIMIT" && (
              <label>
                Price
                <input value={form.price} onChange={onChange("price")} />
              </label>
            )}
            {form.type === "STOP_MARKET" && (
              <label>
                Stop Price
                <input value={form.stopPrice} onChange={onChange("stopPrice")} />
              </label>
            )}
            <label className="checkbox">
              <input type="checkbox" checked={form.dryRun} onChange={onChange("dryRun")} />
              Dry-run
            </label>
            <button className="primary-button" type="submit">
              Submit Order
            </button>
          </form>
          <aside className="symbol-panel">
            <div className="symbol-panel-header">
              <div>
                <p className="panel-eyebrow">Symbol Lookup</p>
                <h3>{form.symbol.trim().toUpperCase() || "Search a symbol"}</h3>
              </div>
              <span className={`lookup-pill ${symbolLoading ? "is-loading" : symbolInfo ? "is-ready" : ""}`}>
                {symbolLoading ? "Loading" : symbolInfo ? "Live" : "Idle"}
              </span>
            </div>
            {symbolError && <div className="symbol-error">{symbolError}</div>}
            {symbolInfo ? (
              <>
                <div className="symbol-grid">
                  {symbolStats.map((item) => (
                    <div key={item.label}>
                      <span>{item.label}</span>
                      <strong>{item.value}</strong>
                    </div>
                  ))}
                </div>
                <div className="symbol-meta">
                  <span>Status: {symbolInfo.status || "-"}</span>
                  <span>Pair: {symbolInfo.baseAsset}/{symbolInfo.quoteAsset}</span>
                  <span>Contract: {symbolInfo.contractType || "-"}</span>
                  <span>Precision: {symbolInfo.pricePrecision}/{symbolInfo.quantityPrecision}</span>
                </div>
              </>
            ) : (
              <p className="symbol-hint">
                Type a futures symbol such as BTCUSDT, ETHUSDT, or SOLUSDT to see live Binance market data.
              </p>
            )}
          </aside>
        </div>
        {orderResult && (
          <div className="order-result">
            <p>Order ID: {orderResult.order?.orderId}</p>
            <p>Status: {orderResult.order?.status}</p>
            <p>Latency: {orderResult.latency_ms?.toFixed(0)}ms</p>
          </div>
        )}
      </section>

      <section className="grid">
        <DataTable
          title="Market Overview"
          columns={["Symbol", "Last Price", "24h Change", "Quote Volume"]}
          rows={marketRows}
        />
        <DataTable
          title="Recent Trades"
          columns={["Trade ID", "Price", "Qty", "Side", "Time"]}
          rows={tradeRows}
        />
      </section>
    </div>
  );
};

export default App;

# Binance Futures Testnet Trading Bot

A full-stack Binance Futures Testnet trading workspace with a Python backend, a React frontend, and a CLI. It is designed to be easy to understand, but still structured like a real trading tool: separate data access, validation, execution, and presentation layers.

The project supports two modes:

- Public market mode: no API key required for live symbol lookup, prices, funding rate, open interest, and recent trades.
- Trading mode: API key and secret required for placing orders and reading private account data.

## What This Project Does

- Shows live Binance Futures market data in the browser.
- Lets you search a symbol and inspect current price movement before trading.
- Places MARKET, LIMIT, and STOP_MARKET orders on Binance Futures Testnet.
- Provides a CLI for people who prefer the terminal.
- Uses validation and retries so bad inputs and network issues are handled cleanly.

## Main Features

- Live public symbol lookup with price, 24h change, high, low, mark price, funding rate, and open interest.
- Public market overview and recent trade feed.
- Order entry for BUY and SELL actions.
- Dry-run mode for safe testing.
- Python backend with FastAPI.
- React frontend with Vite.
- CLI commands with Typer and Rich output.
- Exchange-aware validation using Binance symbol metadata.
- Structured logging with Loguru.

## Project Structure

```text
trading_bot/
├── backend/
│   └── app.py
├── bot/
│   ├── client.py
│   ├── config.py
│   ├── constants.py
│   ├── exceptions.py
│   ├── formatter.py
│   ├── logging_config.py
│   ├── orders.py
│   ├── utils.py
│   └── validators.py
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx
│       ├── main.jsx
│       ├── styles.css
│       └── components/
├── tests/
├── logs/
├── sample_logs/
├── cli.py
├── requirements.txt
└── README.md
```

## Tech Stack

- Python 3.11
- FastAPI
- Uvicorn
- python-binance
- Pydantic and Pydantic Settings
- Typer
- Rich
- Loguru
- React 18
- Vite

## How It Works

### Backend

The backend talks to Binance through `python-binance` and exposes a small HTTP API for the frontend.

Useful endpoints:

- `/health` checks connectivity.
- `/market/summary` returns a small live market snapshot.
- `/market/trades` returns recent public trades for a symbol.
- `/market/symbol` returns the current market details for a single symbol.
- `/orders` submits a testnet order.

### Frontend

The frontend is a live dashboard. When you type a symbol in the order form, it fetches the current Binance market snapshot and shows the most important values before you submit anything.

### CLI

The CLI is useful when you want to work from the terminal. It supports order placement, balance, positions, history, and ping commands.

## Output Images
<img width="1905" height="988" alt="Screenshot 2026-05-09 144701" src="https://github.com/user-attachments/assets/ef724d24-64df-47eb-9b36-7016d4d69b0c" />
<img width="1900" height="984" alt="Screenshot 2026-05-09 144800" src="https://github.com/user-attachments/assets/4c976611-c623-4d48-b30e-44495aac8179" />
<img width="1897" height="992" alt="Screenshot 2026-05-09 144902" src="https://github.com/user-attachments/assets/3c72c1fa-842c-4802-bff3-a18fc1189977" />
<img width="1901" height="988" alt="Screenshot 2026-05-09 144924" src="https://github.com/user-attachments/assets/bb2bd350-2275-4f0f-9b35-65c875ca7f1a" />




## Setup

### 1. Install Python dependencies

Use Python 3.11.

```bash
cd trading_bot
py -3.11 -m venv .venv311
.venv311\Scripts\activate
pip install -r requirements.txt
```

### 2. Set environment variables

Create a `.env` file in `trading_bot/`.

```env
BINANCE_API_KEY=
BINANCE_API_SECRET=
BINANCE_BASE_URL=https://testnet.binancefuture.com
```

You can leave the key and secret empty if you only want public market data. They are required for placing orders.

### 3. Install frontend dependencies

```bash
cd frontend
npm install
```

## Run the Project

### Start the backend

From the `trading_bot` folder:

```bash
uvicorn --app-dir . backend.app:app --host 0.0.0.0 --port 8000
```

### Start the frontend

From the `trading_bot/frontend` folder:

```bash
npm run dev
```

The frontend usually runs on `http://localhost:5173` and the backend on `http://localhost:8000`.

## CLI Commands

```bash
python cli.py ping
python cli.py balance
python cli.py positions
python cli.py history --limit 20
python cli.py order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
python cli.py order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001 --dry-run
```

## Example Workflow

1. Open the frontend.
2. Type a symbol like `BTCUSDT` or `DOGEUSDT`.
3. Review the live symbol snapshot on the right side.
4. Check the price, 24h movement, mark price, funding rate, and open interest.
5. Submit an order only if you have Binance API credentials configured.

## Error Handling

- Invalid symbols are rejected by exchange-aware validation.
- Network and Binance API errors are wrapped in readable messages.
- Retry logic is used for transient request failures.
- The UI shows loading and error states so users know what is happening.

## Logging

- Logs are written to `logs/trading_bot.log`.
- Log rotation keeps the files from growing too large.
- Request details, retries, and errors are recorded for debugging.

## Notes

- Public market data does not require API credentials.
- Private trading actions do require a Binance API key and secret.
- The project is intended for Binance Futures Testnet, not live trading.

## Future Improvements

- Symbol search autocomplete.
- Candlestick charts and order book depth.
- Better account analytics for authenticated users.
- Trade history export.
- Risk and position sizing tools.

## Why This Structure

The codebase is split into clear layers so it stays maintainable:

- `bot/` contains the trading logic and Binance client wrapper.
- `backend/` exposes those features over HTTP.
- `frontend/` gives you a browser dashboard.
- `cli.py` keeps the terminal workflow available.

That separation makes the project easier to test, easier to extend, and easier to debug when something goes wrong.

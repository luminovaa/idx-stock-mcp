# IDX Stock MCP Server

MCP (Model Context Protocol) server untuk analisis saham Indonesia (IDX). Menyediakan 12 tools untuk data harga, indikator teknikal, fundamental, money flow, sentimen berita, data makro, dan kalkulasi risk management.

## Tools

| # | Tool | Fungsi |
|---|------|--------|
| 1 | `get_stock_price` | Harga OHLCV + current price + change % |
| 2 | `get_technical_indicators` | RSI, MACD, EMA, Bollinger Bands, Stochastic, Volume |
| 3 | `get_adx_trend` | ADX, +DI/-DI, trend direction & strength |
| 4 | `get_fundamental_data` | PER, PBV, ROE, DER, margins, growth |
| 5 | `get_money_flow` | OBV, MFI, foreign flow, smart money score |
| 6 | `get_broker_summary` | Top buyer/seller brokers |
| 7 | `get_news_sentiment` | Headlines dari media Indonesia |
| 8 | `get_macro_data` | IHSG, S&P500, HSI, USD/IDR, global sentiment |
| 9 | `calculate_support_resistance` | Support/resistance levels + distance % |
| 10 | `calculate_position_size` | Position sizing (2% rule), SL, TP, R:R |
| 11 | `get_stock_list` | List saham dalam index (LQ45, IDX30) |
| 12 | `screen_stocks` | Filter saham berdasarkan kriteria teknikal |

## Installation

```bash
# Clone
git clone <repo-url>
cd idx-stock-mcp

# Install dependencies (using uv)
uv sync

# Or using pip
pip install -e .
```

## Configuration

Copy `.env.example` ke `.env` dan isi API keys:

```bash
cp .env.example .env
```

**Required:**
- `ALPHAVANTAGE_API_KEY` - Untuk data fundamental tambahan dan forex

**Optional:**
- `IDX_API_KEY` - Untuk broker summary dan foreign flow
- `AJAIB_API_KEY` - Untuk data tambahan money flow

## Usage

### Sebagai MCP Server (stdio)

```bash
# Run langsung
uv run idx-stock-mcp

# Atau
python -m src.server
```

### Konfigurasi di Claude Desktop / OpenCode

Tambahkan ke `claude_desktop_config.json` atau MCP config:

```json
{
  "mcpServers": {
    "idx-stock": {
      "command": "uv",
      "args": ["--directory", "D:/projek/dataku/idx-stock-mcp", "run", "idx-stock-mcp"]
    }
  }
}
```

### Contoh Penggunaan Tools

```
// Get harga BBCA
get_stock_price(symbol="BBCA", period="3mo")

// Get indikator teknikal
get_technical_indicators(symbol="BBCA")

// Get data fundamental
get_fundamental_data(symbol="BBCA")

// Get money flow
get_money_flow(symbol="BBCA")

// Get data makro global
get_macro_data()

// Hitung support/resistance
calculate_support_resistance(symbol="BBCA")

// Hitung position size
calculate_position_size(symbol="BBCA", capital=10000000, risk_pct=2.0)

// Screen saham LQ45
screen_stocks(index="LQ45", min_adx=20, above_ema50=true)
```

## Data Sources

- **yfinance** - Harga OHLCV, info perusahaan (primary)
- **Alpha Vantage** - Fundamental data, forex rates
- **IDX API** - Broker summary, foreign flow
- **Ajaib** - Additional money flow data
- **News scraping** - Bisnis.com, Kontan.co.id

## Project Structure

```
idx-stock-mcp/
├── src/
│   ├── server.py              # MCP server entry point
│   ├── tools/
│   │   ├── price.py           # get_stock_price
│   │   ├── technical.py       # get_technical_indicators, get_adx_trend
│   │   ├── fundamental.py     # get_fundamental_data
│   │   ├── money_flow.py      # get_money_flow, get_broker_summary
│   │   ├── sentiment.py       # get_news_sentiment
│   │   ├── macro.py           # get_macro_data
│   │   ├── calculations.py    # support/resistance, position size
│   │   └── screener.py        # get_stock_list, screen_stocks
│   ├── data_sources/
│   │   ├── yfinance_client.py
│   │   ├── alphavantage_client.py
│   │   ├── idx_client.py
│   │   ├── ajaib_client.py
│   │   └── news_scraper.py
│   └── utils/
│       ├── cache.py           # TTL caching
│       └── indicators.py      # TA calculations
├── pyproject.toml
├── .env.example
└── README.md
```

## Related Project

- **idx-decision** - Web app yang menggunakan MCP server ini sebagai data backbone untuk 8-Gate AI Decision System

## License

MIT

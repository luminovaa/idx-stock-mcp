"""IDX Stock MCP Server - Main entry point.

Provides tools for Indonesian stock market analysis:
- Stock price & OHLCV data
- Technical indicators (RSI, MACD, EMA, BB, Stochastic, ADX)
- Fundamental data (PER, PBV, ROE, DER, growth)
- Money flow (OBV, MFI, foreign flow, broker summary)
- News sentiment
- Macro data (IHSG, S&P500, HSI, USD/IDR)
- Support/Resistance calculation
- Position sizing & risk management
- Stock screener
"""

import asyncio
import json
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .tools.price import get_stock_price
from .tools.technical import get_technical_indicators, get_adx_trend
from .tools.fundamental import get_fundamental_data
from .tools.money_flow import get_money_flow, get_broker_summary
from .tools.sentiment import get_news_sentiment
from .tools.macro import get_macro_data
from .tools.calculations import calculate_support_resistance, calculate_position_size
from .tools.screener import get_stock_list, screen_stocks

# Load environment variables
load_dotenv()

# Create MCP server
server = Server("idx-stock-mcp")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools."""
    return [
        Tool(
            name="get_stock_price",
            description="Get current stock price and historical OHLCV data for an IDX stock. Returns current price, change, volume, and recent price history.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "IDX stock symbol (e.g., 'BBCA', 'TLKM', 'BBRI')",
                    },
                    "period": {
                        "type": "string",
                        "description": "Data period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y (default: 1mo)",
                        "default": "1mo",
                    },
                },
                "required": ["symbol"],
            },
        ),
        Tool(
            name="get_technical_indicators",
            description="Get comprehensive technical indicators for an IDX stock: RSI(14), MACD(12,26,9), EMA(20,50,200), Bollinger Bands, Stochastic, Volume analysis, ATR.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "IDX stock symbol (e.g., 'BBCA', 'TLKM')",
                    },
                },
                "required": ["symbol"],
            },
        ),
        Tool(
            name="get_adx_trend",
            description="Get ADX trend strength analysis: ADX value, +DI/-DI, trend direction (uptrend/downtrend), and strength assessment. ADX >= 20 indicates a trend exists.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "IDX stock symbol (e.g., 'BBCA')",
                    },
                },
                "required": ["symbol"],
            },
        ),
        Tool(
            name="get_fundamental_data",
            description="Get fundamental data for an IDX stock: valuation (PER, PBV), profitability (ROE, margins), financial health (DER, current ratio), growth metrics, and dividends.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "IDX stock symbol (e.g., 'BBCA', 'BBRI')",
                    },
                },
                "required": ["symbol"],
            },
        ),
        Tool(
            name="get_money_flow",
            description="Get money flow analysis: OBV trend, MFI, volume ratio, foreign net buy/sell (5d & 20d), smart money score (0-5), and accumulation/distribution signal.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "IDX stock symbol (e.g., 'BBCA')",
                    },
                },
                "required": ["symbol"],
            },
        ),
        Tool(
            name="get_broker_summary",
            description="Get broker summary showing top 5 buyer and seller brokers for a stock on a specific date. Shows institutional activity.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "IDX stock symbol (e.g., 'BBCA')",
                    },
                    "date": {
                        "type": "string",
                        "description": "Trading date in YYYY-MM-DD format (default: latest trading day)",
                    },
                },
                "required": ["symbol"],
            },
        ),
        Tool(
            name="get_news_sentiment",
            description="Get latest news headlines and snippets from Indonesian financial media (Bisnis.com, Kontan.co.id) for sentiment analysis of a stock.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "IDX stock symbol (e.g., 'BBCA')",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max news items per source (default: 10)",
                        "default": 10,
                    },
                },
                "required": ["symbol"],
            },
        ),
        Tool(
            name="get_macro_data",
            description="Get macro economic and global market data: IHSG, S&P500, Hang Seng trends, USD/IDR exchange rate, and global risk sentiment (risk_on/risk_off/mixed).",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="calculate_support_resistance",
            description="Calculate support and resistance levels using pivot points, previous lows, EMA50/200. Returns distance to nearest support (%) and pass/fail for <= 5% threshold.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "IDX stock symbol (e.g., 'BBCA')",
                    },
                },
                "required": ["symbol"],
            },
        ),
        Tool(
            name="calculate_position_size",
            description="Calculate position size using 2% risk rule. Returns lot size, stop loss, take profit levels, risk/reward ratio, beta, and max drawdown.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "IDX stock symbol (e.g., 'BBCA')",
                    },
                    "capital": {
                        "type": "number",
                        "description": "Total portfolio capital in IDR (e.g., 10000000 for Rp 10 juta)",
                    },
                    "risk_pct": {
                        "type": "number",
                        "description": "Maximum risk per trade as percentage (default: 2.0)",
                        "default": 2.0,
                    },
                },
                "required": ["symbol", "capital"],
            },
        ),
        Tool(
            name="get_stock_list",
            description="Get list of stock symbols in an IDX index (LQ45, IDX30, KOMPAS100).",
            inputSchema={
                "type": "object",
                "properties": {
                    "index": {
                        "type": "string",
                        "description": "Index name: LQ45, IDX30, KOMPAS100, IDX80 (default: LQ45)",
                        "default": "LQ45",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="screen_stocks",
            description="Screen stocks from an index based on technical criteria: RSI range, minimum ADX, above EMA50. Returns filtered list sorted by trend strength.",
            inputSchema={
                "type": "object",
                "properties": {
                    "index": {
                        "type": "string",
                        "description": "Index to screen: LQ45, IDX30 (default: LQ45)",
                        "default": "LQ45",
                    },
                    "min_rsi": {
                        "type": "number",
                        "description": "Minimum RSI value (default: 30)",
                        "default": 30,
                    },
                    "max_rsi": {
                        "type": "number",
                        "description": "Maximum RSI value (default: 70)",
                        "default": 70,
                    },
                    "min_adx": {
                        "type": "number",
                        "description": "Minimum ADX for trend strength (default: 20)",
                        "default": 20,
                    },
                    "above_ema50": {
                        "type": "boolean",
                        "description": "Only include stocks above EMA50 (default: true)",
                        "default": True,
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results (default: 20)",
                        "default": 20,
                    },
                },
                "required": [],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    try:
        if name == "get_stock_price":
            result = await get_stock_price(
                symbol=arguments["symbol"],
                period=arguments.get("period", "1mo"),
            )
        elif name == "get_technical_indicators":
            result = await get_technical_indicators(symbol=arguments["symbol"])
        elif name == "get_adx_trend":
            result = await get_adx_trend(symbol=arguments["symbol"])
        elif name == "get_fundamental_data":
            result = await get_fundamental_data(symbol=arguments["symbol"])
        elif name == "get_money_flow":
            result = await get_money_flow(symbol=arguments["symbol"])
        elif name == "get_broker_summary":
            result = await get_broker_summary(
                symbol=arguments["symbol"],
                date=arguments.get("date"),
            )
        elif name == "get_news_sentiment":
            result = await get_news_sentiment(
                symbol=arguments["symbol"],
                limit=arguments.get("limit", 10),
            )
        elif name == "get_macro_data":
            result = await get_macro_data()
        elif name == "calculate_support_resistance":
            result = await calculate_support_resistance(symbol=arguments["symbol"])
        elif name == "calculate_position_size":
            result = await calculate_position_size(
                symbol=arguments["symbol"],
                capital=arguments["capital"],
                risk_pct=arguments.get("risk_pct", 2.0),
            )
        elif name == "get_stock_list":
            result = await get_stock_list(index=arguments.get("index", "LQ45"))
        elif name == "screen_stocks":
            result = await screen_stocks(
                index=arguments.get("index", "LQ45"),
                min_rsi=arguments.get("min_rsi", 30),
                max_rsi=arguments.get("max_rsi", 70),
                min_adx=arguments.get("min_adx", 20),
                above_ema50=arguments.get("above_ema50", True),
                limit=arguments.get("limit", 20),
            )
        else:
            result = json.dumps({"error": f"Unknown tool: {name}"})
        
        return [TextContent(type="text", text=result)]
    
    except Exception as e:
        error_result = json.dumps({"error": str(e), "tool": name, "arguments": arguments})
        return [TextContent(type="text", text=error_result)]


def main():
    """Run the MCP server."""
    async def run():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())
    
    asyncio.run(run())


if __name__ == "__main__":
    main()

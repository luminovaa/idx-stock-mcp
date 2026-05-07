"""IDX Stock MCP Server - SSE Transport for remote access.

This module runs the MCP server with SSE (Server-Sent Events) transport,
allowing remote clients to connect via HTTP. Suitable for VPS deployment
behind a reverse proxy (Nginx Proxy Manager).
"""

import os
import asyncio
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
import uvicorn

from .server import server, list_tools, call_tool

# Load environment variables
load_dotenv()

# Configuration
HOST = os.getenv("MCP_HOST", "0.0.0.0")
PORT = int(os.getenv("MCP_PORT", "8000"))
API_KEY = os.getenv("MCP_API_KEY", "")

# Create SSE transport
sse = SseServerTransport("/messages/")


async def handle_sse(request: Request):
    """Handle SSE connection from MCP client."""
    # API Key authentication (if configured)
    if API_KEY:
        auth_header = request.headers.get("Authorization", "")
        provided_key = request.query_params.get("api_key", "")
        
        if auth_header:
            # Bearer token format
            if not auth_header.startswith("Bearer ") or auth_header[7:] != API_KEY:
                return JSONResponse(
                    {"error": "Unauthorized - invalid API key"},
                    status_code=401,
                )
        elif provided_key:
            if provided_key != API_KEY:
                return JSONResponse(
                    {"error": "Unauthorized - invalid API key"},
                    status_code=401,
                )
        else:
            return JSONResponse(
                {"error": "Unauthorized - API key required"},
                status_code=401,
            )
    
    async with sse.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await server.run(
            streams[0], streams[1], server.create_initialization_options()
        )


async def handle_messages(request: Request):
    """Handle POST messages from MCP client."""
    # API Key authentication (if configured)
    if API_KEY:
        auth_header = request.headers.get("Authorization", "")
        if auth_header:
            if not auth_header.startswith("Bearer ") or auth_header[7:] != API_KEY:
                return JSONResponse(
                    {"error": "Unauthorized"},
                    status_code=401,
                )
        else:
            return JSONResponse(
                {"error": "Unauthorized - API key required"},
                status_code=401,
            )
    
    await sse.handle_post_message(request.scope, request.receive, request._send)


async def health_check(request: Request):
    """Health check endpoint."""
    tools = await list_tools()
    return JSONResponse({
        "status": "healthy",
        "server": "idx-stock-mcp",
        "version": "0.1.0",
        "transport": "sse",
        "tools_count": len(tools),
        "tools": [t.name for t in tools],
    })


async def info(request: Request):
    """Server info endpoint."""
    return JSONResponse({
        "name": "idx-stock-mcp",
        "version": "0.1.0",
        "description": "MCP Server for Indonesian Stock Market (IDX) analysis",
        "transport": "sse",
        "endpoints": {
            "sse": "/sse",
            "messages": "/messages/",
            "health": "/health",
        },
        "auth": "Bearer token" if API_KEY else "none",
    })


# Create Starlette app
app = Starlette(
    routes=[
        Route("/health", health_check, methods=["GET"]),
        Route("/", info, methods=["GET"]),
        Route("/sse", handle_sse, methods=["GET"]),
        Mount("/messages/", app=sse.handle_post_message),
    ],
    middleware=[
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        ),
    ],
)


def main():
    """Run the SSE MCP server."""
    print(f"Starting IDX Stock MCP Server (SSE transport)")
    print(f"Listening on {HOST}:{PORT}")
    print(f"Auth: {'API Key required' if API_KEY else 'No auth (set MCP_API_KEY to enable)'}")
    print(f"Endpoints:")
    print(f"  - SSE:      http://{HOST}:{PORT}/sse")
    print(f"  - Messages: http://{HOST}:{PORT}/messages/")
    print(f"  - Health:   http://{HOST}:{PORT}/health")
    print(f"  - Info:     http://{HOST}:{PORT}/")
    
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")


if __name__ == "__main__":
    main()

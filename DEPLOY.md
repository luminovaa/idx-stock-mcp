# Deployment Guide - IDX Stock MCP Server

## Prerequisites

- VPS dengan Docker & Docker Compose terinstall
- Nginx Proxy Manager sudah running
- Domain yang sudah di-pointing ke IP VPS

---

## Step 1: Upload Project ke VPS

```bash
# Option A: Git clone (jika sudah di-push ke repo)
cd /opt
git clone <your-repo-url> idx-stock-mcp
cd idx-stock-mcp

# Option B: SCP dari local
scp -r ./idx-stock-mcp user@your-vps-ip:/opt/idx-stock-mcp
```

---

## Step 2: Konfigurasi Environment

```bash
cd /opt/idx-stock-mcp

# Copy dan edit .env
cp .env.example .env
nano .env
```

Isi `.env`:

```env
# PENTING: Set API key untuk proteksi akses
MCP_API_KEY=your_secure_random_key_here

# Server config
MCP_HOST=0.0.0.0
MCP_PORT=8000

# Data source keys
ALPHAVANTAGE_API_KEY=your_key_here
IDX_API_KEY=
AJAIB_API_KEY=
```

> **Generate API key yang aman:**
> ```bash
> openssl rand -hex 32
> ```

---

## Step 3: Build & Run

```bash
cd /opt/idx-stock-mcp

# Build image
docker compose build

# Run (detached)
docker compose up -d

# Cek status
docker compose ps
docker compose logs -f
```

Verifikasi server berjalan:

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "server": "idx-stock-mcp",
  "version": "0.1.0",
  "transport": "sse",
  "tools_count": 12
}
```

---

## Step 4: Setup Nginx Proxy Manager

1. **Login ke Nginx Proxy Manager** (biasanya `http://your-vps-ip:81`)

2. **Add Proxy Host:**

   | Field | Value |
   |-------|-------|
   | Domain Names | `mcp.yourdomain.com` (ganti dengan domain Anda) |
   | Scheme | `http` |
   | Forward Hostname/IP | `idx-stock-mcp` (nama container) ATAU `host.docker.internal` ATAU IP internal VPS |
   | Forward Port | `8000` |
   | Websockets Support | **ON** (penting untuk SSE!) |
   | Block Common Exploits | ON |

3. **SSL Tab:**
   - SSL Certificate: Request a new SSL Certificate
   - Force SSL: ON
   - HTTP/2 Support: ON
   - Agree to Let's Encrypt ToS

4. **Advanced Tab** (tambahkan custom config untuk SSE):

   ```nginx
   # SSE specific settings
   proxy_buffering off;
   proxy_cache off;
   proxy_set_header Connection '';
   proxy_http_version 1.1;
   chunked_transfer_encoding off;
   
   # Timeout settings for long-lived SSE connections
   proxy_read_timeout 86400s;
   proxy_send_timeout 86400s;
   ```

5. **Save**

---

## Step 5: Networking (Jika NPM di Docker juga)

Jika Nginx Proxy Manager juga berjalan di Docker, pastikan keduanya di network yang sama:

### Option A: Gunakan network NPM yang sudah ada

Edit `docker-compose.yml`:

```yaml
services:
  idx-stock-mcp:
    # ... config lainnya ...
    networks:
      - npm-network  # Ganti dengan nama network NPM Anda

networks:
  npm-network:
    external: true
    name: nginx-proxy-manager_default  # Sesuaikan dengan nama network NPM
```

Cek nama network NPM:
```bash
docker network ls | grep nginx
```

### Option B: Gunakan host network

Edit `docker-compose.yml`:
```yaml
services:
  idx-stock-mcp:
    # ... config lainnya ...
    network_mode: host
```

Lalu di NPM, Forward Hostname = `127.0.0.1`, Port = `8000`

---

## Step 6: Verifikasi

```bash
# Test dari luar (ganti domain)
curl https://mcp.yourdomain.com/health

# Test info
curl https://mcp.yourdomain.com/

# Test SSE endpoint (akan hang karena SSE stream)
curl -N https://mcp.yourdomain.com/sse
```

---

## Step 7: Connect MCP Client

### Dari CL4ude Desktop / OpenCode (remote SSE):

```json
{
  "mcpServers": {
    "idx-stock": {
      "url": "https://mcp.yourdomain.com/sse",
      "headers": {
        "Authorization": "Bearer your_secure_random_key_here"
      }
    }
  }
}
```

### Dari kode Python:

```python
from mcp import ClientSession
from mcp.client.sse import sse_client

async def connect():
    async with sse_client(
        url="https://mcp.yourdomain.com/sse",
        headers={"Authorization": "Bearer your_api_key"}
    ) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print(f"Connected! {len(tools.tools)} tools available")
```

---

## Maintenance

```bash
# Lihat logs
docker compose logs -f

# Restart
docker compose restart

# Update (setelah pull code baru)
docker compose down
docker compose build --no-cache
docker compose up -d

# Cek resource usage
docker stats idx-stock-mcp
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| SSE connection drops | Pastikan `proxy_buffering off` di NPM Advanced config |
| 502 Bad Gateway | Cek apakah container running: `docker compose ps` |
| Auth error | Pastikan `MCP_API_KEY` di `.env` sama dengan yang di client config |
| Timeout | Tambah `proxy_read_timeout 86400s` di NPM |
| Container restart loop | Cek logs: `docker compose logs` |
| yfinance rate limit | Data di-cache otomatis (5 min - 24 jam tergantung tipe) |

---

## Security Checklist

- [ ] `MCP_API_KEY` sudah di-set (bukan kosong)
- [ ] SSL/HTTPS aktif via NPM
- [ ] Port 8000 TIDAK di-expose ke public (hanya via NPM)
- [ ] `.env` file tidak di-commit ke git
- [ ] Firewall VPS: hanya allow port 80, 443, 22

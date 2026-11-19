import asyncio
import base64
import json
import os
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

DATA_DIR = Path(os.getenv("DATA_DIR", "/data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "trading212.sqlite3"
API_KEY = os.getenv("T212_API_KEY", "").strip()
API_SECRET = os.getenv("T212_API_SECRET", "").strip()
ENVIRONMENT = os.getenv("T212_ENVIRONMENT", "live").strip().lower()
BASE_URL = "https://demo.trading212.com/api/v0" if ENVIRONMENT == "demo" else "https://live.trading212.com/api/v0"
SYNC_INTERVAL = max(300, int(os.getenv("SYNC_INTERVAL_SECONDS", "900")))

def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with db() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            captured_at TEXT NOT NULL,
            account_currency TEXT,
            cash REAL,
            positions_json TEXT NOT NULL,
            total_value REAL NOT NULL
        )""")

def credentials():
    if not API_KEY or not API_SECRET:
        raise HTTPException(503, "Trading-212-Zugangsdaten fehlen in der Server-Konfiguration (.env).")
    raw = f"{API_KEY}:{API_SECRET}".encode()
    return "Basic " + base64.b64encode(raw).decode()

async def fetch_api(path: str):
    async with httpx.AsyncClient(timeout=25) as client:
        response = await client.get(BASE_URL + path, headers={"Authorization": credentials()})
    if response.status_code == 401:
        raise HTTPException(401, "Trading 212 hat die Zugangsdaten abgelehnt. API Key und Secret prüfen.")
    if response.status_code == 403:
        raise HTTPException(403, "API-Berechtigung fehlt. Beim Trading-212-Schlüssel mindestens Portfolio und Kontodaten nur lesend aktivieren.")
    if response.status_code == 429:
        raise HTTPException(429, "Trading 212 API-Limit erreicht. Bitte später erneut synchronisieren.")
    if response.is_error:
        raise HTTPException(502, f"Trading 212 API Fehler ({response.status_code}).")
    return response.json()

async def sync_now():
    positions = await fetch_api("/equity/positions")
    summary = await fetch_api("/equity/account/summary")
    normalized = []
    for p in positions:
        instrument = p.get("instrument") or {}
        wallet = p.get("walletImpact") or {}
        normalized.append({
            "name": instrument.get("name") or instrument.get("ticker") or "Unbekannte Position",
            "ticker": instrument.get("ticker") or "",
            "isin": instrument.get("isin") or "",
            "currency": instrument.get("currency") or wallet.get("currency") or "EUR",
            "quantity": float(p.get("quantity") or 0),
            "averagePricePaid": float(p.get("averagePricePaid") or 0),
            "currentPrice": float(p.get("currentPrice") or 0),
            "currentValue": float(wallet.get("currentValue") or 0),
            "totalCost": float(wallet.get("totalCost") or 0),
            "unrealizedProfitLoss": float(wallet.get("unrealizedProfitLoss") or 0),
            "walletCurrency": wallet.get("currency") or summary.get("currency") or "EUR",
            "createdAt": p.get("createdAt")
        })
    cash = float(summary.get("cash") or 0)
    total = cash + sum(x["currentValue"] for x in normalized)
    captured = datetime.now(timezone.utc).isoformat()
    with db() as con:
        con.execute("INSERT INTO snapshots(captured_at,account_currency,cash,positions_json,total_value) VALUES(?,?,?,?,?)",
                    (captured, summary.get("currency") or "EUR", cash, json.dumps(normalized), total))
    return {"capturedAt": captured, "accountCurrency": summary.get("currency") or "EUR",
            "cash": cash, "totalValue": total, "positions": normalized}

def latest_snapshot():
    with db() as con:
        row = con.execute("SELECT * FROM snapshots ORDER BY id DESC LIMIT 1").fetchone()
    if not row:
        return None
    return {"capturedAt": row["captured_at"], "accountCurrency": row["account_currency"],
            "cash": row["cash"], "totalValue": row["total_value"],
            "positions": json.loads(row["positions_json"])}

async def poller():
    while True:
        await asyncio.sleep(SYNC_INTERVAL)
        try:
            await sync_now()
        except Exception as exc:
            print(f"Automatic Trading 212 sync failed: {exc}", flush=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    task = asyncio.create_task(poller())
    yield
    task.cancel()

app = FastAPI(title="WealthDashboard Trading 212 Bridge", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET", "POST", "OPTIONS"], allow_headers=["*"])

@app.get("/health")
async def health():
    return {"ok": True, "service": "wealthdashboard-trading212"}

@app.get("/api/status")
async def status():
    snap = latest_snapshot()
    return {"configured": bool(API_KEY and API_SECRET), "environment": ENVIRONMENT,
            "syncIntervalSeconds": SYNC_INTERVAL, "lastSync": snap["capturedAt"] if snap else None,
            "positionCount": len(snap["positions"]) if snap else 0,
            "accountCurrency": snap["accountCurrency"] if snap else None}

@app.get("/api/portfolio")
async def portfolio():
    snap = latest_snapshot()
    if not snap:
        raise HTTPException(404, "Noch keine Synchronisierung vorhanden.")
    return snap

@app.post("/api/sync")
async def sync():
    try:
        return await sync_now()
    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(504, "Zeitüberschreitung bei Trading 212.")
    except httpx.RequestError:
        raise HTTPException(502, "Trading 212 ist momentan nicht erreichbar.")

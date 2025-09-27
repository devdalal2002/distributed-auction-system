# gateway/main.py
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
import httpx
import asyncio
from sse_starlette.sse import EventSourceResponse
import os

BID_URL = os.getenv("BID_URL", "http://bid:8082")
app = FastAPI(title="Gateway", openapi_url="/openapi.json", docs_url="/docs")

AUCTION_BASE = "http://auction:8081"
BID_BASE = "http://bid:8082"

@app.get("/health")
def health():
    return "ok"

@app.post("/auctions", status_code=201)
async def create_auction(req: Request):
    payload = await req.json()
    required = ["title", "description", "start_price", "end_at_unix", "seller_id"]
    missing = [k for k in required if k not in payload]
    if missing:
        raise HTTPException(status_code=422, detail=f"missing fields: {', '.join(missing)}")
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(f"{AUCTION_BASE}/auctions", json=payload)
    if r.status_code >= 400:
        # bubble up backend error body if present
        try:
            detail = r.json()
        except Exception:
            detail = r.text
        raise HTTPException(status_code=r.status_code, detail=detail)
    return r.json()

@app.get("/auctions/{aid}")
async def get_auction(aid: str):
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(f"{AUCTION_BASE}/auctions/{aid}")
    if r.status_code >= 400:
        try:
            detail = r.json()
        except Exception:
            detail = r.text
        raise HTTPException(status_code=r.status_code, detail=detail)
    return r.json()

@app.post("/auctions/{aid}/bids", status_code=201)
async def place_bid(aid: str, req: Request):
    payload = await req.json()
    required = ["bidder_id", "amount"]
    missing = [k for k in required if k not in payload]
    if missing:
        raise HTTPException(status_code=422, detail=f"missing fields: {', '.join(missing)}")
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(f"{BID_BASE}/auctions/{aid}/bids", json=payload)
    if r.status_code >= 400:
        try:
            detail = r.json()
        except Exception:
            detail = r.text
        raise HTTPException(status_code=r.status_code, detail=detail)
    return r.json()


@app.get("/auctions/{aid}/events")
async def stream_events(aid: str):
    BID_SVC = "http://bid:8082"

    async def gen():
        seen = 0
        async with httpx.AsyncClient(timeout=None) as client:
            while True:
                try:
                    r = await client.get(f"{BID_SVC}/auctions/{aid}/bids")
                    if r.status_code == 200:
                        bids = r.json()
                        if len(bids) > seen:
                            for b in bids[seen:]:
                                yield {"event": "bid", "data": b}
                            seen = len(bids)
                except Exception:
                    pass
                await asyncio.sleep(1)

    return EventSourceResponse(gen())

@app.get("/auctions/{aid}/bids")
async def get_bids(aid: str):
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(f"{BID_URL}/auctions/{aid}/bids")
        resp.raise_for_status()
        return resp.json()
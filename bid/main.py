# bid/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List
import time

app = FastAPI(title="Bid Service", openapi_url="/openapi.json", docs_url="/docs")

class BidCreate(BaseModel):
    bidder_id: str
    amount: float = Field(gt=0)

class Bid(BaseModel):
    auction_id: str
    bidder_id: str
    amount: float
    placed_at_unix: int

# in-memory bids by auction id
BIDS: Dict[str, List[Bid]] = {}

@app.get("/health")
def health():
    return "ok"

@app.post("/auctions/{aid}/bids", status_code=201)
def place_bid(aid: str, payload: BidCreate):
    now = int(time.time())
    b = Bid(
        auction_id=aid,
        bidder_id=payload.bidder_id,
        amount=payload.amount,
        placed_at_unix=now,
    )
    BIDS.setdefault(aid, []).append(b)
    return b
@app.get("/auctions/{aid}/bids")
def list_bids(aid: str):
    return [b.dict() for b in BIDS.get(aid, [])]

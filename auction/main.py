# auction/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict
from uuid import uuid4
import time

app = FastAPI(title="Auction Service", openapi_url="/openapi.json", docs_url="/docs")

class AuctionCreate(BaseModel):
    title: str
    description: str
    start_price: float = Field(gt=0)
    end_at_unix: int = Field(gt=0)
    seller_id: str

class Auction(BaseModel):
    id: str
    title: str
    description: str
    start_price: float
    end_at_unix: int
    seller_id: str
    created_at_unix: int

DB: Dict[str, Auction] = {}

@app.get("/health")
def health():
    return {"service": "auction", "ok": True}

@app.post("/auctions", status_code=201)
def create_auction(payload: AuctionCreate):
    now = int(time.time())
    if payload.end_at_unix <= now:
        raise HTTPException(status_code=400, detail="end_at_unix must be in the future")
    aid = str(uuid4())
    a = Auction(
        id=aid,
        title=payload.title,
        description=payload.description,
        start_price=payload.start_price,
        end_at_unix=payload.end_at_unix,
        seller_id=payload.seller_id,
        created_at_unix=now,
    )
    DB[aid] = a
    return a

@app.get("/auctions/{aid}")
def get_auction(aid: str):
    a = DB.get(aid)
    if not a:
        raise HTTPException(status_code=404, detail="auction not found")
    return a

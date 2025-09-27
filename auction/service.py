import asyncio, uuid, grpc
from typing import Dict
import auction_pb2 as apb
import auction_pb2_grpc as agrpc

class AuctionStore:
    def __init__(self):
        self.auctions: Dict[str, apb.Auction] = {}
        self.lock = asyncio.Lock()

STORE = AuctionStore()

class AuctionService(agrpc.AuctionServiceServicer):
    async def CreateAuction(self, req, ctx):
        async with STORE.lock:
            aid = str(uuid.uuid4())
            a = apb.Auction(
                id=aid,
                title=req.title,
                description=req.description,
                start_price=req.start_price,
                status="open",
                end_at_unix=req.end_at_unix,
                highest_amount=req.start_price,
                highest_bidder_id="",
            )
            STORE.auctions[aid] = a
            return apb.CreateAuctionResponse(auction=a)

    async def GetAuction(self, req, ctx):
        a = STORE.auctions.get(req.id)
        if not a:
            await ctx.abort(grpc.StatusCode.NOT_FOUND, "auction not found")
        return apb.GetAuctionResponse(auction=a)

    async def CloseAuction(self, req, ctx):
        async with STORE.lock:
            a = STORE.auctions.get(req.id)
            if not a:
                await ctx.abort(grpc.StatusCode.NOT_FOUND, "auction not found")
            if a.status != "closed":
                a.status = "closed"
                STORE.auctions[a.id] = a
            return apb.CloseAuctionResponse(auction=a)

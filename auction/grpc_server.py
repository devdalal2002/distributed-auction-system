# auction/grpc_server.py
import os
import asyncio
import grpc

import auction_pb2 as apb
import auction_pb2_grpc as agrpc

# Reuse the in-memory store used by FastAPI routes
from service import STORE  # STORE: dict[id] -> dict with auction fields

class AuctionService(agrpc.AuctionServiceServicer):
    async def GetAuction(self, request, context):
        a = STORE.get(request.id)
        if not a:
            await context.abort(grpc.StatusCode.NOT_FOUND, "auction not found")
        return apb.GetAuctionResponse(
            auction=apb.Auction(
                id=a["id"],
                title=a["title"],
                description=a["description"],
                start_price=float(a["start_price"]),
                highest_amount=float(a["highest_amount"]),
                highest_bidder_id=a.get("highest_bidder_id", ""),
                status=a["status"],
                end_at_unix=int(a["end_at_unix"]),
                seller_id=a.get("seller_id", ""),
            )
        )

    async def CreateAuction(self, request, context):
        # Minimal, mirror what your HTTP handler does
        import time, uuid
        aid = str(uuid.uuid4())
        STORE[aid] = {
            "id": aid,
            "title": request.title,
            "description": request.description,
            "start_price": float(request.start_price),
            "highest_amount": float(request.start_price),
            "highest_bidder_id": "",
            "status": "open" if int(request.end_at_unix) > int(time.time()) else "closed",
            "end_at_unix": int(request.end_at_unix),
            "seller_id": request.seller_id or "",
        }
        return apb.CreateAuctionResponse(id=aid)

    async def ListAuctions(self, request, context):
        items = []
        for a in STORE.values():
            items.append(
                apb.Auction(
                    id=a["id"],
                    title=a["title"],
                    description=a["description"],
                    start_price=float(a["start_price"]),
                    highest_amount=float(a["highest_amount"]),
                    highest_bidder_id=a.get("highest_bidder_id", ""),
                    status=a["status"],
                    end_at_unix=int(a["end_at_unix"]),
                    seller_id=a.get("seller_id", ""),
                )
            )
        return apb.ListAuctionsResponse(auctions=items)

async def serve_grpc():
    addr = os.getenv("AUCTION_GRPC_ADDR", "0.0.0.0:50051")
    server = grpc.aio.server()
    agrpc.add_AuctionServiceServicer_to_server(AuctionService(), server)
    server.add_insecure_port(addr)
    await server.start()
    # Do not await termination here, we run it as a background task
    # The task will keep running for the lifetime of the process

import asyncio, time, os, grpc, nats
import bid_pb2 as bpb
import bid_pb2_grpc as bgrpc
import auction_pb2 as apb
import auction_pb2_grpc as agrpc

NATS_URL = os.getenv("NATS_URL", "nats://nats:4222")
AUCTION_ADDR = os.getenv("AUCTION_ADDR", "auction:50051")

# Local in-memory highest bid cache per auction
HIGHEST = {}  # auction_id -> (amount, bidder_id)
IDEM = set()
LOCK = asyncio.Lock()

async def get_auction(auction_id: str) -> apb.Auction | None:
    ch = grpc.aio.insecure_channel(AUCTION_ADDR)
    stub = agrpc.AuctionServiceStub(ch)
    try:
        resp = await stub.GetAuction(apb.GetAuctionRequest(id=auction_id))
        return resp.auction
    except grpc.aio.AioRpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            return None
        raise

class BidService(bgrpc.BidServiceServicer):
    async def PlaceBid(self, req: bpb.PlaceBidRequest, ctx):
        key = f"{req.auction_id}:{req.idempotency_key}"
        async with LOCK:
            if key in IDEM:
                amt, bidder = HIGHEST.get(req.auction_id, (0.0, ""))
                return bpb.PlaceBidResponse(accepted=False, highest_amount=amt, highest_bidder_id=bidder)

        a = await get_auction(req.auction_id)
        if not a:
            await ctx.abort(grpc.StatusCode.NOT_FOUND, "auction not found")

        now = int(time.time())
        if a.status != "open" or now >= a.end_at_unix:
            amt, bidder = HIGHEST.get(req.auction_id, (float(a.highest_amount), a.highest_bidder_id))
            return bpb.PlaceBidResponse(accepted=False, highest_amount=amt, highest_bidder_id=bidder)

        cached_amt, cached_bidder = HIGHEST.get(req.auction_id, (float(a.highest_amount), a.highest_bidder_id))
        base_amt = max(float(a.highest_amount), float(cached_amt))

        if req.amount <= base_amt:
            return bpb.PlaceBidResponse(accepted=False, highest_amount=base_amt, highest_bidder_id=cached_bidder or a.highest_bidder_id)

        async with LOCK:
            IDEM.add(key)
            HIGHEST[req.auction_id] = (float(req.amount), req.bidder_id)

        try:
            nc = await nats.connect(servers=[NATS_URL])
            subj = f"auctions.{req.auction_id}.events"
            payload = f"bid:{req.amount}:{req.bidder_id}".encode()
            await nc.publish(subj, payload)
            await nc.drain()
        except Exception:
            pass

        return bpb.PlaceBidResponse(accepted=True, highest_amount=float(req.amount), highest_bidder_id=req.bidder_id)

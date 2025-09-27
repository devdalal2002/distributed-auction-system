import asyncio, os, uvicorn, grpc
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
import user_pb2_grpc as ugrpc
from service import UserService

APP_ENV = os.getenv("APP_ENV", "dev")
app = FastAPI(title="user", version="0.2.0")

@app.get("/health", response_class=PlainTextResponse)
async def health():
    return "ok"

async def serve_grpc():
    server = grpc.aio.server()
    ugrpc.add_UserServiceServicer_to_server(UserService(), server)
    server.add_insecure_port("0.0.0.0:50053")
    await server.start()
    await server.wait_for_termination()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(serve_grpc())
    uvicorn.run("main:app", host="0.0.0.0", port=8083, reload=False)

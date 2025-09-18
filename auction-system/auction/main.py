import os
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse


APP_ENV = os.getenv("APP_ENV", "dev")
app = FastAPI(title="auction", version="0.1.0")


@app.get("/health", response_class=PlainTextResponse)
async def health():
    return "ok"


@app.get("/")
async def root():
    return {"service": "auction", "env": APP_ENV}
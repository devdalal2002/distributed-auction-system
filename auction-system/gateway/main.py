import os
import asyncio
from typing import Optional
from fastapi import FastAPI, Response
from fastapi.responses import PlainTextResponse


APP_ENV = os.getenv("APP_ENV", "dev")


app = FastAPI(title="gateway", version="0.1.0")


@app.get("/health", response_class=PlainTextResponse)
async def health():
    return "ok"


# Placeholders for day-1. We will route to services in Day 2.
@app.get("/")
async def root():
    return {"service": "gateway", "env": APP_ENV}
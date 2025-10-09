"""Lightweight benchmarking helper for the auction gateway."""

import json
import os
import sys
import time
from statistics import mean
from urllib import error, request


def _handle_http_error(exc: error.HTTPError):
    body = exc.read().decode("utf-8", "ignore")
    try:
        parsed = json.loads(body) if body else {}
    except json.JSONDecodeError:
        parsed = {"error": body.strip()}
    message = parsed.get("error") or parsed.get("message") or exc.reason
    raise RuntimeError(f"{exc.code} {exc.reason} for {exc.url}: {message}") from exc


def call(url, payload):
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        _handle_http_error(exc)
    except error.URLError as exc:
        raise RuntimeError(f"Failed to reach {url}: {exc.reason}") from exc


def get(url):
    try:
        with request.urlopen(url) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        _handle_http_error(exc)
    except error.URLError as exc:
        raise RuntimeError(f"Failed to reach {url}: {exc.reason}") from exc


def _normalize_base_url(raw: str) -> str:
    candidate = raw.strip()
    if not candidate:
        raise RuntimeError("Base URL cannot be empty")
    # Allow passing an environment variable name such as BASE_URL
    env_value = os.getenv(candidate)
    if env_value:
        candidate = env_value
    if not candidate.lower().startswith("http"):
        if candidate.upper() == candidate and not env_value:
            raise RuntimeError(
                f"Provide a concrete base URL (e.g. http://localhost:8080) instead of the placeholder '{raw}'."
            )
        candidate = f"http://{candidate}"
    return candidate.rstrip("/")


def run(base_url: str, iterations: int = 5):
    base = _normalize_base_url(base_url)
    latencies = []
    for idx in range(iterations):
        start = time.time()
        try:
            create = call(f"{base}/api/auctions", {
                "name": f"Load Test Item {idx}",
                "description": "Benchmark item",
                "starting_bid": 10 + idx,
                "duration_seconds": 120,
            })
            auction_id = create.get("auction", {}).get("id")
            if not auction_id:
                raise RuntimeError("Auction creation did not return an id")
            call(f"{base}/api/auctions/{auction_id}/bid", {"bidder": "bot", "amount": 20 + idx})
            call(f"{base}/api/auctions/{auction_id}/close", {})
            get(f"{base}/api/history")
            latencies.append(time.time() - start)
        except RuntimeError as exc:
            print(f"Iteration {idx + 1} failed: {exc}")
            break
    if not latencies:
        print("No successful iterations were recorded.")
        return
    throughput = len(latencies) / sum(latencies)
    print(f"Latency avg: {mean(latencies):.4f}s")
    print(f"Throughput: {throughput:.2f} ops/s")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python benchmark.py <base_url>")
        sys.exit(1)
    run(sys.argv[1])


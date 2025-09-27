# Distributed Auction System, Day 1


## Prereqs
- Docker and Docker Compose


## Run
```bash
cd deploy
cp .env.example .env
# Optionally edit ports or creds
docker compose up --build

Phase 2
Prereqs

Docker and Docker Compose

PowerShell or curl for testing endpoints

Setup & Run
cd deploy
cp .env.example .env
# Optionally edit ports or credentials
docker compose up --build

Health Checks

Verify that all core services are running:

curl http://localhost:8080/health   # gateway
curl http://localhost:8081/health   # auction
curl http://localhost:8082/health   # bid
curl http://localhost:8083/health   # user

Phase 2 Features
1. Create Auction
$now = [int][DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
$end = $now + 300
$body = @{
  title       = "Laptop"
  description = "MBP"
  start_price = 500
  end_at_unix = $end
  seller_id   = "u1"
} | ConvertTo-Json

$auc = Invoke-RestMethod -Method Post -Uri "http://localhost:8080/auctions" -ContentType "application/json" -Body $body
$auc

2. Read Auction
Invoke-RestMethod "http://localhost:8080/auctions/$($auc.id)"

3. Place Bids
$bidBody = @{ bidder_id="u2"; amount=560 } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "http://localhost:8080/auctions/$($auc.id)/bids" -ContentType "application/json" -Body $bidBody

4. List Bids
Invoke-RestMethod "http://localhost:8080/auctions/$($auc.id)/bids"

5. Direct Bid Service (optional)
Invoke-RestMethod "http://localhost:8082/auctions/$($auc.id)/bids"
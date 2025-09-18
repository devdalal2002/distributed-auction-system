import os
import time


APP_ENV = os.getenv("APP_ENV", "dev")


if __name__ == "__main__":
    print({"service": "worker", "env": APP_ENV, "status": "starting"}, flush=True)
    # Day 1, idle loop. Day 2 will scan and close auctions.
    while True:
        print({"service": "worker", "heartbeat": True}, flush=True)
        time.sleep(10)
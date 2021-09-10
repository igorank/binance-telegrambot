import time
import requests
import pandas as pd

while True:
    r = requests.get("https://api.binance.com/api/v3/depth", params=dict(symbol="ETHUSDT"))
    results = r.json()
    r2 = requests.get("https://api.binance.com/api/v3/ticker/24hr", params=dict(symbol="ETHUSDT"))
    results2 = r2.json()

    frames = {side: pd.DataFrame(data=results[side], columns=["price", "quantity"], dtype=float) for side in ["bids", "asks"]}

    frames_list = [frames[side].assign(side=side) for side in frames]
    data = pd.concat(frames_list, axis="index", 
                         ignore_index=True, sort=True)

    price_summary = data.groupby("side").price.describe()
    price_summary.to_markdown()
    print(frames["bids"])
    print(results2["quoteVolume"])
    time.sleep(1)

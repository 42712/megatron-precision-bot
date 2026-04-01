import requests
import random
from config import CMC_API
from indicators import ema, rsi

headers = {"X-CMC_PRO_API_KEY": CMC_API}

def analisar():
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
    params = {"limit": 30, "convert": "USD"}

    data = requests.get(url, headers=headers, params=params).json()["data"]

    sinais = []

    for coin in data:
        price = coin["quote"]["USD"]["price"]
        volume = coin["quote"]["USD"]["volume_24h"]
        change = coin["quote"]["USD"]["percent_change_24h"]

        # simulação leve de candles
        precos = [price * (1 + random.uniform(-0.02, 0.02)) for _ in range(30)]

        ema9 = ema(precos, 9)
        ema21 = ema(precos, 21)
        rsi_val = rsi(precos)

        if (
            ema9 > ema21
            and 50 < rsi_val < 65
            and volume > 50000000
            and 2 < change < 8
        ):
            sinais.append(coin["symbol"] + "USDT")

    return sinais

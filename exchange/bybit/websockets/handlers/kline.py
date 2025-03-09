import numpy as np
from typing import List
from indicators.bbw import bbw
from sharedstate import SharedState
from pybit.unified_trading import HTTP

class BybitKlineHandler:
    def __init__(self, ss: SharedState) -> None:
        self.ss = ss
        self.session = HTTP(api_key=self.ss.api_key, api_secret=self.ss.api_secret)

    def _update_volatility_(self) -> None:
        self.ss.volatility_value = bbw(
            klines=self.ss.bybit_klines._unwrap(), 
            length=self.ss.bb_length, 
            multiplier=self.ss.bb_std
        )

        self.ss.volatility_value += self.ss.volatility_offset

    def initialize(self, data: List) -> None:
        """
        Initialize the klines array and update volatility value
        """
        self.ss.simple_bybit_klines = data
        for candle in data:
            arr = np.array(candle, dtype=np.float64)
            self.ss.bybit_klines.append(arr)
        self._update_volatility_()

    def simple(self, recv: List) -> None:

        klines = self.session.get_kline(
            category="linear", 
            symbol=self.ss.bybit_symbol, 
            interval=str(self.ss.interval),
            limit=str(301)
        )["result"]["list"]
        klines.reverse()
        self.ss.simple_bybit_klines =  klines

    def process(self, recv: List) -> None:
        """
        Used to attain close values and calculate volatility
        # """
        # print(f"recv: {recv}")
        # self.simple()
        for candle in recv["data"]:
            new = np.array([
                float(candle["start"]),
                float(candle["open"]),
                float(candle["high"]),
                float(candle["low"]),
                float(candle["close"]),
                float(candle["volume"]),
                float(candle["turnover"]),
            ])

            # If previous time same, then overwrite, else append
            if self.ss.bybit_klines[-1][0] != new[0]:
                self.ss.bybit_klines.append(new)
            else:
                self.ss.bybit_klines.pop()
                self.ss.bybit_klines.append(new)

            self._update_volatility_()
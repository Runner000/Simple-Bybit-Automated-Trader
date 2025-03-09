import numpy as np
from typing import List, Tuple
from strategy.features.generate import Features
from sharedstate import SharedState
import pandas as pd
from strategy.indicators import Indicators


class Trending:
    """
    Implements trend based strategy that involves using 
    spread adjustment for volatility, and order size calculations.

    Attributes
    ----------
    ss : SharedState
        Shared application state containing configuration and market data.
    features : Features
        A class instance for calculating market features like skew.
    tick_size : float
        The minimum price movement of an asset.
    lot_size : float
        The minimum quantity movement of an asset.
    spread : float
        The adjusted spread based on market volatility.

    Methods
    -------
    _skew_() -> Tuple[float, float]:
        Calculates bid and ask skew based on inventory and market conditions.
    _adjusted_spread_() -> float:
        Adjusts the base spread according to market volatility.
    _prices_(bid_skew: float, ask_skew: float) -> Tuple[np.ndarray, np.ndarray]:
        Generates bid and ask prices based on market conditions and skew.
    _sizes_(bid_skew: float, ask_skew: float) -> Tuple[np.ndarray, np.ndarray]:
        Calculates the sizes for bid and ask orders based on skew.
    generate_quotes() -> List[Tuple[str, float, float]]:
        Generates a list of quotes to be submitted to the exchange.
    """

    def __init__(self, ss: SharedState) -> None:
        self.ss = ss
        self.features = Features(self.ss)
        self.func = Indicators
        self.vwma_len, self.fast_ema_len, self.slow_ema_len = self.ss.vwma_len, self.ss.fast_ema_len, self.ss.slow_ema_len
        self.median_pcnt, self.atr_period = self.ss.median_pcnt, self.ss.atr_period
        self.stddev, self.bband_period, self.candle_lookback = self.ss.stddev, self.ss.bband_period, self.ss.candle_lookback


    def _candle_trend_(self) -> List[Tuple[str, str]]: #maybe needs to be a Tuple as well???
        """
        Calculates the trend direction for the last two closed candles.

        Steps:
        1. Grabs last 300 klines from exchange feed.
        2. Calculates values and variables via indicators.
        3. Finally uses these values to establish the trend directions of each candle.
        
        Returns
        -------
        String
            The trend direction of the last and 2nd to last candle.
        """

        df = pd.DataFrame(self.ss.simple_bybit_klines, columns=["start", "open", "high", "low", "close", "volume", "turnover"])
        df = df.apply(pd.to_numeric).iloc[:-1]
        self.slowema = self.func.EMA(df.close, self.slow_ema_len)
        self.fastema = self.func.EMA(df.close, self.fast_ema_len)
        self.ref_ema = self.func.VWMA(df.close, df.volume, self.vwma_len)
        self.bbp = self.func.BolBands(df, self.bband_period, self.stddev, bbp=True)
        self.trend = self.func.trend(self.ref_ema, self.candle_lookback, pcnt=self.median_pcnt)
        self.emaCheck = self.func.emaCheck(self.fastema, self.slowema)
        atr = self.func.ATR(df.high, df.low, df.close, self.atr_period)
        self.ss.atr = atr[-1]

        # Last candles values
        emaStatus0 = self.emaCheck[-2]
        refEMA0 = self.ref_ema[-2]
        bbP0 = self.bbp.iloc[-2]
        direction0 = self.trend[-2] 

        # Current candles values
        emaStatus = self.emaCheck[-1]
        refEMA = self.ref_ema[-1]
        bbP = self.bbp.iloc[-1]
        direction = self.trend[-1] 

        trend0 = self._check_(emaStatus0, df.close.iloc[-2], refEMA0, direction0, bbP0)
        self.trend1 = self._check_(emaStatus, df.close.iloc[-1], refEMA, direction, bbP)
        return trend0, self.trend1

    def _trade_(self, trend0, trend1) -> None:
        """
        Compares the last two closed candles trend directions and establishes if a trade signal has occured.
        
        """
        self.long, self.short, self.closeLong, self.closeShort = False, False, False, False

        if trend0 != trend1:
            if trend1 == "bull" and (trend0 == "bear" or trend0 == "bearish"):
                self.long = True
            if trend1 == "bullish" and (trend0 == "bear" or trend0 == "bearish"):
                self.long = True
                self.closeShort = True
            if trend1 == "bear" and (trend0 == "bull" or trend0 == "bullish"):
                self.short = True
            if trend1 == "bearish" and (trend0 == "bull" or trend0 == "bullish"):
                self.short = True
                self.closeLong = True

    def _check_(self, emaStatus, Close, refEMA, direction, bbP) -> str:
        if emaStatus and Close > refEMA:
            if direction == 1 and bbP > 0.51:
                return "bull"
            else: return "bullish"
        else:
            if direction == 0 and bbP < 0.49:
                return "bear"
            else: return "bearish"

    def generate_signal(self, debug=False) -> List[Tuple[str, str, str, str]]:
        """
        Generates whether or not the current price action has developed a trade signal. Either entering or exiting a position (long/short)

        Steps:
        1. Finds trend of past two candles.
        3. Calculates whether or not a trade signal has developed.
        4. Returns variables regarding entering or exiting a position.

        Returns
        -------
        List[Tuple[str, str, str, str]]
            Variables that correspond to binary long or short signals. Or closing a long or short.
        """

        trend0, trend1 = self._candle_trend_()
        self._trade_(trend0, trend1)

        if debug:
            print("-----------------------------")
            # print(f"Long: {self.long} | Short {self.short} | CloseLong {self.closeLong} | CloseShort {self.closeShort}")
            print(f"Candle Trend: {self.trend1}")
            # print(f"Inventory: {self.ss.inventory_delta}")

        return self.long, self.short, self.closeLong, self.closeShort
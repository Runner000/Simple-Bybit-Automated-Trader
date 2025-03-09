import pandas_ta as ta, numpy as np, tulipy as ti, statistics, pandas as pd
# from scipy.signal import savgol_filter, find_peaks

## ---------------- Indicators ---------------- ##
class Indicators:

    def EMA(close, window):
        series = ta.ema(close, window, fillna=0)
        return series

    def ATR(high, low, close, period):
        series = ta.atr(high, low, close, period)
        pad = np.pad(series, ((len(close)-len(series)), 0), 'constant')
        return pad

    def BolBands(df, period, stddev, **kwargs):
        bw = kwargs.get('bw', False)
        bbp = kwargs.get('bbp', False)
        bands = ta.bbands(df.close, period, stddev, fillna=df.close.iloc[0])
        if bbp:
            return bands[f'BBP_{period}_{stddev}']
        elif bw:
            bands = bands.drop(columns=[f'BBL_{period}_{stddev}', f'BBM_{period}_{stddev}', f'BBU_{period}_{stddev}'])
            return bands
        else:
            bands = bands.drop(columns=[f'BBB_{period}_{stddev}', f'BBP_{period}_{stddev}'])
            return bands
        
    # Returns a series of candle directions based on Trend Strat slope based trend
    def trend(series, lookback, **kwargs):
        series = pd.Series(series)
        pcnt = kwargs.get('pcnt', 20)/100
        medianRange = kwargs.get('medianRange', 200)
        slopes, trend = [], [2,2]

        for i in range(lookback, len(series),1):
            slopes.append((series[i]-series[i-lookback])*10)
        # median = ta.median(slopes[-200:], 199)[-1]
        median = statistics.median(slopes[-medianRange:])
        for i in range(len(slopes)):
            if slopes[i] < pcnt*median and slopes[i] > -pcnt*median:
                trend.append(2)
            elif slopes[i] > 0:
                trend.append(1)
            elif slopes[i] < 0:
                trend.append(0)
            else: trend.append(2)
        return trend

    def VWMA(close, volume, length):
        series = ta.vwma(close, volume, length)
        pad = np.pad(series, ((len(close)-len(series)), 0), 'constant')
        return pad

    def emaCheck(fast, slow):
        checks = []
        for i in range(len(fast)):
            if fast[i] > slow[i]:
                checks.append(True)
            else: checks.append(False)
        return checks

    # def VWAP(df):
    #     series = ta.vwap(df.High, df.Low, df.Close, df.Volume)
    #     return series

    # def a_or_b(ema, price):
    #     if ema <= price:
    #         above = True
    #     else: above = False
    #     return above

    # def crossed(fastma, slowma):
    #     # Fast MA crossing over Slow MA
    #     if ti.crossover(fastma, slowma):
    #         cross = 'over'
    #     # Fast MA crossing under Slow MA
    #     elif ti.crossover(slowma, fastma):
    #         cross = 'under'
    #     else: cross = False
    #     return cross

    # def rsi_divs(close, fast_p, slow_p):
    #     fast = RSI(close, fast_p)
    #     slow = RSI(close, slow_p)
    #     divs = fast-slow
    #     return divs

    # def RSI(close, window):
    #     series = ti.rsi(close,window)
    #     pad = np.pad(series, ((len(close)-len(series)), 0), 'constant')
    #     return pad

    # def Supertrend(df, length, multip):
    #     supert = ta.supertrend(df.High, df.Low, df.Close, length, multip, fillna=0)
    #     return supert.drop(columns=[f'SUPERTl_{length}_{multip}', f'SUPERTs_{length}_{multip}'])

    # def MS(df):
    #     atr = ATR(df.High.to_numpy(), df.Low.to_numpy(), df.Close.to_numpy(), 12)
    #     # Smooths the Close into a line chart, finds the peaks and troughs of the line
    #     smooth = savgol_filter(df.Close, 20, 8)
    #     peaks_idx = find_peaks(smooth, distance=5, width=3, prominence=atr)[0]
    #     troughs_idx = find_peaks(-1*smooth, distance=5, width=3, prominence=atr)[0]

    #     up_run_len = 0
    #     up_run=True
    #     down_run_len = 0
    #     down_run=True
    #     #With the indexes of each peak and trough, we determine if each one is greater than or less than. This determines the nature of the trend (up/down)
    #     while up_run:
    #         if 2 + up_run_len > len(peaks_idx) or 2 + up_run_len > len(troughs_idx):
    #             break
    #         if smooth[peaks_idx[-1-up_run_len]] > smooth[peaks_idx[-2-up_run_len]] and smooth[troughs_idx[-1-up_run_len]] > smooth[troughs_idx[-2-up_run_len]]:
    #             up_run_len+=1
    #             int(up_run_len)
    #         else: up_run = False
    #     while down_run:
    #         if 2 + down_run_len > len(peaks_idx) or 2 + down_run_len > len(troughs_idx):
    #             break
    #         if smooth[peaks_idx[-1-down_run_len]] < smooth[peaks_idx[-2-down_run_len]] and smooth[troughs_idx[-1-down_run_len]] < smooth[troughs_idx[-2-down_run_len]]:
    #             down_run_len+=1
    #             int(down_run_len)
    #         else: down_run = False

    #     if up_run_len > 0:
    #         trend = 'up'       # Up
    #     elif down_run_len > 0:
    #         trend = 'down'       # Down
    #     else: trend = False     # Chop
    #     return trend

    # Find the local High/Low with 'n' bars
    # def local_HL(data, bars, H_L):
    #     if H_L: # Find local High
    #         for i in range(2,bars,1):
    #             if data[-i] > data[-1]:
    #                 local = data[-i]
    #     else:
    #         for i in range(2,bars,1):
    #             if data[-i] < data[-1]:
    #                 local = data[-i]
    #     return local

    # Just returns the last candles slope
    # def slope(series, lookback, **kwargs):
    #     pcnt = kwargs.get('pcnt', 20)/100
    #     medianRange = kwargs.get('medianRange', 200)
    #     slopes = []
        
    #     for i in range(lookback, len(series),1):
    #         slopes.append((series[i]-series[i-lookback])*10)
    #     # median = ta.median(slopes[-200:], 199)[-1]
    #     median = statistics.median(slopes[-medianRange:])
    #     if slopes[-1] < pcnt*median and slopes[-1] > -pcnt*median:
    #         trend = 2
    #     elif slopes[-1] > 0:
    #         trend = 1
    #     elif slopes[-1] < 0:
    #         trend = 0
    #     return trend

from typing import Dict, List, Union
from strategy.inventory import Inventory
from sharedstate import SharedState
import datetime


class BybitPositionHandler:
    def __init__(self, ss: SharedState) -> None:
        self.ss = ss
        self.inventory = Inventory(self.ss)
    
    def sync(self, recv: Dict) -> None:
        if recv is not None:
            self.process(recv["result"]["list"][0])

    def convertTime(self, created):
        dt = datetime.datetime.fromtimestamp(created/1000)
        minutes = dt.minute //15*15
        return dt.replace(minute=minutes, second=0, microsecond=0)
        return

    def process(self, data: Union[Dict, List]) -> None:
        # print(data)
        if isinstance(data, list):
            data = data[0]

        if data["side"]:
            self.ss.side = data["side"]
            try:
                symbol = str(data["symbol"])
                value = float(data["positionValue"])
                leverage = float(data["leverage"])
                entry = float(data["avgPrice"])
                if sl := data["stopLoss"]:
                    sl = float(sl)
                else: sl = 0
                if tp := data["takeProfit"]:
                    tp = float(tp)
                else: tp = 0
                upnl = float(data["unrealisedPnl"])
                created_ = int(data["updatedTime"])
                created = self.convertTime(created_)
                self.ss.tradeStart = created

                pcnt = round((upnl/abs(value))*100,4)
                # if sl and tp:
                #     sl, tp = int(sl), int(tp)
                # else: sl, tp = 0, 0
                # print({symbol: [entry, sl, tp, value, upnl, pcnt]})
                self.ss.positionInfo = {symbol: [entry, sl, tp, value, upnl, pcnt, created]}#created.strftime("%D %H:%M")]}
                self.inventory.position_delta(data["side"], value, leverage)
            except Exception as e: 
                print(e)
        else: 
            self.ss.positionInfo = None
            self.ss.side = None
            self.ss.tradeStart = None
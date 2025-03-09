from typing import Dict
from sharedstate import SharedState


class BybitTickerHandler:
    def __init__(self, ss: SharedState) -> None:
        self.ss = ss

    def process(self, recv: Dict) -> None:
        data = recv["data"]
        if "markPrice" in data:
            self.ss.bybit_mark_price = float(data["markPrice"])
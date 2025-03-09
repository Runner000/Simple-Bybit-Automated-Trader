import asyncio, numpy as np
from typing import List, Tuple, Coroutine, Union
from utils.jit_funcs import nbabs
from exchange.bybit.post.order import Order
from strategy.inventory import Inventory
from sharedstate import SharedState
from datetime import datetime, timedelta
   
class sOMS:
    """
    Manages the order lifecycle for Bybit, including segregating, amending, and placing orders based on strategy needs.

    Attributes
    ----------
    ss : SharedState
        Shared state object to access and update application-wide data.

    Methods
    -------
    segregate_current_orders(orders: Dict) -> Tuple[List, List]:
        Segregates and sorts current orders into buys and sells.
    segregate_new_orders(orders: List) -> Tuple[List, List]:
        Segregates and sorts new orders into buys and sells.
    amend_orders(current_orders: List, new_orders: List) -> Coroutine:
        Amends existing orders based on new order instructions.
    run(new_orders: List) -> Coroutine:
        Orchestrates the order management process, including order segregation, synchronization, and amendment.
    """
    def __init__(self, ss: SharedState) -> None:
        self.ss = ss
        self.tradeStart = self.round_to_nearest_15min(datetime.now())

    def current_orders(self) -> Tuple[List, List]:
        buys, sells = [], []
        for orderId, details in self.ss.current_orders.items():
            if details["side"] == "Buy":
                buys.append([orderId, details["side"], details["price"], details["qty"], details["leavesValue"]])
            else:
                sells.append([orderId, details["side"], details["price"], details["qty"], details["leavesValue"]])
        buys.sort(key=lambda x: x[2], reverse=True)
        sells.sort(key=lambda x: x[2])
        return buys, sells

    def round_to_nearest_15min(self, dt) -> datetime:
        minutes = dt.minute //15*15
        return dt.replace(minute=minutes, second=0, microsecond=0)

    def pnl_and_duration_check(self, time):
        trade_dur, pnlClose = True, False
        now = self.round_to_nearest_15min(datetime.now())
        interval = now - time
        trade_duration = int(interval.total_seconds()/60/15)
        print(f"Trade Duration: {trade_duration}")
        if trade_duration >= self.ss.trade_dur_min:
            trade_dur = True
        if trade_duration >= self.ss.pnlCandle and self.ss.positionInfo[self.ss.bybit_symbol][5] <= self.ss.pnlPcnt:
            pnlClose = True
        return trade_dur, pnlClose

    async def check_orders(self) -> None:
        b_orders, s_orders = self.current_orders()

        bid_price, ask_price = self.ss.bybit_bba[:, 0]
        print("Checking orders and positions...")

        # Order was cancelled somehow, reset param to re-initiate trade
        if self.ss.side == None and not(b_orders) and not(s_orders):
            self.ss.fillMe = None
            print("Resetting variables")
            return

        # Order was cancelled somehow, reset param to re-initiate trade
        elif self.ss.side != None and self.ss.fillMe != None and not(b_orders) and not(s_orders):
            self.ss.fillMe = None
            print("Resetting variables")
            return

        #Long was filled
        if self.ss.side == "Buy" and self.ss.fillMe == "Buy" and not(b_orders):
            self.ss.fillMe = None
            print("Long filled")
            return

        # Short was filled
        elif self.ss.side == "Sell" and self.ss.fillMe == "Sell" and not(s_orders):
            self.ss.fillMe = None
            print("Short filled")
            return

        # Buy orders present, amend to bid if bid price is not at bb
        elif b_orders and self.ss.side != "Buy":
            if b_orders[0][2] < bid_price:
                await Order(self.ss).amend([b_orders[0][0], bid_price, 0], simple=True)
            print(f"Buy Orders: {b_orders}")
            print("Checked Long orders, bid is at top of book")
            return
        
        # Sell orders present, amend to ask if ask price is not at ba
        elif s_orders and self.ss.side != "Sell":
            if s_orders[0][2] > ask_price:
                await Order(self.ss).amend([s_orders[0][0], ask_price, 0], simple=True)
            print(f"Sell Orders: {s_orders}")
            print("Checked Sell orders, ask is at top of book")
            return

    async def run(self, long: bool, short: bool, closeLong: bool, closeShort: bool) -> None:
        """
        Orchestrates the order management process by comparing new orders against current ones,
        determining necessary adjustments, and executing them.

        Steps:
        1. No current orders
            -> Cancel all (for safety), then send new orders

        2. All are bids/asks and have changed (extreme scenario)
            -> Cancel missing and send new in singles

        3. Current and new sides dont match (switching from/to extreme scenario)
            -> Cancel all and send all new

        4. 4 close to BBA orders have changed
            -> Amend changed orders to new price/qty

        5. Outer orders have changed more than buffer
            -> Cancel changed and send changed as batch

        Parameters
        ----------
        new_orders : List[Tuple[str, float, float]]
            A list of new orders, where each order is represented as a tuple of side, price, and quantity.
        """
        # Checks to see if the current position is greater than 3 candles old (prevents flip flopping directions so much)

        bid_price, ask_price = self.ss.bybit_bba[:, 0]
        b_orders, s_orders = self.current_orders()
        # print(self.ss.bybit_liquidations)

        if self.ss.side:
            # trade_dur, pnlClose = self.pnl_and_duration_check(self.ss.tradeStart)
            trade_dur, pnlClose = self.pnl_and_duration_check(self.ss.positionInfo[self.ss.bybit_symbol][6])
        else: trade_dur, pnlClose = True, False

        print(f"Position: {self.ss.positionInfo}")
        print(f"Side: {self.ss.side}")
        print(f"Buy Orders: {b_orders}")
        print(f"Sell Orders: {s_orders}")
        # print(f"fillMe = {self.ss.fillMe}")

        if self.ss.fillMe != None:
            await self.check_orders() #****** Impliment partially filled orders? if a buy order is present when longing then dont add?

        # Long Scenario
        if long and self.ss.side != "Buy" and self.ss.fillMe != "Buy" and len(b_orders) <= 2 and trade_dur:
            print("Long signal printed")
            if self.ss.side:
                print("Closing Short and opening a Long")
                order = ["Buy", bid_price, self.ss.qty*2]
                print("Closed")
                await Order(self.ss).order_limit(order)
            elif not(b_orders):
                print("Opening Long")
                sl_l = bid_price - (self.ss.atr * self.ss.sl_l)
                tp_l = bid_price + (self.ss.atr * self.ss.tp_l)
                order = ["Buy", bid_price, self.ss.qty]
                print("Entered Long")
                await Order(self.ss).order_limit_simple(order, sl=sl_l, tp=tp_l)
            self.ss.fillMe = "Buy"
        # Short Scenario
        elif short and self.ss.side != "Sell" and self.ss.fillMe != "Sell" and len(s_orders) <= 2 and trade_dur:
            if self.ss.side:
                print("Short signal printed, so closing Long")
                order = ["Sell", ask_price, self.ss.qty*2]
                print("Closed")
                await Order(self.ss).order_limit(order)
            elif not(s_orders):
                print("Opening Short")
                sl_s = ask_price + (self.ss.atr * self.ss.sl_s)
                tp_s = ask_price - (self.ss.atr * self.ss.tp_s)
                order = ["Sell", ask_price, self.ss.qty]
                print("Entered Short")
                await Order(self.ss).order_limit_simple(order, sl=sl_s, tp=tp_s)
            self.ss.fillMe = "Sell"
        
        # #Adjust SL after hitting a certain pnl to be following price by a multiple of ATR
        if self.ss.side == "Buy" and len(s_orders) <= 3:
            high = float(self.ss.simple_bybit_klines[-1][2])
            entry = self.ss.positionInfo[self.ss.bybit_symbol][0]
            sl = self.ss.positionInfo[self.ss.bybit_symbol][1]
            # tp = self.ss.positionInfo[self.ss.bybit_symbol][2]
            if closeLong or pnlClose:
                print("Closing Long")
                order = ["Sell", ask_price, self.ss.qty]
                print("Closed Long")
                await Order(self.ss).order_limit(order)
                self.ss.fillMe = "Sell"
            elif sl < entry and high >= (entry+entry*(self.ss.be/100)) and sl != 0:
                print("Moving SL to Entry")
                await Order(self.ss).set_sl_tp(entry+1)

        elif self.ss.side == "Sell" and len(b_orders) <= 3:
            low = float(self.ss.simple_bybit_klines[-1][3])
            entry = self.ss.positionInfo[self.ss.bybit_symbol][0]
            sl = self.ss.positionInfo[self.ss.bybit_symbol][1]
            # tp = self.ss.positionInfo[self.ss.bybit_symbol][2]
            if closeShort or pnlClose:
                print("Closing Short")
                order = ["Buy", bid_price, self.ss.qty]
                print("Closed Short")
                await Order(self.ss).order_limit(order)
                self.ss.fillMe = "Buy"
            elif sl > entry and low <= (entry-entry*(self.ss.be/100)) and sl != 0:
                print("Moving SL to Entry")
                await Order(self.ss).set_sl_tp(entry-1)
    
# NOTE: 
import numpy as np
from typing import Dict, List
from sharedstate import SharedState
from datetime import datetime

class BybitLiquidationsHandler:
    """
    Handler for processing trades data from Bybit and updating the shared state.

    Attributes
    ----------
    ss : SharedState
        An instance of SharedState for storing and managing trades data.

    Methods
    -------
    initialize(data: List[Dict]) -> None:
        Initializes the handler with historical trades data.
    process(recv: List[Dict]) -> None:
        Processes real-time trades data received from Bybit.
    """

    def __init__(self, ss: SharedState) -> None:
        """
        Initializes the BybitTradesHandler with a reference to SharedState.

        Parameters
        ----------
        ss : SharedState
            The shared state instance for managing trades data.
        """
        self.ss = ss

    def initialize(self, data: List[Dict]) -> None:
        """
        Initializes the shared state with historical trades data.

        Parameters
        ----------
        data : List[Dict]
            A list of dictionaries, each representing a liquidation with time, price, size, and side information.
        """
        for row in data:
            ts = float(row["time"])
            price = float(row["price"])
            size = float(row["size"])
            side = 0.0 if row["side"] == "Buy" else 1.0
            new_liq = np.array([[ts, side, price, size]])
            self.ss.bybit_liquidations.append(new_liq)

    def process(self, recv: List[Dict]) -> None:
        """
        Processes and updates the shared state with real-time trades data received from Bybit.

        Parameters
        ----------
        recv : List[Dict]
            A list of dictionaries, each representing a trade with time, price, quantity, and side information.
        """
        for liq in recv["data"]:
            time = float(liq["T"])
            price = float(liq["p"])
            size = float(liq["v"])
            side = 0.0 if liq["S"] == "Buy" else 1.0
            new_liq = np.array([[time, side, price, size]])
            self.ss.bybit_liquidations.append(new_liq)
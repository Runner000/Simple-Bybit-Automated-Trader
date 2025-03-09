
### Configure the trading parameters

Next, we are going to configure the parameters that actually determine which market we are making, and how the trader should behave. 

Sensible defaults are set in `parameters.yaml.example`. Copy it over to your `parameter.yaml` file to get started:
```console
$ cp parameters.yaml.example parameters.yaml
```

The `parameters.yaml` file is gitignored, and can be configured for each environment that you are trading in separately.

Each of the configurable parameters are explained below in more detail

- `account_size` - Your account size in USD.
- `primary_data_feed` - Either Binance or Bybit. While most of the features are based on Bybit's own price, selecting Binance will start additional websocket streams to enable additional pricing features. Only possible if the symbol is trading on Binance USD-M.

- `binance_symbol`: - The derivatives symbol on Binance USD-M, unused if primary_data_feed is set to Bybit.
- `bybit_symbol`: - The derivatives symbol on Bybit Futures.

#### Master offsets 
- `price_offset` - Offset the generates quote prices ± some value. Positive number increases the quote price (and vice versa), however keep in mind that the API will return errors if the offset causes the minimum quote price to be less than 0, or the prices to be outside the exchange defined min/max range.
- `size_offset` - Offset the generates quote sizes ± some value. Positive number increases the quote size (and vice versa), however keep in mind that the API will return errors if the offset causes the minimum quote size to be less than minimum trading size.
- `volatility_offset` - Offset the total quote range ± some value (Positive number increases the distance between the lowest bid and the highest ask, and vice versa)


#### Market Maker Settings
Settings regarding the functionality of the core market making script
- `base_spread` - Lowest spread you're willing to quote at any given volatility. This may be scaled depending on the short-term volatility, up to 10x it's value.
- `min_order_size` - The minimum order size of the closest order to mid-price. 
- `max_order_size` - The maximum order size of the further order from mid-price. 
-  `inventory_extreme` - A value between 0 <-> 1, defining the maximum limit at which the system quotes normally. If inventory delta exceeds this value, it will stop quoting the opposite side and go into a reduce-only mode.

#### Volatility settings
The volatility indicator used to define the trading range is Bollinger Band Width.
- `bollinger_band_length` - Lookback of 1 minute candlestick close data used to calculate band width. 
- `bollinger_band_std` - Multipler of standard deviations generated over the lookback period above.


#### Running the bot

To run the the bot, once your `.env` and `parameters.yaml` file are configured, simply run:
```console
(venv) $ python3 -m main
```


# Strategy Design/Overview

1. Prices from Bybit (and optionally Binance) are streamed using websockets into a common shared class.
2. Features are calculated from the updated market data, and a market maker class generates optimal quotes
  * Multiple features work on comparing different mid-prices to each other (trying to predict where price is likely to go).
  * Both bid/ask skew is then calculated, based on the feature values but corrected for the current inventory (filled position).
  * Prices & sizes are generated based on the skew, with edge cases for extreme inventory cases.
  * Spread is adjusted for volatility (as a multiple of the base spread), widening when short term movements increase.
  * Quotes are generated using all the above, formatted for the local client and returned.
3. Orders are sent via a Order Management System (currently disabled), which transitions between current and new states, and tries to do so in the most ratelimit-efficient way possible.
  

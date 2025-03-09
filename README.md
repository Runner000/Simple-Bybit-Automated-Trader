# Modifications in Branch:
1. Simplified framework that can implement any algorithmic trading strategy
2. Removed most of the Binance references
3. Added a liquidation tracker that utilizes the newly updated bybit allliquidations REST API

# Configure the trading parameters
Sensible defaults are set in `parameters.yaml`. Copy it over to your `parameters.yaml` file to get started:

Each of the configurable parameters are explained below in more detail

- `account_size` - Your account size in USD.
- `bybit_symbol`: - The derivatives symbol on Bybit Futures.

# Running the bot

To run the the bot, once your `.env` and `parameters.yaml` file are configured, simply run:
```console
(venv) $ python3 -m main
```
  

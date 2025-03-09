import asyncio
import winloop
from dotenv import load_dotenv
load_dotenv()

from strategy.core import Strategy
from sharedstate import SharedState

async def main():
    """
    The main entry point of the application. Initializes the shared state and strategy,
    then concurrently refreshes parameters and runs the trading strategy.
    """
    try:
        sharedstate = SharedState()
        await asyncio.gather(
            asyncio.create_task(sharedstate.refresh_parameters()),  
            asyncio.create_task(Strategy(sharedstate).run())  
        )
    except Exception as e:
        print(f"Critical exception occured: {e}")
        # TODO: Add shutdown sequence here
        raise e

if __name__ == "__main__":
    asyncio.set_event_loop_policy(winloop.EventLoopPolicy())
    asyncio.run(main())

# TODO: need to change trade duration (using signal trigger time from df and writing to SS)
# NOTE: Figure out how to manage orders and not repeat the same order. Also amend or cancel old for new bb/ba
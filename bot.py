import asyncio
from telegram_handler import WalletTrackerBot

if __name__ == "__main__":
    wallet_tracker_bot = WalletTrackerBot()
    asyncio.run(wallet_tracker_bot.run())

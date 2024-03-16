import requests
import configparser
from telegram.ext import CommandHandler, CallbackContext
from telegram import Update, Bot, ext
import logging
from storage import save_last_hash, get_last_hash
import asyncio
from telegram.ext import JobQueue
from telegram.ext import Application
from telegram.ext import Application, CommandHandler
from telegram.ext import ApplicationBuilder
import threading
import time
from base_wallet_tracker import BaseScanWalletTracker, escape_markdown


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Set up basic logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
class WalletTrackerBot:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        self.bot_token = self.config.get('Telegram', 'token')
        self.bot = Bot(self.bot_token)
        self.basescan_api_key = self.config.get('BaseScan', 'api_key')
        self.basescan_tracker = BaseScanWalletTracker(self.basescan_api_key)
        self.application = Application.builder().token(self.bot_token).build()
        self.application.add_handler(CommandHandler("start", self.start_command))

    async def start_command(self, update: Update, context: CallbackContext):
        chat_id = update.message.chat_id
        await context.bot.send_message(chat_id=chat_id, text="Hello! I am your BaseScan wallet tracking bot.")

    async def check_new_transactions(self):
        tracked_addresses = ['0x5aFFDEb3C6bC653C70e21bd2bAa4B228Ae63F1dF','0x89E6179A5a69d2Da30f061CA9e09eBDCC0423333','0xa338B75BA3fD53DD25054B70A423493F3d2B0CC6','0x612C45551195f15Bf05D722b9f137C914b077FC7','0xaD63E4d4Be2229B080d20311c1402A2e45Cf7E75','0xCeBad81c2236F4fc0F4592e802932D8677bB201D','0xaB799C5d55675D45f4371E161F893cdeF4E5d3e5','0x81101F861b02F73B34448F011f5F8Dcb89AC50e9','0x68478B80D61E9AAB4f7d63B29671b90C10799A27','0xEAE50a871E446e955abc6CFe3dD0dE8f3373B790']
        chat_id = "-4138009914"  # Replace with actual chat ID or logic to retrieve it

        for address in tracked_addresses:
            last_hash = get_last_hash(address)
            logging.info(f"Checking new transactions for {address}. Last hash: {last_hash}")
            new_transactions = self.basescan_tracker.get_new_erc20_transactions(address, last_hash)
            logging.info(f"Found {len(new_transactions)} new transactions for {address}")

            if new_transactions:
            # Assuming the API returns the latest transaction first
                newest_transaction = new_transactions[0]
                logging.info(f"Newest transaction hash: {newest_transaction['hash']}")

                if last_hash is None or last_hash != newest_transaction['hash']:
                # Call the send_notification method to construct and send the message
                    await self.send_notification(newest_transaction, address)
                    save_last_hash(address, newest_transaction['hash'])
                    logging.info(f"Updated last hash for {address} to {newest_transaction['hash']}")


    async def send_notification(self, transaction, address):
        # Determine if it was a buy or a sell based on 'to' and 'from' addresses
        transaction_type = "Bought" if transaction['to'].lower() == address.lower() else "Sold"
        value_raw = (transaction.get('value','0'))
        token_decimals = int(transaction.get('tokenDecimal', 18))
        token_value = round(int(value_raw) / (10 ** token_decimals), 2)
        escaped_token_value = escape_markdown(str(token_value))

    # Fetch the token name and contract address. Assuming 'tokenName' and 'contractAddress' are keys in the transaction dictionary.
        token_name = transaction.get('tokenName', 'Unknown Token')
        contract_address = transaction.get('contractAddress', 'Unknown Contract Address')
        transaction_url = f"https://basescan.org/tx/{transaction['hash']}"
        profile_url = f"https://basescan.org/address/{address}#tokentxns"
        dexscreener_url = f"https://dexscreener.com/base/{contract_address}"
        escaped_transaction_url = escape_markdown(transaction_url)
        escaped_profile_url = escape_markdown(profile_url)
        escaped_dexscreener_url = escape_markdown(dexscreener_url)
    

    # Escape MarkdownV2 special characters in the token name and address if necessary
        escaped_token_name = token_name.replace('_', '\_').replace('[', '\[').replace(']', '\]').replace('(', '\(').replace(')', '\)').replace('~', '\~').replace('`', '\`').replace('>', '\>').replace('#', '\#').replace('+', '\+').replace('-', '\-').replace('=', '\=').replace('|', '\|').replace('{', '\{').replace('}', '\}').replace('.', '\.').replace('!', '\!')

    # Construct the message with transaction type and token name using Markdown for hyperlinks
        message = (
            "🚨🚨🚨\n"
            f"New transaction for {address}:\n\n"
            f"{transaction_type} {escaped_token_value} [{escaped_token_name}]({escaped_transaction_url})\n\n"
            f"[Transaction Link]({escaped_transaction_url})\n"
            f"[Wallet Profile]({escaped_profile_url})\n"
            f"[DexScreener]({escaped_dexscreener_url})"
    )

        chat_id = "-4138009914"  # Replace with dynamic logic or configuration as needed 
        await self.bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode='MarkdownV2'  # Specify MarkdownV2 as the parse mode
    )

    async def schedule_check_transactions(self, interval=60):
        while True:
            await asyncio.sleep(interval)  # Wait for the specified interval
            await self.check_new_transactions(None) 

    async def run_polling(self):
        """Run the bot's polling in the background."""
        # This is a non-blocking way to start the polling.
        self.application.run_polling(stop_signals=None)


    def start_check_transactions_thread(self, interval=60):
        """Starts a background thread that checks for new transactions."""
        def run_check():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            while True:
                loop.run_until_complete(self.check_new_transactions())
                time.sleep(interval)
        
        thread = threading.Thread(target=run_check)
        thread.start()

    def run(self):
        # Starting the background thread for transaction checks
        self.start_check_transactions_thread()
        
        # Run the asyncio event loop
        loop = asyncio.get_event_loop()
        loop.create_task(self.application.run_polling())
        loop.run_forever()

# Configurations should be in 'config.ini' under [BaseScan] and [Telegram] sections
if __name__ == '__main__':
    wallet_tracker_bot = WalletTrackerBot()
    wallet_tracker_bot.run()  # Call the run method to start the bot

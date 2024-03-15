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

class BaseScanWalletTracker:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.basescan.org/api"

    
    def get_new_erc20_transactions(self, address, last_hash=None):
        logging.info(f"Fetching new ERC20 transactions for address: {address} with last known hash: {last_hash}")
        params = {
            'module': 'account',
            'action': 'tokentx',
            'address': address,
            'page': '1',
            'offset': '1',
            'sort': 'desc',
            'apikey': self.api_key
        }

        response = requests.get(self.base_url, params=params)
        if response.status_code == 200:
            transactions = response.json().get('result', [])
            logging.info(f"Total transactions fetched: {len(transactions)} for address: {address}")

            if last_hash:
                new_transactions = [tx for tx in transactions if tx['hash'] != last_hash]
                logging.info(f"New transactions identified (excluding last known hash): {len(new_transactions)} for address: {address}")
            else:
                new_transactions = transactions
                logging.info(f"No last hash provided, treating all fetched transactions as new: {len(new_transactions)} for address: {address}")

            for tx in new_transactions[:5]:  # Log details of the first few new transactions
                logging.info(f"Transaction Hash: {tx['hash']}, Block Number: {tx.get('blockNumber')}, TimeStamp: {tx.get('timeStamp')}")

            if new_transactions:
                newest_transaction = new_transactions[0]
                if newest_transaction['hash'] == last_hash:
                    logging.info(f"The newest transaction matches the last known hash: {newest_transaction['hash']}")
                else:
                    logging.info(f"Identifying a new hash to update: {newest_transaction['hash']}")

            return new_transactions
        else:
            logging.error(f"Failed to fetch transactions for address: {address}. HTTP Status Code: {response.status_code}")
            return []
        
def escape_markdown(text):
    escape_chars = '_*[]()~`>#+-=|{}.!'
    return ''.join('\\' + char if char in escape_chars else char for char in text)

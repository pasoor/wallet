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

        headers = {
            'Authorization': f"Bearer {self.api_key}",
            'Content-Type': 'application/json'
    }

        response = requests.get(self.base_url, params=params, headers=headers)
        if response.status_code == 200:
            json_data = response.json()
        # Check that the response is a dictionary with a 'result' key
            if isinstance(json_data, dict) and 'result' in json_data:
                transactions = json_data['result']
            # Check if each transaction is a dictionary and has a 'hash' key
                new_transactions = [
                    tx for tx in transactions if isinstance(tx, dict) and 'hash' in tx and (last_hash is None or tx['hash'] != last_hash)
            ]
                logging.info(f"New transactions identified: {len(new_transactions)} for address: {address}")
                return new_transactions
            else:
                logging.error(f"Response JSON structure is not as expected: {json_data}")
                return []
        else:
            logging.error(f"Failed to fetch transactions for address: {address}. HTTP Status Code: {response.status_code}")
            return []

        
def escape_markdown(text):
    escape_chars = '_*[]()~`>#+-=|{}.!'
    return ''.join('\\' + char if char in escape_chars else char for char in text)

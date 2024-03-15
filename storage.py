import json
import threading

lock = threading.Lock()

def save_last_hash(address, last_hash):
    with lock:
        try:
            with open('last_hashes.json', 'r+') as file:
                hashes = json.load(file)
        except FileNotFoundError:
            hashes = {}
        hashes[address] = last_hash
        with open('last_hashes.json', 'w') as file:
            json.dump(hashes, file)

def get_last_hash(address):
    with lock:
        try:
            with open('last_hashes.json', 'r') as file:
                hashes = json.load(file)
                return hashes.get(address)
        except FileNotFoundError:
            return None

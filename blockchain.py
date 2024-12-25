import hashlib
import json
from time import time
from urllib.parse import urlparse
import requests

class blockchain:
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()
        self.borrowers = set()
        self.new_block(previous_hash='1', proof=100)  # Create the genesis block

    def new_transaction(self, borrower, lender, amount, interest_rate, duration, total_interest):
        transaction = {
            'Заемщик': borrower,
            'Кредитор': lender,
            'Сумма': amount,
            'Ставка': interest_rate,
            'Продолжительность': duration,
            'Всего процентов': total_interest,  # Сохраняем рассчитанные проценты
            'status': 'В процессе выплаты'  # Track the status of the loan
        }
        self.current_transactions.append(transaction)
        return self.last_block['index'] + 1



    def repay_loan(self, borrower, amount):
        """Repay a loan by updating the transaction status."""
        for transaction in self.current_transactions:
            if transaction['Заемщик'] == borrower and transaction['status'] == 'В процессе выплаты':
                transaction['Сумма'] -= amount
                if transaction['Сумма'] <= 0:
                    transaction['status'] = 'Погашен'
                return transaction
        return None  # No matching loan found

    def new_block(self, proof, previous_hash=None):
        """Create a new block in the blockchain."""
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1])
        }

        self.current_transactions = []
        self.chain.append(block)
        return block

    @staticmethod
    def hash(block):
        """Create a SHA-256 hash of a block."""
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        """Return the last block in the chain."""
        return self.chain[-1]

    def proof_of_work(self, last_proof):
        """Simple proof of work algorithm."""
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        """Validates the proof of work."""
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == '0000'

    def valid_chain(self, chain):
        """Check if a blockchain is valid."""
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]

            # Validate previous_hash
            if block['previous_hash'] != self.hash(last_block):
                return False

            # Validate proof of work
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        """Resolve conflicts by replacing the chain with the longest one."""
        neighbours = self.nodes
        new_chain = None
        max_length = len(self.chain)

        for node in neighbours:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        if new_chain:
            self.chain = new_chain
            return True
        return False

    def register_node(self, address):
        """Add a new node to the list of nodes."""
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)


from uuid import uuid4
from flask import Flask, jsonify, request
from blockchain import blockchain

app = Flask(__name__)

node_identifier = str(uuid4()).replace('-', '')  # Unique identifier for this node
blockchain = blockchain()

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    required = ['Заемщик', 'Кредитор', 'Сумма', 'Ставка', 'Продолжительность']
    if not all(k in values for k in required):
        return 'Missing value', 400

    try:
        # Извлечение данных
        amount = float(values['Сумма'])  # Основной долг
        interest_rate = float(values['Ставка'])  # Процентная ставка (годовая)
        duration = float(values['Продолжительность'])  # Срок займа (в годах)

        # Расчет процентов
        total_interest = amount * (interest_rate / 100) * duration

        # Create a new loan transaction
        index = blockchain.new_transaction(
            borrower=values['Заемщик'],
            lender=values['Кредитор'],
            amount=values['Сумма'],
            interest_rate=values['Ставка'],
            duration=values['Продолжительность'],
            total_interest=total_interest  # Добавляем проценты в транзакцию
        )

        response = {
            'message': f'Транзакция проведена ',
            'Всего процентов': total_interest  # Возвращаем рассчитанные проценты
        }
        return jsonify(response), 201

    except ValueError:
        return 'Invalid input. Please ensure that amount, interest_rate, and duration are numbers.', 400

@app.route('/transactions/repay', methods=['POST'])
def repay_loan():
    values = request.get_json()

    required = ['Заемщик', 'Сумма']
    if not all(k in values for k in required):
        return 'Missing value', 400

    transaction = blockchain.repay_loan(borrower=values['Заемщик'], amount=values['Сумма'])

    if transaction:
        response = {
            'message': 'Процесс погашения кредита',
            'updated_transaction': transaction
        }
    else:
        response = {
            'message': 'No matching loan found or repayment failed'
        }

    return jsonify(response), 200

@app.route('/calculate_interest', methods=['POST'])
def calculate_interest():
    values = request.get_json()

    required = ['Сумма', 'Ставка', 'Продолжительность']
    if not all(k in values for k in required):
        return 'Missing value', 400

    try:
        # Извлечение данных
        amount = float(values['Сумма'])  # Основной долг
        interest_rate = float(values['Ставка'])  # Процентная ставка (годовая)
        duration = float(values['Продолжительность'])  # Срок займа (в годах)

        # Расчет процентов
        interest = amount * (interest_rate / 100) * duration

        response = {
            'Сумма': amount,
            'Ставка': interest_rate,
            'Длительность': duration,
            'Проценты': interest
        }
        return jsonify(response), 200

    except ValueError:
        return 'Invalid input. Please ensure that amount, interest_rate, and duration are numbers.', 400

@app.route('/mine', methods=['GET'])
def mine():
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # Reward for mining a new block
    blockchain.new_transaction(sender="0", recipient=node_identifier, amount=1)

    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': 'New Block Forged',
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash']
    }

    return jsonify(response), 200

@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }

    return jsonify(response), 200

@app.route('/borrowers', methods=['GET'])
def get_borrowers():
    borrowers = blockchain.current_transactions
    response = {
        'Заемщики': borrowers,
        'Всего заемщиков': len(borrowers)
    }
    return jsonify(response), 200

@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201

@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }

    return jsonify(response), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
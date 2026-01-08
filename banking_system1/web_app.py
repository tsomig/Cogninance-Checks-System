#!/usr/bin/env python3
"""
Flask Web Interface - Updated for Forwarding Visualization
"""
from flask import Flask, render_template, request, jsonify
import sys, os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.schema import DatabaseManager, EntityManager, TransactionLogger
from managers.intent_parser import IntentParser
from managers.check_manager import CheckManager
from managers.transaction_manager import TransactionManager
from managers.conversation_agent import ConversationAgent
import config

app = Flask(__name__)
app.config['SECRET_KEY'] = 'banking-demo-key'

db = DatabaseManager(config.DATABASE_PATH)
db.connect()
db.initialize_schema()

entity_mgr = EntityManager(db)
logger = TransactionLogger(db)
parser = IntentParser()
check_mgr = CheckManager(db, entity_mgr)
tx_mgr = TransactionManager(parser, check_mgr, entity_mgr, logger)
agent = ConversationAgent(tx_mgr)

USER_ID = 1

@app.route('/')
def index(): return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        msg = request.json.get('message', '').strip()
        response = agent.chat(USER_ID, msg, "You")
        return jsonify({'response': response})
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/api/status', methods=['GET'])
def status():
    try:
        balance = check_mgr.get_user_balance(USER_ID)
        checks = check_mgr.get_user_checks(USER_ID, 'all')
        
        pending_incoming = []
        issued = []
        accepted = []
        denied = []
        forwarded = [] 

        def fmt(c, role):
            # Helper to format date nicely
            m_date = c['maturity_date']
            if isinstance(m_date, str):
                try: m_date = datetime.fromisoformat(m_date).strftime('%Y-%m-%d')
                except: pass
            
            # Formatter for Forwarded Checks
            if role == 'forwarded':
                status_icon = "⏳" if c['status'] == 'PENDING' else "✓"
                return {
                    'id': c['id'],
                    'amount': c['amount'],
                    'origin': c['issuer_name'],  # The original creator
                    'destination': f"{c['payee_name']} ({status_icon} {c['status']})", # Who has it now
                    'maturity_date': m_date
                }
            
            # Formatter for Standard Checks
            counterparty = c['issuer_name'] if role == 'incoming' else c['payee_name']
            return {
                'id': c['id'],
                'amount': c['amount'],
                'counterparty': counterparty,
                'status': c['status'],
                'maturity_date': m_date
            }

        for c in checks:
            # 1. Incoming Pending (Checks waiting for me to accept)
            if c['payee_id'] == USER_ID and c['status'] == 'PENDING':
                pending_incoming.append(fmt(c, 'incoming'))
            
            # 2. Accepted (My Wallet - checks I own)
            elif c['payee_id'] == USER_ID and c['status'] == 'ACCEPTED':
                accepted.append(fmt(c, 'incoming'))
            
            # 3. Denied History
            elif c['payee_id'] == USER_ID and c['status'] == 'DENIED':
                denied.append(fmt(c, 'incoming'))

            # 4. Forwarded (Checks I sent to someone else, but I didn't originally create)
            # Logic: I am the sender, but NOT the original issuer.
            elif c['sender_id'] == USER_ID and c['issuer_id'] != USER_ID:
                forwarded.append(fmt(c, 'forwarded'))
            
            # 5. Issued (Checks I created)
            elif c['issuer_id'] == USER_ID:
                issued.append(fmt(c, 'outgoing'))

        return jsonify({
            'balance': balance,
            'checks': {
                'pending_incoming': pending_incoming,
                'issued': issued,
                'accepted': accepted,
                'denied': denied,
                'forwarded': forwarded,
                'total': len(checks)
            },
            'transactions': [],
            'counterparties': []
        })
    except Exception as e:
        print(f"Error in status: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
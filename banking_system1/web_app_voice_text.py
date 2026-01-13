#!/usr/bin/env python3
"""
Flask Web Interface - Updated with Voice Avatar Support
========================================================

Includes:
- Original text chat interface at /
- NEW: Voice avatar interface at /voice
- All existing API endpoints preserved
"""
from flask import Flask, render_template, request, jsonify
import sys
import os
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

# Initialize database and managers
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

# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def index():
    """Main text chat interface"""
    return render_template('index.html')


@app.route('/voice')
def voice_interface():
    """
    Voice + Text hybrid interface with animated avatar
    
    Provides both speech-to-text and text input options with
    an animated avatar for a more engaging user experience.
    
    Uses the same /api/chat endpoint as the text interface.
    """
    return render_template('voice_text_hybrid.html')


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Process chat message (works for both text and voice interfaces)
    
    Request: { "message": "user's message" }
    Response: { "response": "assistant's response" }
    
    For voice interface, this endpoint is called after speech-to-text
    converts the user's voice to text.
    """
    try:
        msg = request.json.get('message', '').strip()
        
        if not msg:
            return jsonify({'error': 'Empty message'}), 400
        
        # Process through conversation agent (Claude API)
        response = agent.chat(USER_ID, msg, "You")
        
        # Log for behavioral analysis (optional metadata for voice)
        input_modality = request.json.get('modality', 'text')
        
        return jsonify({
            'response': response,
            'modality': input_modality
        })
        
    except Exception as e:
        print(f"Chat error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/status', methods=['GET'])
def status():
    """
    Get current system status (checks, balance, etc.)
    Used by both text and voice interfaces for dashboard updates.
    """
    try:
        balance = check_mgr.get_user_balance(USER_ID)
        checks = check_mgr.get_user_checks(USER_ID, 'all')
        
        pending_incoming = []
        issued = []
        accepted = []
        denied = []
        forwarded = []

        def fmt(c, role):
            """Format check for display"""
            m_date = c['maturity_date']
            if isinstance(m_date, str):
                try:
                    m_date = datetime.fromisoformat(m_date).strftime('%Y-%m-%d')
                except:
                    pass
            
            # Formatter for Forwarded Checks
            if role == 'forwarded':
                status_icon = "⏳" if c['status'] == 'PENDING' else "✓"
                return {
                    'id': c['id'],
                    'amount': c['amount'],
                    'origin': c['issuer_name'],
                    'destination': f"{c['payee_name']} ({status_icon} {c['status']})",
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
            # 1. Incoming Pending
            if c['payee_id'] == USER_ID and c['status'] == 'PENDING':
                pending_incoming.append(fmt(c, 'incoming'))
            
            # 2. Accepted (My Wallet)
            elif c['payee_id'] == USER_ID and c['status'] == 'ACCEPTED':
                accepted.append(fmt(c, 'incoming'))
            
            # 3. Denied History
            elif c['payee_id'] == USER_ID and c['status'] == 'DENIED':
                denied.append(fmt(c, 'incoming'))

            # 4. Forwarded
            elif c['sender_id'] == USER_ID and c['issuer_id'] != USER_ID:
                forwarded.append(fmt(c, 'forwarded'))
            
            # 5. Issued
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
        print(f"Status error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/voice/config', methods=['GET'])
def voice_config():
    """
    NEW: Return voice configuration settings
    
    Can be extended to return user preferences for:
    - Preferred TTS voice
    - Speech rate
    - Language settings
    """
    return jsonify({
        'language': 'en-US',
        'speechRate': 1.0,
        'pitch': 1.0,
        'continuous': False
    })


# ============================================================================
# BEHAVIORAL RESEARCH EXTENSIONS (Optional)
# ============================================================================

@app.route('/api/voice/log', methods=['POST'])
def log_voice_metrics():
    """
    NEW: Log voice interaction metrics for behavioral analysis
    
    This endpoint can be called by the voice interface to log
    additional behavioral signals not captured in text:
    
    - Speech duration
    - Hesitation count (pauses)
    - Speech rate (words per minute)
    - Confidence from STT
    
    Request: {
        "user_id": 1,
        "transcript": "issue check to alice for 500",
        "metrics": {
            "duration_ms": 2340,
            "hesitation_count": 1,
            "speech_rate_wpm": 145,
            "stt_confidence": 0.92
        }
    }
    """
    try:
        data = request.json
        
        # Log to transaction history with voice metadata
        if data.get('metrics'):
            logger.log_transaction(
                user_id=data.get('user_id', USER_ID),
                operation_type='VOICE_INTERACTION',
                status='LOGGED',
                conversation_context=data.get('transcript', ''),
                metadata={
                    'input_modality': 'voice',
                    'voice_metrics': data.get('metrics', {})
                }
            )
        
        return jsonify({'status': 'logged'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("🏦 CONVERSATIONAL BANKING SYSTEM")
    print("=" * 60)
    print("\n📍 Available interfaces:")
    print("   • Text Chat:  http://localhost:5000/")
    print("   • Voice Chat: http://localhost:5000/voice")
    print("\n🎤 Voice interface uses browser's Speech Recognition")
    print("   (Works best in Chrome or Edge)")
    print("=" * 60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
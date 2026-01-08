"""
Transaction Manager - System Orchestrator
=========================================
Coordinates Intent Parser, Check Manager, and Logger.
Contains the high-level business logic routing.
"""

from typing import Dict, Tuple, Optional
from managers.intent_parser import IntentParser, Intent
from managers.check_manager import CheckManager
from database.schema import EntityManager, TransactionLogger
import config

class TransactionManager:
    def __init__(
        self,
        parser: IntentParser,
        check_manager: CheckManager,
        entity_manager: EntityManager,
        logger: TransactionLogger
    ):
        self.parser = parser
        self.check_mgr = check_manager
        self.entity_mgr = entity_manager
        self.logger = logger
    
    def process_command(self, user_id: int, user_input: str) -> Dict:
        """Main entry point for command processing."""
        # 1. Parse Intent
        intent = self.parser.parse(user_input)
        
        # 2. Check Ambiguity
        if intent.needs_clarification():
            return {
                'success': False, 
                'message': "I didn't quite catch that. Could you clarify the check number or the person?", 
                'intent': intent, 
                'needs_clarification': True
            }
        
        # 3. Route Command
        op = intent.operation
        
        if op == 'ISSUE_CHECK':
            return self._execute_issue_check(user_id, intent)
        elif op == 'ACCEPT_CHECK':
            return self._execute_accept_check(user_id, intent)
        elif op == 'DENY_CHECK':
            return self._execute_deny_check(user_id, intent)
        elif op == 'FORWARD_CHECK':
            return self._execute_forward_check(user_id, intent)
        elif op == 'REVOKE_OP':
            return self._execute_revoke_operation(user_id, intent)
        elif op.startswith('QUERY'):
            return self._handle_query(user_id, intent)
        
        return {'success': False, 'message': f"Operation {op} not implemented.", 'intent': intent}

    # --- EXECUTION HANDLERS ---

    def _execute_issue_check(self, user_id: int, intent: Intent) -> Dict:
        p = intent.parameters
        if 'counterparty' not in p or 'amount' not in p:
            return {'success': False, 'message': "I need a name and amount to issue a check.", 'intent': intent}
        
        success, msg, cid = self.check_mgr.issue_check(
            user_id, p['counterparty'], p['amount'], custom_date=p.get('custom_date')
        )
        
        self.logger.log_transaction(
            user_id, 'ISSUE_CHECK', 'SUCCESS' if success else 'FAILED', 
            check_id=cid, amount=p['amount'], conversation_context=intent.raw_text
        )
        return {'success': success, 'message': msg, 'intent': intent}

    def _execute_accept_check(self, user_id: int, intent: Intent) -> Dict:
        p = intent.parameters
        
        # A. Accept All
        if p.get('accept_all'):
            # Get pending checks where I am the payee
            pending = [c for c in self.check_mgr.get_user_checks(user_id) if c['payee_id'] == user_id and c['status'] == 'PENDING']
            if not pending: return {'success': True, 'message': "No pending checks to accept.", 'intent': intent}
            
            for c in pending:
                self.check_mgr.accept_check(user_id, check_id=c['id'])
                self.logger.log_transaction(user_id, 'ACCEPT_CHECK', 'SUCCESS', check_id=c['id'])
            return {'success': True, 'message': f"Accepted {len(pending)} checks.", 'intent': intent}
        
        # B. Specific Checks (Batch or Single)
        ids = p.get('check_ids', [p.get('check_id')]) if 'check_id' in p or 'check_ids' in p else []
        ids = [x for x in ids if x] # Filter None
        
        if not ids: return {'success': False, 'message': "Which check?", 'intent': intent}
        
        results = []
        for cid in ids:
            s, m, _ = self.check_mgr.accept_check(user_id, check_id=cid)
            results.append(f"#{cid}: {m}")
            if s: self.logger.log_transaction(user_id, 'ACCEPT_CHECK', 'SUCCESS', check_id=cid)
            
        return {'success': True, 'message': " | ".join(results), 'intent': intent}

    def _execute_deny_check(self, user_id: int, intent: Intent) -> Dict:
        p = intent.parameters
        ids = p.get('check_ids', [p.get('check_id')]) if 'check_id' in p or 'check_ids' in p else []
        ids = [x for x in ids if x]
        
        if not ids: return {'success': False, 'message': "Which check?", 'intent': intent}
        
        results = []
        for cid in ids:
            s, m, _ = self.check_mgr.deny_check(user_id, check_id=cid)
            results.append(f"#{cid}: {m}")
            if s: self.logger.log_transaction(user_id, 'DENY_CHECK', 'SUCCESS', check_id=cid)
            
        return {'success': True, 'message': " | ".join(results), 'intent': intent}

    def _execute_forward_check(self, user_id: int, intent: Intent) -> Dict:
        p = intent.parameters
        if 'check_id' not in p: return {'success': False, 'message': "Need check number.", 'intent': intent}
        if 'to_counterparty' not in p: return {'success': False, 'message': "Need recipient name.", 'intent': intent}
        
        s, m, nid = self.check_mgr.forward_check(user_id, p['check_id'], p['to_counterparty'])
        
        self.logger.log_transaction(
            user_id, 'FORWARD_CHECK', 'SUCCESS' if s else 'FAILED', 
            check_id=nid, conversation_context=intent.raw_text
        )
        return {'success': s, 'message': m, 'intent': intent}

    def _execute_revoke_operation(self, user_id: int, intent: Intent) -> Dict:
        """Smart Router for Revoke/Cancel/Undo"""
        p = intent.parameters
        ids = p.get('check_ids', [p.get('check_id')]) if 'check_id' in p or 'check_ids' in p else []
        ids = [x for x in ids if x]
        
        if not ids: return {'success': False, 'message': "Which check number?", 'intent': intent}
        
        results = []
        success_count = 0
        
        for cid in ids:
            # 1. Fetch check to understand context
            cursor = self.check_mgr.db.conn.cursor()
            cursor.execute("SELECT * FROM checks WHERE id=?", (cid,))
            check = cursor.fetchone()
            
            if not check:
                results.append(f"#{cid}: Not found")
                continue
            
            success = False
            msg = ""
            
            # 2. Logic Branching
            
            # Branch A: I Forwarded it (I am Sender, Status is Pending)
            if check['sender_id'] == user_id and check['status'] == 'PENDING':
                success, msg = self.check_mgr.cancel_forward(user_id, cid)
                
            # Branch B: I Issued it (I am Issuer, Status is Pending, No Sender)
            elif check['issuer_id'] == user_id and check['status'] == 'PENDING':
                success, msg = self.check_mgr.cancel_issuance(user_id, cid)
                
            # Branch C: I Received it (I am Payee, Status is Accepted/Denied)
            elif check['payee_id'] == user_id:
                if check['status'] in ['ACCEPTED', 'DENIED']:
                    success, msg = self.check_mgr.revoke_incoming_decision(user_id, cid)
                else:
                    success, msg = False, f"Check is {check['status']}, nothing to revoke."
            
            else:
                success, msg = False, "You cannot revoke this check (wrong status or ownership)."
            
            results.append(f"#{cid}: {msg}")
            if success:
                success_count += 1
                self.logger.log_transaction(user_id, 'REVOKE_OP', 'SUCCESS', check_id=cid)
        
        return {'success': success_count > 0, 'message': " | ".join(results), 'intent': intent}

    def _handle_query(self, user_id: int, intent: Intent) -> Dict:
        op = intent.operation
        
        if op == 'QUERY_BALANCE':
            bal = self.check_mgr.get_user_balance(user_id)
            return {'success': True, 'message': f"Balance: ${bal:.2f}", 'intent': intent}
            
        elif op == 'QUERY_CHECKS':
            checks = self.check_mgr.get_user_checks(user_id)
            
            # Organize by basket for the text response
            baskets = {'INCOMING': [], 'WALLET': [], 'ISSUED': [], 'FORWARDED': [], 'DENIED_HISTORY': []}
            for c in checks:
                cat = c.get('category', 'OTHER')
                if cat in baskets:
                    baskets[cat].append(c)
            
            # Build a nice text summary
            msg_lines = []
            if baskets['INCOMING']:
                msg_lines.append(f"📬 **Incoming ({len(baskets['INCOMING'])}):**")
                for c in baskets['INCOMING']: msg_lines.append(f"  - #{c['id']} from {c['issuer_name']}: ${c['amount']}")
            
            if baskets['WALLET']:
                msg_lines.append(f"\n💰 **Wallet ({len(baskets['WALLET'])}):**")
                for c in baskets['WALLET']: msg_lines.append(f"  - #{c['id']}: ${c['amount']}")

            if baskets['FORWARDED']:
                msg_lines.append(f"\n🚀 **Forwarded ({len(baskets['FORWARDED'])}):**")
                for c in baskets['FORWARDED']: 
                    status_icon = "⏳" if c['status']=='PENDING' else "✓"
                    msg_lines.append(f"  - #{c['id']} to {c['payee_name']} ({status_icon} {c['status']})")

            if baskets['ISSUED']:
                msg_lines.append(f"\n✍️ **Issued ({len(baskets['ISSUED'])}):**")
                for c in baskets['ISSUED']: msg_lines.append(f"  - #{c['id']} to {c['payee_name']}: ${c['amount']}")

            if not msg_lines:
                final_msg = "You have no checks."
            else:
                final_msg = "\n".join(msg_lines)

            return {'success': True, 'message': final_msg, 'data': {'checks': checks}, 'intent': intent}
            
        return {'success': True, 'message': "Query Done", 'intent': intent}